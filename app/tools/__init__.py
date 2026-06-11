from .gitlab_tools import (
    create_gitlab_issue,
    list_gitlab_issues,
    comment_on_issue,
    list_gitlab_branches,
    get_file_content,
    create_merge_request,
    accept_merge_request,
    list_pipeline_statuses,
    trigger_pipeline_retry
)
from .team_tools import (
    assign_task_to_developer,
    get_ide_agent_status,
    review_ide_agent_proposal
)

# Export all tools for the Gemini Agent
GITLAB_TOOLS = [
    create_gitlab_issue,
    list_gitlab_issues,
    comment_on_issue,
    list_gitlab_branches,
    get_file_content,
    create_merge_request,
    accept_merge_request,
    list_pipeline_statuses,
    trigger_pipeline_retry,
    assign_task_to_developer,
    get_ide_agent_status,
    review_ide_agent_proposal
]
