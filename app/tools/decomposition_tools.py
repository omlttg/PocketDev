import json
import logging
import google.generativeai as genai
from app.config import settings
from app.tools.gitlab_tools import create_gitlab_issue, comment_on_issue, get_project

logger = logging.getLogger(__name__)

def decompose_task_into_subissues(task_title: str, task_description: str = "", parent_issue_iid: int = 0) -> str:
    """
    Decomposes a complex task into 2-4 specific sub-issues.
    Creates a parent issue (if not provided) and corresponding sub-issues on GitLab, linking them together.

    Args:
        task_title: Title of the task to decompose (Required).
        task_description: Detailed description of the complex task.
        parent_issue_iid: IID of the existing parent issue. If <= 0, automatically creates a new parent issue.

    Returns:
        The completion status and list of created sub-issues with link URLs.
    """
    if not settings.GEMINI_API_KEY:
        return "❌ <b>Failure:</b> GEMINI_API_KEY is not configured on the system."

    parent_iid = parent_issue_iid
    parent_url = ""
    parent_result = ""

    # 1. Create parent issue if not provided
    if parent_iid <= 0:
        logger.info(f"Creating parent issue for: '{task_title}'")
        parent_result = create_gitlab_issue(
            title=task_title,
            description=task_description,
            labels="epic,complex-task"
        )
        if "Success" in parent_result:
            try:
                # Parse "Success: Created Issue #X" to extract IID
                parts = parent_result.split("#")
                if len(parts) > 1:
                    parent_iid = int(parts[1].split("-")[0].strip())
            except Exception as e:
                logger.error(f"Error parsing parent issue iid: {e}")
        else:
            return f"❌ <b>Failure:</b> Could not create parent issue on GitLab.\nDetail: {parent_result}"

    # Fetch parent issue details if IID is valid
    if parent_iid > 0:
        try:
            project = get_project()
            parent_issue = project.issues.get(parent_iid)
            parent_url = parent_issue.web_url
        except Exception as e:
            logger.error(f"Error fetching parent issue details: {e}")

    # 2. Call Gemini API to decompose the task
    prompt = (
        "You are an excellent Lead Developer. Analyze the complex request below and break it down into 2 to 4 specific, "
        "independent, highly technical, and immediately actionable subtasks.\n\n"
        f"Main Task:\n"
        f"Title: {task_title}\n"
        f"Description: {task_description or 'No detailed description provided.'}\n\n"
        "Output Format Requirement:\n"
        "You MUST return a JSON array containing objects. Do not add any text other than JSON, "
        "and do not wrap it in a markdown code block (no ```json). Structure of each object:\n"
        "[\n"
        "  {\n"
        "    \"title\": \"Concise subtask title in English\",\n"
        "    \"description\": \"Detailed technical description of this subtask in English, steps to implement, and expected outcomes.\",\n"
        "    \"labels\": \"subtask,appropriate_label_name\"\n"
        "  }\n"
        "]"
    )

    subtasks = []
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        subtasks = json.loads(response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini for decomposition: {e}")
        # Retry by stripping formatting block
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            subtasks = json.loads(text.strip())
        except Exception as retry_err:
            return f"❌ <b>Failure:</b> Unable to decompose task via Gemini. Detail: <code>{str(retry_err)}</code>"

    if not isinstance(subtasks, list):
        return "❌ <b>Failure:</b> The AI model did not return a valid list of tasks as a JSON array."

    # 3. Create sub-issues on GitLab and link to parent
    created_subissues = []
    subissue_links_md = []

    for i, task in enumerate(subtasks):
        sub_title = task.get("title", f"Subtask {i+1} for #{parent_iid}")
        sub_desc = task.get("description", "")
        sub_labels = task.get("labels", "subtask")

        # Append link back to the parent issue
        link_desc = sub_desc
        if parent_iid > 0:
            link_desc += f"\n\n---\n*Parent Issue: [#{parent_iid}]({parent_url})*"

        sub_result = create_gitlab_issue(
            title=sub_title,
            description=link_desc,
            labels=sub_labels
        )

        if "Success" in sub_result:
            sub_iid = None
            sub_url = ""
            for line in sub_result.split("\n"):
                if line.startswith("Success: Created Issue"):
                    # Success: Created Issue #X
                    sub_iid = line.split("#")[1].split("-")[0].strip()
                elif line.startswith("Link:"):
                    sub_url = line.replace("Link:", "").strip()
            
            if sub_iid:
                subissue_links_md.append(f"- #{sub_iid}: {sub_title} - Link: {sub_url}")
                created_subissues.append((sub_iid, sub_title, sub_url))
        else:
            logger.error(f"Failed to create subtask '{sub_title}': {sub_result}")

    # 4. Comment on parent issue listing the sub-issues
    if parent_iid > 0 and subissue_links_md:
        comment_body = (
            "### 📋 Automatically Decomposed Sub-issues:\n\n" +
            "\n".join(subissue_links_md)
        )
        comment_on_issue(parent_iid, comment_body)

    # 5. Format response message
    result_msg = ["✅ <b>Task decomposition completed!</b>\n"]
    if parent_iid > 0:
        result_msg.append(f"📌 <b>Parent Issue:</b> <a href=\"{parent_url}\">Issue #{parent_iid} - {task_title}</a>\n")
    
    result_msg.append("🛠️ <b>Created Sub-issues:</b>")
    for link in subissue_links_md:
        result_msg.append(link)

    return "\n".join(result_msg)
