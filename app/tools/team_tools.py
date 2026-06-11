import os
import json
import httpx
import logging
from app.config import settings
from app.tools.gitlab_tools import create_gitlab_issue, accept_merge_request

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROPOSALS_FILE = os.path.join(PROJECT_ROOT, "data", "proposals.json")

def load_proposals() -> dict:
    os.makedirs(os.path.dirname(PROPOSALS_FILE), exist_ok=True)
    if not os.path.exists(PROPOSALS_FILE):
        try:
            with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception as err:
            logger.error(f"Error creating proposals file: {err}")
        return {}
    try:
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading proposals: {e}")
        return {}

def save_proposals(proposals: dict):
    os.makedirs(os.path.dirname(PROPOSALS_FILE), exist_ok=True)
    try:
        with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
            json.dump(proposals, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving proposals: {e}")

# ==========================================
# 1. TEAM COORDINATION TOOLS
# ==========================================

def assign_task_to_developer(developer_username: str, task_title: str, task_description: str = "") -> str:
    """
    Assign a development task to a developer. Creates a GitLab Issue and alerts the team on Telegram Group Chat.

    Args:
        developer_username: The GitLab username of the developer (e.g. 'john_dev').
        task_title: The title of the task / issue.
        task_description: Detailed description of what needs to be done.

    Returns:
        Confirmation status of the task assignment.
    """
    try:
        # 1. Create the Issue on GitLab using the existing GitLab tool
        gitlab_result = create_gitlab_issue(
            title=task_title,
            description=task_description,
            assignee_username=developer_username,
            labels="assigned-by-cto"
        )
        
        # Extract issue link from the gitlab_result if possible
        issue_link = ""
        for line in gitlab_result.split("\n"):
            if line.startswith("Link:"):
                issue_link = line.replace("Link:", "").strip()
                
        # 2. Format notification message for the Telegram Group Chat
        group_msg = (
            f"🔔 <b>New Task Assigned</b>\n\n"
            f"👤 <b>Developer:</b> @{developer_username}\n"
            f"📋 <b>Task:</b> {task_title}\n"
            f"📝 <b>Details:</b> {task_description or 'No extra details provided.'}\n\n"
        )
        if issue_link:
            group_msg += f"🔗 <b>GitLab Issue:</b> <a href=\"{issue_link}\">View on GitLab</a>"
        else:
            group_msg += f"⚠️ <i>Note: GitLab Issue creation returned: {gitlab_result}</i>"
            
        # 3. Broadcast to Telegram Group Chat using synchronous httpx (to avoid async event loop conflicts)
        if not settings.TELEGRAM_GROUP_CHAT_ID:
            return f"{gitlab_result}\n\nWarning: TELEGRAM_GROUP_CHAT_ID is not configured. Group notification skipped."
            
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": settings.TELEGRAM_GROUP_CHAT_ID,
            "text": group_msg,
            "parse_mode": "HTML"
        }
        
        with httpx.Client() as client:
            response = client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info(f"Successfully posted task assignment to group {settings.TELEGRAM_GROUP_CHAT_ID}")
                return f"{gitlab_result}\n\nGroup Alert: Tagged @{developer_username} in the Team Group Chat successfully."
            else:
                logger.error(f"Failed to send Telegram Group Alert: {response.text}")
                return f"{gitlab_result}\n\nWarning: Failed to send Group Alert (Telegram API returned status {response.status_code})."
                
    except Exception as e:
        logger.error(f"Error in assign_task_to_developer: {e}")
        return f"Error delegating task: {str(e)}"

# ==========================================
# 2. CLOUD IDE AGENT MONITORING TOOLS
# ==========================================

def get_ide_agent_status() -> str:
    """
    Retrieve the status, active logs, and pending code changes from the Cloud IDE Agent (Google Antigravity SDK).

    Returns:
        A formatted status log showing the IDE Agent activity and code proposals.
    """
    proposals = load_proposals()
    pending = [p for p in proposals.values() if p.get("status") in ["PENDING_REVIEW", "PENDING"]]
    
    if not pending:
        return (
            "🤖 <b>Cloud IDE Agent Status:</b> <code>IDLE / WAITING</code>\n"
            "💻 No active branch code proposals are currently pending review."
        )
        
    status_report = [
        "🤖 <b>Cloud IDE Agent Status:</b> <code>WAITING_FOR_REVIEW</code>\n"
        "📈 <b>Pending Proposals:</b>"
    ]
    for p in pending:
        changed = ", ".join(p.get("changed_files", [])) if p.get("changed_files") else "None"
        cmd = p.get("command", "")
        cmd_str = f"\n ├─ <b>Command:</b> <code>{cmd}</code>" if cmd else ""
        status_report.append(
            f" ├─ <b>ID:</b> <code>{p['id']}</code>\n"
            f" ├─ <b>Task:</b> {p['task']}\n"
            f" ├─ <b>Description:</b> {p.get('description', '')}"
            f"{cmd_str}\n"
            f" ├─ <b>Files:</b> <code>{changed}</code>\n"
            f" └─ <b>Action required:</b> Reply with 'Approve {p['id']}' or 'Reject {p['id']} [reason]'."
        )
    return "\n\n".join(status_report)

def review_ide_agent_proposal(proposal_id: str, action: str, feedback: str = "") -> str:
    """
    Approve or Reject code changes proposed by the Cloud IDE Agent. 
    Approving will automatically merge the code (if merge_request_iid is present) and run CI/CD pipelines.

    Args:
        proposal_id: The ID of the proposal to review (e.g. 'P-01').
        action: The review decision. Must be 'approve' or 'reject'.
        feedback: Feedback or correction requirements (required if action is 'reject').

    Returns:
        The action execution status.
    """
    proposals = load_proposals()
    proposal = proposals.get(proposal_id)
    if not proposal:
        return f"Error: Proposal ID '{proposal_id}' was not found."
        
    action_lower = action.lower().strip()
    if action_lower not in ["approve", "reject"]:
        return "Error: Invalid action. Please specify either 'approve' or 'reject'."
        
    if action_lower == "reject" and not feedback:
        return "Error: Feedback is required when rejecting a proposal to help the IDE Agent refactor code."
        
    try:
        if action_lower == "approve":
            proposal["status"] = "APPROVED"
            mr_iid = proposal.get("merge_request_iid")
            
            gitlab_merge_msg = ""
            if mr_iid:
                try:
                    gitlab_merge_msg = f"\n🦊 <b>GitLab Action:</b> {accept_merge_request(int(mr_iid))}"
                except Exception as mr_err:
                    gitlab_merge_msg = f"\n⚠️ <i>Failed to merge MR: {mr_err}</i>"
            
            save_proposals(proposals)
            
            result = (
                f"✅ <b>Proposal {proposal_id} APPROVED</b>\n\n"
                f"🚀 <b>Action Taken:</b> Proposal marked as approved.{gitlab_merge_msg}\n\n"
                f"🎉 The Cloud IDE Agent has been notified."
            )
            return result
        else:
            # Action: Reject
            proposal["status"] = "REJECTED"
            proposal["feedback"] = feedback
            save_proposals(proposals)
            
            result = (
                f"❌ <b>Proposal {proposal_id} REJECTED</b>\n\n"
                f"📝 <b>Feedback sent to Cloud IDE Agent:</b> \"{feedback}\"\n\n"
                f"🔄 The Cloud IDE Agent is now notified to rewrite or refactor based on your feedback."
            )
            return result
            
    except Exception as e:
        logger.error(f"Error in review_ide_agent_proposal: {e}")
        return f"Error reviewing proposal: {str(e)}"
