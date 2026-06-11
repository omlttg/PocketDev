import os
import json
import logging
import google.generativeai as genai
from app.config import settings
from app.tools import GITLAB_TOOLS

logger = logging.getLogger(__name__)

# Configure Gemini API Key
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not configured in the env variables!")

# System Instruction defining the persona and behavior of the Agent
SYSTEM_INSTRUCTION = """
You are PocketDev, a highly intelligent and agile "Pocket CTO / Lead Developer Agent".
Your mission is to help managers and developers manage code, coordinate issues, open/merge MRs, and track CI/CD pipelines on GitLab directly through chat (Telegram).

Principles of Operation:
1. Move Beyond Chat: Do not just answer questions. You have direct read/write access to the GitLab project via the provided tools. Use them proactively to accomplish tasks.
2. Multi-Step Mission & Planning: When the user issues a complex software request (e.g. implementing a new feature, restructuring files, or fixing a multi-part bug):
   a. First, analyze the current code structure using the `analyze_codebase_architecture` tool.
   b. Second, formulate a plan and actively decompose the main requirement into 2-4 concrete technical sub-tasks using the `decompose_task_into_subissues` tool to create linked issues on GitLab.
   c. Explain your step-by-step plan clearly to the user before or while executing these planning tools.
3. Keep your responses short, concise, and structured (use bullet points and bold formatting where appropriate), optimized for reading on mobile phone screens.
4. Respond in the same language the user communicates with you (e.g., if they ask in Vietnamese, reply in Vietnamese; if they ask in English, reply in English). Default to English if the language is unclear.
5. When an action succeeds (e.g., issue or MR created), always provide the ID and a clickable GitLab URL link.
6. If the user input is missing required parameters for a tool, ask for clarification instead of guessing or failing.
"""

# Map function names to actual functions for dynamic invocation
TOOL_MAP = {func.__name__: func for func in GITLAB_TOOLS}

class AgentManager:
    def __init__(self):
        # In-memory cache for user chat sessions (chat_id -> ChatSession)
        self.sessions = {}
        # Directory for local chat history JSON persistence
        self.history_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.history_dir, exist_ok=True)

    def _get_model(self) -> genai.GenerativeModel:
        """Initialize and configure the Gemini model."""
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # High-speed model suitable for quick webhook responses
            tools=GITLAB_TOOLS,
            system_instruction=SYSTEM_INSTRUCTION
        )

    def _get_history_filepath(self, chat_id: int) -> str:
        """Returns the file path for the history of a specific chat_id."""
        return os.path.join(self.history_dir, f"chat_history_{chat_id}.json")

    def _load_history_from_file(self, chat_id: int) -> list:
        """Load and reconstruct simplified text-only history from a JSON file using raw dict structures."""
        filepath = self._get_history_filepath(chat_id)
        if not os.path.exists(filepath):
            return []
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_history = json.load(f)
                
            gemini_history = []
            for msg in raw_history:
                # Build list of message dicts accepted by Gemini SDK
                gemini_history.append({
                    "role": msg["role"],
                    "parts": [{"text": msg["text"]}]
                })
            logger.info(f"Restored {len(gemini_history)} chat history messages from file for chat_id: {chat_id}")
            return gemini_history
        except Exception as e:
            logger.error(f"Error loading chat history file for chat_id {chat_id}: {e}")
            return []

    def _save_history_to_file(self, chat_id: int, chat_session: genai.ChatSession):
        """Save simplified text-only chat history into a local JSON file."""
        filepath = self._get_history_filepath(chat_id)
        try:
            simplified_history = []
            for content in chat_session.history:
                text_parts = []
                # Safely extract text parts from model's Content objects
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        text_parts.append(part.text)
                    elif isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                        
                if text_parts:
                    simplified_history.append({
                        "role": content.role,
                        "text": " ".join(text_parts)
                    })
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(simplified_history, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved chat history to JSON file for chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Error saving chat history file for chat_id {chat_id}: {e}")

    def get_or_create_chat(self, chat_id: int) -> genai.ChatSession:
        """Retrieve existing chat session or load from history file / start a new one."""
        if chat_id not in self.sessions:
            logger.info(f"Initializing ChatSession for chat_id: {chat_id}")
            model = self._get_model()
            history = self._load_history_from_file(chat_id)
            self.sessions[chat_id] = model.start_chat(history=history)
        return self.sessions[chat_id]

    async def process_message(self, chat_id: int, user_message: str) -> str:
        """
        Processes a user message, resolves any Tool Calling loops,
        persists the updated history, and returns the final text response.
        """
        chat = self.get_or_create_chat(chat_id)
        
        try:
            logger.info(f"[User {chat_id}]: {user_message}")
            response = chat.send_message(user_message)
            
            # Loop for function/tool calling (max 5 iterations to prevent infinite loops)
            loop_count = 0
            max_loops = 5
            
            while response.function_calls and loop_count < max_loops:
                loop_count += 1
                logger.info(f"Gemini requested calling {len(response.function_calls)} tools (Iteration {loop_count})")
                
                parts_responses = []
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args
                    
                    logger.info(f"Executing tool '{name}' with args: {args}")
                    
                    tool_func = TOOL_MAP.get(name)
                    if tool_func:
                        try:
                            # Convert args from protobuf Struct to a regular python dict
                            dict_args = {k: v for k, v in args.items()}
                            result = tool_func(**dict_args)
                        except Exception as tool_err:
                            logger.error(f"Error executing tool {name}: {tool_err}")
                            result = f"Error executing tool: {str(tool_err)}"
                    else:
                        result = f"Error: Tool '{name}' not found on server."
                        
                    logger.info(f"Result for tool '{name}': {result}")
                    
                    # Formulate function response part using raw dict format
                    part_response = {
                        "function_response": {
                            "name": name,
                            "response": {"result": result}
                        }
                    }
                    parts_responses.append(part_response)
                
                # Send tool execution results back to the Gemini model using raw dict message format
                response = chat.send_message({
                    "role": "user",
                    "parts": parts_responses
                })
                
            if loop_count >= max_loops:
                logger.warning(f"Exceeded max tool calling loops ({max_loops}) for chat_id: {chat_id}")
                return "I've triggered the required actions, but the process is taking too many steps. Please verify details directly on GitLab."
                
            # Save the updated conversation history
            self._save_history_to_file(chat_id, chat)
            
            return response.text

        except Exception as e:
            logger.error(f"Error processing agent message: {e}", exc_info=True)
            return f"Apologies, an error occurred while processing your request: {str(e)}"

# Global AgentManager instance
agent_manager = AgentManager()
