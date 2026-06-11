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

# Danh sách tất cả các tools xuất ra để Gemini sử dụng làm Function Callings
GITLAB_TOOLS = [
    create_gitlab_issue,
    list_gitlab_issues,
    comment_on_issue,
    list_gitlab_branches,
    get_file_content,
    create_merge_request,
    accept_merge_request,
    list_pipeline_statuses,
    trigger_pipeline_retry
]
