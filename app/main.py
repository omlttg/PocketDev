import inspect
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from app.config import settings
from app.agent import agent_manager
from app.telegram_bot import send_telegram_message

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PocketDev Backend",
    description="Webhook Backend for PocketDev Core Agent connecting Telegram and GitLab / GCP Agent Builder",
    version="1.0.0"
)

# Pydantic schemas for IDE Agent communication
class ProposalCreate(BaseModel):
    proposal_id: str
    task: str
    command: Optional[str] = ""
    changed_files: Optional[List[str]] = []
    description: Optional[str] = ""
    merge_request_iid: Optional[int] = None

class ExecutionLog(BaseModel):
    proposal_id: str
    log: str

@app.post("/api/agent/proposals")
async def create_agent_proposal(proposal: ProposalCreate):
    """
    Endpoint for the IDE Agent to register a new code execution proposal.
    Notifies the CTO immediately via Telegram.
    """
    from app.tools.team_tools import load_proposals, save_proposals
    
    proposals = load_proposals()
    proposal_id = proposal.proposal_id
    
    # Save the proposal with status PENDING
    proposals[proposal_id] = {
        "id": proposal_id,
        "task": proposal.task,
        "command": proposal.command,
        "changed_files": proposal.changed_files,
        "description": proposal.description,
        "status": "PENDING",
        "merge_request_iid": proposal.merge_request_iid
    }
    save_proposals(proposals)
    
    # Notify CTO via Telegram push
    chat_ids = []
    if settings.ALLOWED_TELEGRAM_USER_IDS:
        chat_ids = [int(uid.strip()) for uid in settings.ALLOWED_TELEGRAM_USER_IDS.split(",") if uid.strip()]
        
    notify_msg = (
        f"🤖 <b>New IDE Agent Proposal (ID: {proposal_id})</b>\n\n"
        f"📋 <b>Task:</b> {proposal.task}\n"
        f"📝 <b>Description:</b> {proposal.description or 'No description provided.'}\n"
    )
    if proposal.command:
        notify_msg += f"💻 <b>Command:</b> <code>{proposal.command}</code>\n"
    if proposal.changed_files:
        notify_msg += f"📂 <b>Files:</b> <code>{', '.join(proposal.changed_files)}</code>\n"
        
    notify_msg += f"\n📥 <i>Reply with 'Approve {proposal_id}' or 'Reject {proposal_id} [reason]' to decide.</i>"
    
    for cid in chat_ids:
        try:
            await send_telegram_message(cid, notify_msg)
        except Exception as e:
            logger.error(f"Failed to push proposal notification to {cid}: {e}")
            
    return {"status": "pending", "proposal_id": proposal_id}

@app.get("/api/agent/proposals/{proposal_id}")
async def get_agent_proposal(proposal_id: str):
    """
    Allows the IDE Agent to query the current status of its proposal.
    """
    from app.tools.team_tools import load_proposals
    proposals = load_proposals()
    proposal = proposals.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {
        "proposal_id": proposal_id,
        "status": proposal.get("status", "PENDING"),
        "feedback": proposal.get("feedback", "")
    }

@app.post("/api/agent/logs")
async def create_agent_log(exec_log: ExecutionLog):
    """
    Receives real-time terminal output logs from the IDE Agent and notifies the CTO.
    """
    chat_ids = []
    if settings.ALLOWED_TELEGRAM_USER_IDS:
        chat_ids = [int(uid.strip()) for uid in settings.ALLOWED_TELEGRAM_USER_IDS.split(",") if uid.strip()]
        
    log_msg = (
        f"ℹ️ <b>IDE Agent Execution Log (ID: {exec_log.proposal_id}):</b>\n\n"
        f"<code>{exec_log.log}</code>"
    )
    
    for cid in chat_ids:
        try:
            truncated_msg = log_msg
            if len(log_msg) > 4000:
                truncated_msg = log_msg[:4000] + "\n... [Log truncated] </code>"
            await send_telegram_message(cid, truncated_msg)
        except Exception as e:
            logger.error(f"Failed to push execution log to {cid}: {e}")
            
    return {"status": "logged"}

