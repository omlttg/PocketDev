import re
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def markdown_to_telegram_html(text: str) -> str:
    """
    Convert basic Markdown syntax from Gemini into Telegram-compatible HTML tags.
    Supports:
      - **bold** -> <b>bold</b>
      - *italic* or _italic_ -> <i>italic</i>
      - ```code block``` -> <pre><code>code block</code></pre>
      - `inline code` -> <code>inline code</code>
      - [link text](url) -> <a href="url">link text</a>
    """
    if not text:
        return ""
        
    # Check if the text already contains HTML formatting tags to bypass markdown conversion and escaping
    html_tags = ["<b>", "</b>", "<code>", "</code>", "<i>", "</i>", "<pre>", "</pre>", "<a ", "</a>"]
    if any(tag in text for tag in html_tags):
        return text
        
    # 1. Escape HTML special characters first to avoid invalid nested tags
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 2. Extract and protect Code Blocks
    code_blocks = []
    def save_code_block(match):
        code_content = match.group(2)
        code_blocks.append(code_content)
        return f"__CODE_BLOCK_PLACEHOLDER_{len(code_blocks)-1}__"
        
    text = re.sub(r"```(\w*)\n([\s\S]*?)\n```", save_code_block, text)
    text = re.sub(r"```([\s\S]*?)```", save_code_block, text)

    # 3. Extract and protect Inline Code
    inline_codes = []
    def save_inline_code(match):
        code_content = match.group(1)
        inline_codes.append(code_content)
        return f"__INLINE_CODE_PLACEHOLDER_{len(inline_codes)-1}__"
    text = re.sub(r"`([^`\n]+)`", save_inline_code, text)

    # 4. Handle Bold (**text**)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    # 5. Handle Italic (*text*)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)

    # 6. Handle Links ([text](url))
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # 7. Restore Inline Code to <code> tags
    for i, code in enumerate(inline_codes):
        text = text.replace(f"__INLINE_CODE_PLACEHOLDER_{i}__", f"<code>{code}</code>")

    # 8. Restore Code Blocks to <pre><code> tags
    for i, code in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_PLACEHOLDER_{i}__", f"<pre><code>{code}</code></pre>")

    return text

async def send_telegram_message(chat_id: int, text: str) -> bool:
    """
    Send a text message to a Telegram Chat ID using HTML parse mode.
    Automatically converts Gemini's Markdown responses to HTML.
    """
    html_text = markdown_to_telegram_html(text)
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to send Telegram message (HTML): {response.status_code} - {response.text}")
                # Fallback: attempt to send raw text if HTML parser fails
                if "can't parse entities" in response.text or "bad request" in response.text.lower():
                    logger.warning("HTML parsing failed on Telegram side. Retrying with raw plain text...")
                    fallback_payload = {
                        "chat_id": chat_id,
                        "text": text  # Send the original raw markdown text
                    }
                    fallback_response = await client.post(url, json=fallback_payload, timeout=15.0)
                    return fallback_response.status_code == 200
                return False
        except Exception as e:
            logger.error(f"Network error calling Telegram API: {e}")
            return False
