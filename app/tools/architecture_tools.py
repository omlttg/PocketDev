import os
import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

def analyze_codebase_architecture(file_paths: str = "") -> str:
    """
    Analyzes the source code architecture of the specified files (comma-separated) or automatically scans the 'app' directory.
    Reads contents and uses Gemini API to generate a concise structural summary in Markdown.

    Args:
        file_paths: Comma-separated relative paths to files (e.g. 'app/main.py,app/agent.py').
                    If empty, scans the entire 'app' directory.

    Returns:
        A concise Markdown analysis report suitable for Telegram.
    """
    if not settings.GEMINI_API_KEY:
        return "❌ <b>Failure:</b> GEMINI_API_KEY is not configured on the system."

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    files_to_read = []

    if file_paths:
        paths = [p.strip() for p in file_paths.split(",") if p.strip()]
        for p in paths:
            # Ensure safety and avoid path traversal
            abs_path = os.path.abspath(os.path.join(project_root, p))
            if abs_path.startswith(project_root) and os.path.exists(abs_path) and os.path.isfile(abs_path):
                files_to_read.append((p, abs_path))
    else:
        # Scan the app/ directory
        app_dir = os.path.join(project_root, "app")
        if os.path.exists(app_dir):
            for root, dirs, files in os.walk(app_dir):
                if "__pycache__" in root:
                    continue
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, project_root)
                        files_to_read.append((rel_path, full_path))

    if not files_to_read:
        return "⚠️ No source files found to analyze."

    # Limit maximum file count to avoid token overflow
    files_to_read = files_to_read[:10]

    code_contents = []
    for rel_path, abs_path in files_to_read:
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Truncate if file is too long
                if len(content) > 3000:
                    content = content[:3000] + "\n... [File content truncated] ..."
                code_contents.append(f"### File: {rel_path}\n```python\n{content}\n```")
        except Exception as e:
            logger.error(f"Error reading file {abs_path}: {e}")
            code_contents.append(f"### File: {rel_path}\nError reading: {str(e)}")

    prompt = (
        "You are a talented Software Architect. Analyze the source code structure of the files below "
        "and provide an extremely concise and clear system architecture summary so the CTO can read it quickly on a Telegram mobile screen.\n\n"
        "Report requirements:\n"
        "1. Overall Structure: Brief overview of the architecture and interaction/data flows between the main files/modules.\n"
        "2. Component Breakdown: Briefly state the primary role of each file.\n"
        "3. Quality Assessment/Recommendations (if any).\n\n"
        "Please write in concise English using intuitive emojis. Limit the response to around 3000 characters.\n\n"
        "Source code to analyze:\n\n" + "\n\n".join(code_contents)
    )

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API in analyze_codebase_architecture: {e}")
        return f"❌ <b>System Error:</b> Unable to analyze the architecture via Gemini API. Detail: <code>{str(e)}</code>"
