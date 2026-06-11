import httpx
import logging
import google.auth
import google.auth.transport.requests
from app.config import settings

logger = logging.getLogger(__name__)

async def detect_intent_agent_builder(session_id: str, text: str) -> str:
    """
    Sends a chat message to the Google Cloud Agent Builder API (Dialogflow CX / Vertex AI Agent endpoint).
    Uses Application Default Credentials (ADC) to authenticate Google API calls dynamically.
    """
    if not settings.GCP_PROJECT_ID or not settings.GCP_AGENT_ID:
        raise ValueError("GCP_PROJECT_ID and GCP_AGENT_ID must be configured in .env to use Google Cloud Agent Builder.")
        
    try:
        # Get Google OAuth2 Access Token using Application Default Credentials (ADC)
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token
    except Exception as auth_err:
        logger.error(f"Error obtaining Google Application Default Credentials (ADC): {auth_err}")
        return (
            f"❌ <b>Google Cloud Auth Error</b>\n\n"
            f"Unable to load Google Application Default Credentials. "
            f"If running locally, please run: <code>gcloud auth application-default login</code>. "
            f"Detail: <code>{str(auth_err)}</code>"
        )

    # Dialogflow CX / Agent Builder REST API URL format
    url = (
        f"https://{settings.GCP_LOCATION}-dialogflow.googleapis.com/v3/"
        f"projects/{settings.GCP_PROJECT_ID}/"
        f"locations/{settings.GCP_LOCATION}/"
        f"agents/{settings.GCP_AGENT_ID}/"
        f"sessions/{session_id}:detectIntent"
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "queryInput": {
            "text": {
                "text": text
            },
            "languageCode": "en"  # Standard code, Gemini parses multi-lingual internally
        }
    }
    
    logger.info(f"Sending message to Google Cloud Agent Builder. URL: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                query_result = data.get("queryResult", {})
                response_messages = query_result.get("responseMessages", [])
                
                # Parse all text messages returned by the Agent
                text_responses = []
                for msg in response_messages:
                    if "text" in msg and "text" in msg["text"]:
                        text_responses.extend(msg["text"]["text"])
                        
                if text_responses:
                    return "\n".join(text_responses)
                return "Google Cloud Agent Builder returned an empty response."
            else:
                logger.error(f"Google Cloud Agent Builder API returned status {response.status_code}: {response.text}")
                return (
                    f"❌ <b>Google Cloud Agent Builder API Error</b>\n\n"
                    f"Status code: <code>{response.status_code}</code>\n"
                    f"Detail: <code>{response.text}</code>"
                )
        except Exception as e:
            logger.error(f"Network error calling Google Cloud Agent Builder API: {e}")
            return f"❌ <b>Network Error</b>\n\nFailed to connect to Google Cloud Agent Builder: <code>{str(e)}</code>"
