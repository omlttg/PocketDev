import gitlab
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# GitLab client instance (lazy initialized)
gl = None

def get_gitlab_client():
    global gl
    if gl is None:
        if not settings.GITLAB_PERSONAL_ACCESS_TOKEN:
            raise ValueError("GITLAB_PERSONAL_ACCESS_TOKEN is not configured in the .env file!")
        gl = gitlab.Gitlab(url=settings.GITLAB_URL, private_token=settings.GITLAB_PERSONAL_ACCESS_TOKEN)
    return gl

def get_project():
    """Retrieve the GitLab project instance based on the configured GITLAB_PROJECT_ID."""
    client = get_gitlab_client()
    if not settings.GITLAB_PROJECT_ID:
        raise ValueError("GITLAB_PROJECT_ID is not configured in the .env file!")
    return client.projects.get(settings.GITLAB_PROJECT_ID)

# ==========================================
# 1. ISSUE MANAGEMENT GROUP
# ==========================================

def create_gitlab_issue(title: str, description: str = "", assignee_username: str = "", labels: str = "") -> str:
    """
    Create a new Issue in the GitLab project.

    Args:
        title: The title of the Issue. Required.
        description: Detailed description of the Issue or steps to reproduce a bug.
        assignee_username: GitLab username of the person to assign (e.g., 'dev_a'). Leave empty if none.
        labels: Comma-separated list of labels to assign (e.g., 'bug,frontend').

    Returns:
        A string message containing the creation status, Issue ID, and URL link.
    """
    try:
        project = get_project()
        issue_data = {
            'title': title,
            'description': description
        }
        
        # Search User ID by username
        if assignee_username:
            client = get_gitlab_client()
            users = client.users.list(username=assignee_username)
            if users:
                issue_data['assignee_ids'] = [users[0].id]
            else:
                logger.warning(f"GitLab user not found with username: {assignee_username}")
                
        # Parse labels
        if labels:
            issue_data['labels'] = [l.strip() for l in labels.split(",") if l.strip()]
            
        issue = project.issues.create(issue_data)
        return f"Success: Created Issue #{issue.iid} - '{issue.title}' on GitLab.\nLink: {issue.web_url}"
    except Exception as e:
        logger.error(f"Error in create_gitlab_issue: {e}")
        return f"Failure: Could not create Issue. Error detail: {str(e)}"

def list_gitlab_issues(state: str = "opened", labels: str = "") -> str:
    """
    List existing Issues on the GitLab project.

    Args:
        state: State of the issues to filter. Valid values: 'opened', 'closed', 'all'. Default is 'opened'.
        labels: Filter issues by labels (comma-separated list, e.g., 'bug,critical').

    Returns:
        A formatted list of Issues.
    """
    try:
        project = get_project()
        params = {'state': state}
        if labels:
            params['labels'] = [l.strip() for l in labels.split(",") if l.strip()]
            
        issues = project.issues.list(**params, get_all=False, page=1, per_page=15)
        if not issues:
            return f"No issues found in state '{state}'."
            
        result = [f"Issues list ({state}):"]
        for issue in issues:
            assignee = issue.assignee['username'] if issue.assignee else "Unassigned"
            lbls = f" [{', '.join(issue.labels)}]" if issue.labels else ""
            result.append(f"- #{issue.iid}: {issue.title} (Assignee: {assignee}){lbls} - Link: {issue.web_url}")
        return "\n".join(result)
    except Exception as e:
        logger.error(f"Error in list_gitlab_issues: {e}")
        return f"Error retrieving issues: {str(e)}"

def comment_on_issue(issue_iid: int, body: str) -> str:
    """
    Add a comment/note to a specific GitLab Issue.

    Args:
        issue_iid: The IID (Internal ID) of the Issue to comment on (e.g., 12).
        body: The content of the comment (Markdown supported).

    Returns:
        Status message of the operation.
    """
    try:
        project = get_project()
        issue = project.issues.get(issue_iid)
        issue.notes.create({'body': body})
        return f"Success: Added comment to Issue #{issue_iid}."
    except Exception as e:
        logger.error(f"Error in comment_on_issue: {e}")
        return f"Failure: Could not comment on Issue #{issue_iid}. Error: {str(e)}"

# ==========================================
# 2. REPOSITORY & MERGE REQUEST GROUP
# ==========================================

