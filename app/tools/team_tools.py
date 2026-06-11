import httpx
import logging
from app.config import settings
from app.tools.gitlab_tools import create_gitlab_issue, accept_merge_request

logger = logging.getLogger(__name__)

# Mock database for Cloud IDE Agent proposals
# In a real MVP, this would query a Cloud DB or the Antigravity Agent API
MOCK_IDE_PROPOSALS = {
    "P-01": {
        "id": "P-01",
        "task": "Implement OAuth2 Google Login",
        "branch": "feature/google-oauth",
        "merge_request_iid": 1,  # Maps to a real or mock Merge Request ID on GitLab
        "changed_files": ["app/routes/auth.py", "app/models/user.py"],
        "status": "PENDING_REVIEW",
        "description": "Added Google login endpoints, user validation schema, and unit tests."
    }
}

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
    # Simulate fetching status from the cloud agent
    status_report = (
        "🤖 <b>Cloud IDE Agent Status:</b> <code>WAITING_FOR_REVIEW</code>\n"
        "💻 <b>Active Branch:</b> <code>feature/google-oauth</code>\n"
        "📈 <b>Last Activity Logs:</b>\n"
        " ├─ [14:15:22] Pulled latest changes from main branch\n"
        " ├─ [14:16:05] Created Google OAuth routes in <code>app/routes/auth.py</code>\n"
        " ├─ [14:16:48] Configured validation schemas in <code>app/models/user.py</code>\n"
        " └─ [14:17:12] Ran pytest suite: 12 tests passed, 0 failed.\n\n"
        "📥 <b>Pending Proposal:</b>\n"
        " ├─ <b>ID:</b> <code>P-01</code>\n"
        " ├─ <b>Title:</b> Implement OAuth2 Google Login\n"
        " ├─ <b>Files:</b> <code>app/routes/auth.py</code>, <code>app/models/user.py</code>\n"
        " └─ <b>Action required:</b> Reply with 'Approve P-01' or 'Reject P-01 [reason]'."
    )
    return status_report

def review_ide_agent_proposal(proposal_id: str, action: str, feedback: str = "") -> str:
    """
    Approve or Reject code changes proposed by the Cloud IDE Agent. 
    Approving will automatically merge the code and run CI/CD pipelines.

    Args:
        proposal_id: The ID of the proposal to review (e.g. 'P-01').
        action: The review decision. Must be 'approve' or 'reject'.
        feedback: Feedback or correction requirements (required if action is 'reject').

    Returns:
        The action execution status.
    """
    proposal = MOCK_IDE_PROPOSALS.get(proposal_id)
    if not proposal:
        return f"Error: Proposal ID '{proposal_id}' was not found."
        
    action_lower = action.lower().strip()
    if action_lower not in ["approve", "reject"]:
        return "Error: Invalid action. Please specify either 'approve' or 'reject'."
        
    if action_lower == "reject" and not feedback:
        return "Error: Feedback is required when rejecting a proposal to help the IDE Agent refactor code."
        
    try:
        if action_lower == "approve":
            # 1. Update mock status
            proposal["status"] = "APPROVED"
            mr_iid = proposal["merge_request_iid"]
            
            # 2. Attempt to accept the Merge Request on GitLab (if MR exists)
            gitlab_merge_msg = accept_merge_request(mr_iid)
            
            result = (
                f"✅ <b>Proposal {proposal_id} APPROVED</b>\n\n"
                f"🚀 <b>Action Taken:</b> Merging branch <code>{proposal['branch']}</code> into main.\n"
                f"🦊 <b>GitLab Action:</b> {gitlab_merge_msg}\n\n"
                f"🎉 The Cloud IDE Agent has been notified. Code integrated, CI/CD pipeline triggered."
            )
            return result
        else:
            # Action: Reject
            proposal["status"] = "REJECTED"
            result = (
                f"❌ <b>Proposal {proposal_id} REJECTED</b>\n\n"
                f"📝 <b>Feedback sent to Cloud IDE Agent:</b> \"{feedback}\"\n\n"
                f"🔄 The Cloud IDE Agent is now rewriting the code on branch <code>{proposal['branch']}</code> based on your feedback."
            )
            return result
            
    except Exception as e:
        logger.error(f"Error in review_ide_agent_proposal: {e}")
        return f"Error reviewing proposal: {str(e)}"