# High-fidelity Glassmorphic Landing Page HTML
LANDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PocketDev — The Mobile CTO Agent</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(23, 28, 41, 0.45);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary-gradient: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
            --accent-glow: radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.15) 0%, transparent 60%);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --success-color: #10b981;
            --error-color: #ef4444;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow-x: hidden;
            position: relative;
            padding: 2rem 1rem;
        }}

        /* Soft ambient glowing background */
        body::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--accent-glow);
            z-index: 0;
            pointer-events: none;
        }}

        .container {{
            max-width: 800px;
            width: 100%;
            background: var(--card-bg);
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 2.5rem;
            z-index: 1;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            text-align: center;
            transition: transform 0.3s ease;
        }}

        .logo-container {{
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 80px;
            height: 80px;
            background: var(--primary-gradient);
            border-radius: 20px;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px rgba(124, 58, 237, 0.4);
            animation: pulse 3s infinite alternate;
        }}

        .logo-container svg {{
            width: 44px;
            height: 44px;
            fill: #ffffff;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #ffffff, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .tagline {{
            color: var(--text-muted);
            font-size: 1.1rem;
            margin-bottom: 2rem;
            font-weight: 300;
        }}

        /* Interactive Process flow */
        .flow-diagram {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.2rem;
            margin-bottom: 2.5rem;
            font-size: 0.9rem;
        }}

        .flow-step {{
            flex: 1;
            font-weight: 600;
            color: #a78bfa;
        }}

        .flow-arrow {{
            color: var(--border-color);
            font-size: 1.2rem;
            margin: 0 10px;
            user-select: none;
        }}

        /* Table design */
        .status-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2.5rem;
            text-align: left;
        }}

        .status-table th, .status-table td {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .status-table th {{
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .status-table td {{
            font-size: 0.95rem;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }}

        .status-badge.success {{
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--success-color);
        }}

        .status-badge.error {{
            background-color: rgba(239, 68, 68, 0.15);
            color: var(--error-color);
        }}

        .webhook-box {{
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 2rem;
            font-family: monospace;
            font-size: 0.85rem;
            word-break: break-all;
            color: #38bdf8;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.05); }}
        }}

        @media (max-width: 600px) {{
            .container {{
                padding: 1.5rem;
            }}
            h1 {{
                font-size: 1.8rem;
            }}
            .flow-diagram {{
                flex-direction: column;
                gap: 8px;
            }}
            .flow-arrow {{
                transform: rotate(90deg);
                margin: 5px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-container">
            <svg viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/>
            </svg>
        </div>
        <h1>PocketDev Backend</h1>
        <p class="tagline">Webhook server orchestrating GitLab actions & Cloud IDE Agents via Telegram Bot</p>

        <div class="flow-diagram">
            <div class="flow-step">📱 Telegram User</div>
            <div class="flow-arrow">➜</div>
            <div class="flow-step">⚡ FastAPI Server</div>
            <div class="flow-arrow">➜</div>
            <div class="flow-step">🧠 Google Cloud Agent Builder</div>
            <div class="flow-arrow">➜</div>
            <div class="flow-step">🦊 GitLab / Cloud IDE</div>
        </div>

        <table class="status-table">
            <thead>
                <tr>
                    <th>Connection Component</th>
                    <th>Configuration Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>GCP Agent Builder</b> (Reasoning Engine)</td>
                    <td><span class="status-badge {gcp_class}">{gcp_status}</span></td>
                </tr>
                <tr>
                    <td><b>Telegram Bot API</b> (Command Webhook)</td>
                    <td><span class="status-badge {telegram_class}">{telegram_status}</span></td>
                </tr>
                <tr>
                    <td><b>Telegram Group Chat</b> (Team Alerts)</td>
                    <td><span class="status-badge {group_class}">{group_status}</span></td>
                </tr>
                <tr>
                    <td><b>Cloud IDE Agent</b> (Google Antigravity Engine)</td>
                    <td><span class="status-badge success">Connected</span></td>
                </tr>
                <tr>
                    <td><b>GitLab API Wrapper</b> (Execution Layer)</td>
                    <td><span class="status-badge {gitlab_class}">{gitlab_status}</span></td>
                </tr>
                <tr>
                    <td><b>Target GitLab Project ID</b> (Managed Repo)</td>
                    <td><code>{project_id}</code></td>
                </tr>
            </tbody>
        </table>

        <div class="webhook-box">
            <span>Webhook Endpoint: [HOST_URL]{webhook_url}</span>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Renders the dashboard landing page demonstrating system status."""
    gcp_ok = bool(settings.USE_AGENT_BUILDER and settings.GCP_PROJECT_ID and settings.GCP_AGENT_ID)
    gcp_status = "Connected (Agent Builder)" if gcp_ok else ("Inactive (Local SDK)" if not settings.USE_AGENT_BUILDER else "Config Missing")
    gcp_class = "success" if gcp_ok else ("success" if not settings.USE_AGENT_BUILDER else "error")
    
    telegram_status = "Configured" if settings.TELEGRAM_BOT_TOKEN else "Missing Token"
    telegram_class = "success" if settings.TELEGRAM_BOT_TOKEN else "error"
    
    group_status = "Linked" if settings.TELEGRAM_GROUP_CHAT_ID else "Missing Group ID"
    group_class = "success" if settings.TELEGRAM_GROUP_CHAT_ID else "error"
    
    gitlab_ok = bool(settings.GITLAB_PERSONAL_ACCESS_TOKEN and settings.GITLAB_PROJECT_ID)
    gitlab_status = "Linked" if gitlab_ok else "Missing Token/ProjectID"
    gitlab_class = "success" if gitlab_ok else "error"
    
    html_content = LANDING_HTML.format(
        gcp_status=gcp_status,
        gcp_class=gcp_class,
        telegram_status=telegram_status,
        telegram_class=telegram_class,
        group_status=group_status,
        group_class=group_class,
        gitlab_status=gitlab_status,
        gitlab_class=gitlab_class,
        project_id=settings.GITLAB_PROJECT_ID or "Not configured",
        webhook_url=f"/webhook/telegram/{settings.WEBHOOK_SECRET_TOKEN}"
    )
    return html_content

@app.post("/webhook/telegram/{secret_token}")
async def telegram_webhook(secret_token: str, request: Request):
    """
    Webhook Endpoint receiving messages forwarded by Telegram.
    """
    if secret_token != settings.WEBHOOK_SECRET_TOKEN:
        logger.warning(f"Unauthorized Webhook access attempted with token: {secret_token}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Webhook Secret Token"
        )
        
    try:
        update = await request.json()
        logger.info(f"Received Telegram update: {update}")
        
        if "message" not in update:
            return {"status": "ignored", "reason": "Update is not of type Message"}
            
        message = update["message"]
        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        user_id = from_user.get("id")
        
        # 1. Security: Validate that the sender is in the ALLOWED list
        allowed_users = settings.allowed_users
        if allowed_users and user_id not in allowed_users:
            logger.warning(f"Blocked message from unauthorized user ID: {user_id} (@{from_user.get('username')})")
            await send_telegram_message(
                chat_id=chat_id,
                text=(
                    f"⚠️ <b>Access Denied</b>\n\n"
                    f"Your Telegram account (ID: <code>{user_id}</code>) is not authorized to interact with this PocketDev instance.\n"
                    f"Please update the <code>ALLOWED_TELEGRAM_USER_IDS</code> configuration on the backend server."
                )
            )
            return {"status": "forbidden", "reason": "User not allowed"}
            
        # 2. Extract user message
        user_text = message.get("text", "")
        if not user_text:
            return {"status": "ignored", "reason": "Message is empty or contains no text"}
            
        # Intercept Approve/Reject commands from CTO
        user_text_clean = user_text.strip()
        user_text_lower = user_text_clean.lower()
        
        if user_text_lower.startswith("approve "):
            proposal_id = user_text_clean[8:].strip()
            from app.tools.team_tools import review_ide_agent_proposal
            result = review_ide_agent_proposal(proposal_id=proposal_id, action="approve")
            await send_telegram_message(chat_id, result)
            return {"status": "success"}
            
        elif user_text_lower.startswith("reject "):
            parts = user_text_clean[7:].strip().split(maxsplit=1)
            proposal_id = parts[0].strip() if parts else ""
            feedback = parts[1].strip() if len(parts) > 1 else ""
            
            if not feedback:
                await send_telegram_message(
                    chat_id,
                    "⚠️ <b>Error:</b> Please provide feedback when rejecting a proposal.\n"
                    "Example: <code>Reject P-99 Add more unit tests</code>"
                )
                return {"status": "success"}
                
            from app.tools.team_tools import review_ide_agent_proposal
            result = review_ide_agent_proposal(proposal_id=proposal_id, action="reject", feedback=feedback)
            await send_telegram_message(chat_id, result)
            return {"status": "success"}
            
        # 3. Process conversation through Google Cloud Agent Builder OR local SDK fallback
        if settings.USE_AGENT_BUILDER:
            logger.info("Routing conversation to Google Cloud Agent Builder API...")
            from app.agent_builder import detect_intent_agent_builder
            agent_response = await detect_intent_agent_builder(str(chat_id), user_text)
        else:
            logger.info("Routing conversation to local Gemini SDK fallback...")
            agent_response = await agent_manager.process_message(chat_id, user_text)
        
        # 4. Respond to the user
        await send_telegram_message(chat_id, agent_response)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook request: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}

@app.post("/webhook/tools")
async def agent_builder_tools_webhook(request: Request):
    """
    Fulfillment webhook endpoint for Google Cloud Agent Builder.
    Executes Python tools when triggered by the cloud agent.
    """
    try:
        body = await request.json()
        logger.info(f"Received Agent Builder Tool webhook: {body}")
        
        # Extract tag and parameters from Dialogflow CX Webhook Request structure
        fulfillment_info = body.get("fulfillmentInfo", {})
        tag = fulfillment_info.get("tag")
        
        session_info = body.get("sessionInfo", {})
        parameters = session_info.get("parameters", {})
        
        if not tag:
            raise HTTPException(status_code=400, detail="Missing fulfillmentInfo.tag")
            
        # Import maps of registered tools
        from app.agent import TOOL_MAP
        tool_func = TOOL_MAP.get(tag)
        
        if not tool_func:
            result = f"Error: Tool '{tag}' is not registered on the fulfillment backend."
            logger.warning(result)
        else:
            try:
                # Align parameter names and types with the function signature
                sig = inspect.signature(tool_func)
                clean_args = {}
                for param_name, param in sig.parameters.items():
                    if param_name in parameters:
                        val = parameters[param_name]
                        # Handle basic type conversion
                        if param.annotation == int:
                            try:
                                clean_args[param_name] = int(val)
                            except (ValueError, TypeError):
                                clean_args[param_name] = 0
                        elif param.annotation == float:
                            try:
                                clean_args[param_name] = float(val)
                            except (ValueError, TypeError):
                                clean_args[param_name] = 0.0
                        else:
                            clean_args[param_name] = str(val)
                            
                logger.info(f"Executing tool '{tag}' with arguments: {clean_args}")
                result = tool_func(**clean_args)
            except Exception as tool_err:
                logger.error(f"Error running tool {tag}: {tool_err}")
                result = f"Error executing tool {tag}: {str(tool_err)}"
                
        # Return Dialogflow CX compliant Webhook Response
        response_payload = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [result]
                        }
                    }
                ]
            }
        }
        
        return response_payload
    except Exception as e:
        logger.error(f"Error executing Agent Builder Tool webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