def list_gitlab_branches() -> str:
    """
    List all branches present in the GitLab repository.

    Returns:
        A list of branches along with their latest commit information.
    """
    try:
        project = get_project()
        branches = project.branches.list(get_all=False, page=1, per_page=20)
        if not branches:
            return "No branches found in the repository."
            
        result = ["Repository Branches:"]
        for b in branches:
            status = " [Default]" if b.default else ""
            result.append(f"- {b.name}{status} (Latest Commit: {b.commit['short_id']} - {b.commit['title']})")
        return "\n".join(result)
    except Exception as e:
        logger.error(f"Error in list_gitlab_branches: {e}")
        return f"Error retrieving branches: {str(e)}"

def get_file_content(file_path: str, ref: str = "main") -> str:
    """
    Retrieve and read the source code content of a specific file in the repository.

    Args:
        file_path: Relative path to the file (e.g., 'app/main.py' or 'src/index.js').
        ref: Branch name or commit hash to read the file from. Default is 'main'.

    Returns:
        The content of the file or an error message.
    """
    try:
        project = get_project()
        f = project.files.get(file_path=file_path, ref=ref)
        content = f.decode().decode('utf-8')
        # Limit response characters to avoid exceeding Telegram size limits (approx 3500 chars)
        if len(content) > 3000:
            content = content[:3000] + "\n\n... [File content too long, truncated] ..."
        return f"Source file '{file_path}' (ref '{ref}'):\n```\n{content}\n```"
    except Exception as e:
        logger.error(f"Error in get_file_content: {e}")
        return f"Error reading file '{file_path}': {str(e)}"

def create_merge_request(source_branch: str, target_branch: str, title: str, description: str = "") -> str:
    """
    Create a new Merge Request (MR) in the GitLab project.

    Args:
        source_branch: The source branch containing new changes (e.g., 'feature-x').
        target_branch: The target branch to merge into (e.g., 'main' or 'develop').
        title: Title of the Merge Request.
        description: Detailed descriptions of changes included in this MR.

    Returns:
        Operation status and the Merge Request URL.
    """
    try:
        project = get_project()
        mr_data = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
            'description': description
        }
        mr = project.mergerequests.create(mr_data)
        return f"Success: Created Merge Request #{mr.iid} from '{source_branch}' into '{target_branch}'.\nMR Link: {mr.web_url}"
    except Exception as e:
        logger.error(f"Error in create_merge_request: {e}")
        return f"Failure: Could not create Merge Request. Error: {str(e)}"

def accept_merge_request(mr_iid: int) -> str:
    """
    Approve and merge (accept) an open Merge Request.

    Args:
        mr_iid: The IID (Internal ID) of the Merge Request to accept (e.g., 3).

    Returns:
        Status message of the merge action.
    """
    try:
        project = get_project()
        mr = project.mergerequests.get(mr_iid)
        merged_mr = mr.accept()
        return f"Success: Approved and merged MR #{mr_iid} - '{merged_mr.title}'."
    except Exception as e:
        logger.error(f"Error in accept_merge_request: {e}")
        return f"Failure: Could not merge MR #{mr_iid}. Error: {str(e)}"

# ==========================================
# 3. CI/CD PIPELINE GROUP
# ==========================================

def list_pipeline_statuses(ref: str = "", limit: int = 5) -> str:
    """
    View the status of recent CI/CD Pipelines on the project.

    Args:
        ref: Filter pipelines by branch name (e.g., 'main'). Leave empty for all branches.
        limit: Number of pipelines to list. Default is 5.

    Returns:
        A list of pipelines with status and URL.
    """
    try:
        project = get_project()
        params = {}
        if ref:
            params['ref'] = ref
            
        pipelines = project.pipelines.list(**params, get_all=False, page=1, per_page=limit)
        if not pipelines:
            return "No pipelines found."
            
        result = [f"Latest {len(pipelines)} Pipelines:"]
        for p in pipelines:
            result.append(f"- ID #{p.id} ({p.ref}) -> Status: **{p.status}** - Link: {p.web_url}")
        return "\n".join(result)
    except Exception as e:
        logger.error(f"Error in list_pipeline_statuses: {e}")
        return f"Error retrieving pipeline status: {str(e)}"

def trigger_pipeline_retry(pipeline_id: int) -> str:
    """
    Retry a failed or canceled CI/CD Pipeline.

    Args:
        pipeline_id: ID of the pipeline to retry (e.g., 124590).

    Returns:
        Operation status of the retry trigger.
    """
    try:
        project = get_project()
        pipeline = project.pipelines.get(pipeline_id)
        new_pipeline = pipeline.retry()
        return f"Success: Triggered retry for Pipeline #{pipeline_id}. New status: {new_pipeline.status}."
    except Exception as e:
        logger.error(f"Error in trigger_pipeline_retry: {e}")
        return f"Failure: Could not retry Pipeline #{pipeline_id}. Error: {str(e)}"
