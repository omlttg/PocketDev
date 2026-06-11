# Technical Specification: PocketDev Core Dev Agent (MVP 1)

* **Specification Code:** 0001-260611-pocketdev-core-agent
* **Created Date:** June 11, 2026
* **Status:** Approved
* **Authors:** Antigravity (AI Coding Assistant) & User

---

## 1. Product Goal
To build a highly mobile software development and coordination assistant (PocketDev) operating via Telegram. Instead of sitting in front of a laptop monitoring AI coding agents, a CTO or Lead Developer can chat with PocketDev from their mobile phone to supervise autonomous Cloud IDE Agents (approving/rejecting code proposals in real-time) and automatically delegate tasks to human developers via Group Chat notifications and GitLab Issues.

---

## 2. Functional Scope

### 2.1. Telegram Interface (CTO Chat & Team Group Chat)
* **CTO Direct Chat:** Receive commands from the authorized CTO, route them to Gemini, and respond with mobile-optimized formatting. Intercepts Approve/Reject commands for instant execution.
* **Team Group Chat Notification:** Automatically broadcast task delegations to the team's Telegram Group Chat, tagging the respective developer (e.g., `@username`).

### 2.2. Agent Brain (Gemini Agent)
* Utilize `gemini-1.5-flash` to parse natural language intentions (e.g., *"Assign UI task to dev A"* or *"Approve the latest code proposal"*).
* Process complex multi-step tool execution loops (Multi-Step Planning) and retain text-based conversation histories.

### 2.3. Core Integration Tools (Superpowers)
* **Team Delegation Tools:**
  * `assign_task_to_developer(developer_username, task_title, task_description)`: Create a GitLab Issue assigned to the developer, and send a structured alert to the Telegram Group Chat tagging the developer.
* **IDE Agent Supervision Tools:**
  * `get_ide_agent_status()`: Fetch the current active proposals and logs of the running IDE Agent.
  * `review_ide_agent_proposal(proposal_id, action, feedback)`: Approve (`approve`) or reject (`reject`) code changes. Approving triggers a GitLab Merge Request merge and kicks off CI/CD.
* **Planning & Architecture Tools:**
  * `analyze_codebase_architecture(file_paths)`: Read and summarize code structure via Gemini.
  * `decompose_task_into_subissues(task_title, task_description, parent_issue_iid)`: Automatically break down complex tasks into sub-tasks on GitLab.

### 2.4. Real-time IDE Agent REST APIs
* `POST /api/agent/proposals`: IDE Agent registers execution proposals (saving to `data/proposals.json` and sending Telegram alerts).
* `GET /api/agent/proposals/{proposal_id}`: Polls proposal status (`PENDING`, `APPROVED`, `REJECTED`).
* `POST /api/agent/logs`: Receives command output logs and forwards them to Telegram.

---

## 3. Technical Architecture

### 3.1. Tech Stack
* **Language:** Python 3.10+
* **Web Framework:** FastAPI (async routing)
* **Generative AI SDK:** `google-generativeai`
* **GitLab SDK:** `python-gitlab`
* **HTTP Client:** `httpx` (for calling Telegram API and broadcasting to group chats)
* **Configuration:** `python-dotenv` & `pydantic-settings`

### 3.2. Model Context Protocol (MCP) Client
* PocketDev implements an **MCP Client Adapter** in [gitlab_tools.py](file:///home/thienvu/workspace/PocketDev/app/tools/gitlab_tools.py).
* When `USE_MCP_SERVER=True`, GitLab tools route commands through an external GitLab MCP Server via standard JSON-RPC HTTP POST requests instead of invoking the python-gitlab SDK directly.

### 3.3. Data Flow & Environment Variables
* `TELEGRAM_BOT_TOKEN`: Token for PocketDev chatbot.
* `ALLOWED_TELEGRAM_USER_IDS`: CTO's account ID for authorization.
* `TELEGRAM_GROUP_CHAT_ID`: The target group chat ID where the team coordinates.
* `GITLAB_PERSONAL_ACCESS_TOKEN`: API Token with write access.
* `GITLAB_PROJECT_ID`: Target repository ID.
* `WEBHOOK_SECRET_TOKEN`: Security token securing the inbound Telegram API webhook.
* `USE_MCP_SERVER`: Enable/disable GitLab MCP Server routing.
* `MCP_SERVER_URL`: Target endpoint of the GitLab MCP Server.

---

## 4. Acceptance Criteria
1. Sending `"Assign backend fix to dev_john"` creates an Issue on GitLab assigned to `dev_john` and posts an announcement in the Telegram Group Chat tagging `@dev_john`.
2. IDE Agent submitting a proposal triggers a push Telegram message. Replying `"Approve P-01"` updates the status to `APPROVED` and merges the MR.
3. The IDE Agent polling the API receives status updates, executes tasks, and sends terminal outputs via the logs endpoint, showing them on Telegram.
4. The Web Dashboard interface displays the complete connection status of both the Telegram Group Chat and the IDE Agent.
