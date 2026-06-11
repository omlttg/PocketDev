# Technical Specification: PocketDev Core Dev Agent (MVP 1)

* **Specification Code:** 0001-260611-pocketdev-core-agent
* **Created Date:** June 11, 2026
* **Status:** Draft
* **Authors:** Antigravity (AI Coding Assistant) & User

---

## 1. Product Goal
To build a highly mobile software development and coordination assistant (PocketDev) operating via Telegram. Instead of sitting in front of a laptop monitoring AI coding agents, a CTO or Lead Developer can chat with PocketDev from their mobile phone to supervise autonomous Cloud IDE Agents (approving/rejecting code proposals) and automatically delegate tasks to human developers via Group Chat notifications and GitLab Issues.

---

## 2. Functional Scope

### 2.1. Telegram Interface (CTO Chat & Team Group Chat)
* **CTO Direct Chat:** Receive commands from the authorized CTO, route them to Gemini, and respond with mobile-optimized formatting.
* **Team Group Chat Notification:** Automatically broadcast task delegations to the team's Telegram Group Chat, tagging the respective developer (e.g., `@"username"`).

### 2.2. Agent Brain (Gemini Agent)
* Utilize `gemini-1.5-flash` to parse natural language intentions (e.g., *"Assign UI task to dev A"* or *"Approve the latest code proposal"*).
* Process complex multi-step tool execution loops and retain text-based conversation histories.

### 2.3. Core Integration Tools (Superpowers)
* **Team Delegation Tools:**
  * `assign_task_to_developer(developer_username, task_title, task_description)`: Create a GitLab Issue assigned to the developer, and send a structured alert to the Telegram Group Chat tagging the developer.
* **IDE Agent Supervision Tools:**
  * `get_ide_agent_status()`: Fetch the current state, logs, and pending code changes proposed by the autonomous IDE coding agent running on the cloud.
  * `review_ide_agent_proposal(proposal_id, action, feedback)`: Approve (`approve`) or reject (`reject`) code changes. Approving triggers a GitLab Merge Request merge and kicks off CI/CD.
* **GitLab Management Tools:** Standard capabilities for issue tracking, branch queries, file reading, and CI/CD pipeline monitoring.

---

## 3. Technical Architecture

### 3.1. Tech Stack
* **Language:** Python 3.10+
* **Web Framework:** FastAPI (async routing)
* **Generative AI SDK:** `google-generativeai`
* **GitLab SDK:** `python-gitlab`
* **HTTP Client:** `httpx` (for calling Telegram API and broadcasting to group chats)
* **Configuration:** `python-dotenv` & `pydantic-settings`

### 3.2. Data Flow & Environment Variables
* `TELEGRAM_BOT_TOKEN`: Token for PocketDev chatbot.
* `ALLOWED_TELEGRAM_USER_IDS`: CTO's account ID for authorization.
* `TELEGRAM_GROUP_CHAT_ID`: The target group chat ID (e.g., `-100xxxxxxxxx`) where the development team coordinates.
* `GITLAB_PERSONAL_ACCESS_TOKEN`: API Token with write access.
* `GITLAB_PROJECT_ID`: Target repository ID.
* `WEBHOOK_SECRET_TOKEN`: Security token securing the inbound Telegram API webhook.

---

## 4. Acceptance Criteria
1. Sending `"Assign backend fix to dev_john"` creates an Issue on GitLab assigned to `dev_john` and posts an announcement in the Telegram Group Chat tagging `@dev_john`.
2. Sending `"Check IDE Agent status"` returns logs showing what the Cloud coding agent is working on and lists pending code proposals.
3. Sending `"Approve code proposal P-01"` automatically approves the proposal, creates a Merge Request, merges it into the main branch, and triggers the GitLab Pipeline.
4. Giao diện Web Dashboard hiển thị đầy đủ trạng thái kết nối của cả Telegram Group Chat và IDE Agent.
