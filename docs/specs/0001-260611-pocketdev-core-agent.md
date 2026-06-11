# Technical Specification: PocketDev Core Dev Agent (MVP 1)

* **Specification Code:** 0001-260611-pocketdev-core-agent
* **Created Date:** June 11, 2026
* **Status:** Draft
* **Authors:** Antigravity (AI Coding Assistant) & User

---

## 1. Product Goal
To build a highly mobile software development assistant (Core Dev Agent) operating via Telegram. It allows managers and developers to orchestrate source code, manage Issues, and monitor CI/CD pipelines on GitLab directly from their mobile chat interface.

---

## 2. Functional Scope

### 2.1. Telegram Interface (Receiving & Responding)
* Receive incoming text commands from Telegram users via a secure public HTTPS webhook endpoint.
* Authenticate incoming requests (only allow interaction from pre-configured Telegram User IDs to ensure system security).
* Send formatted Markdown responses back to the user's Telegram chat interface.

### 2.2. Agent Brain (Gemini Agent)
* Utilize the `gemini-1.5-flash` model for high-speed, advanced reasoning.
* System Instructions define the persona as a wise, concise, action-oriented "Pocket CTO / Lead Developer" who gets straight to the point.
* Maintain conversation context locally via an in-memory cache backed up by local JSON files.

### 2.3. GitLab Integration via Function Calling (Tools)
The Agent is equipped with Python tools mapping directly to the GitLab REST API:
* **Issue Management:**
  * `create_gitlab_issue(title, description, assignee_username, labels)`: Create a new Issue.
  * `list_gitlab_issues(state, labels)`: Query project Issues.
  * `comment_on_issue(issue_iid, body)`: Post comments on specific Issues.
* **Repository & MR Management:**
  * `list_gitlab_branches()`: List all git branches.
  * `get_file_content(file_path, ref)`: Read source code of a file.
  * `create_merge_request(source_branch, target_branch, title, description)`: Open a Merge Request.
  * `accept_merge_request(mr_iid)`: Merge an open Merge Request.
* **CI/CD Pipeline Management:**
  * `list_pipeline_statuses(ref, limit)`: Monitor recent CI/CD run statuses.
  * `trigger_pipeline_retry(pipeline_id)`: Re-run a failed pipeline.

---

## 3. Technical Architecture

### 3.1. Tech Stack
* **Language:** Python 3.10+
* **Web Framework:** FastAPI (for high-performance async capabilities)
* **Generative AI SDK:** `google-generativeai`
* **GitLab SDK:** `python-gitlab`
* **HTTP Client:** `httpx` (for calling the Telegram Bot API asynchronously)
* **Configuration:** `python-dotenv` & `pydantic-settings`

### 3.2. Security and Data Flow
* Sensitive credentials (`TELEGRAM_BOT_TOKEN`, `GITLAB_PERSONAL_ACCESS_TOKEN`, `GEMINI_API_KEY`, `ALLOWED_TELEGRAM_USER_IDS`) must be stored in a `.env` file and loaded into environment variables.
* The Telegram webhook endpoint (`/webhook/telegram/{secret_token}`) utilizes a random secret token to prevent spam and unauthorized requests.

---

## 4. Acceptance Criteria
1. Sending a greeting on Telegram results in the Bot introducing itself as the PocketDev CTO Agent in English.
2. Sending a command like `"Create a new issue titled 'Fix dark mode footer' on GitLab"` triggers the issue creation tool and returns the new Issue ID & URL.
3. Sending `"Check pipeline status for main branch"` returns the latest status (Success/Failed/Running) of the corresponding pipeline.
4. Chat history is preserved across consecutive messages (the agent remembers previous context).
