# Implementation Plan: PocketDev Core Dev Agent (MVP 1)

* **Plan Code:** 0001-260611-pocketdev-core-agent-plan
* **Associated Spec:** 0001-260611-pocketdev-core-agent
* **Created Date:** June 11, 2026
* **Status:** Completed
* **Authors:** Antigravity (AI Coding Assistant) & User

---

## 1. Task List

### Phase 1: Environment Setup & Configuration
* [x] **Task 1.1:** Initialize project and create `requirements.txt`.
* [x] **Task 1.2:** Create `.env.example` and load settings safely in `app/config.py`.
* [x] **Task 1.3:** Add `TELEGRAM_GROUP_CHAT_ID` configurations to `.env.example` and `app/config.py`.

### Phase 2: Core Module Development
* [x] **Task 2.1:** Write the `app/telegram_bot.py` helper to send messages back to Telegram.
* [x] **Task 2.2:** Build GitLab API wrappers in `app/tools/gitlab_tools.py` using `python-gitlab`.
* [x] **Task 2.3:** Implement `app/agent.py` to configure the Gemini Agent and register the GitLab tools.
* [x] **Task 2.4:** Build team coordination and IDE Agent supervision tools in `app/tools/team_tools.py`.
* [x] **Task 2.5:** Register new tools in `app/tools/__init__.py` and configure Gemini mapping.

### Phase 3: Webhook Server & Memory Persistence
* [x] **Task 3.1:** Implement `app/main.py` FastAPI server, the `/webhook/telegram` endpoint, and simple JSON-based local history persistence.
* [x] **Task 3.2:** Update Dashboard UI in `app/main.py` to reflect Team Group Chat and IDE Agent connectivity status.

### Phase 4: Testing & Packaging
* [x] **Task 4.1:** Write quick setup instructions in `README.md`.
* [x] **Task 4.2:** Run local integration tests and simulate webhook requests.
* [x] **Task 4.3:** Add integration tests for Team/IDE simulation tools and verify.

### Phase 5: MCP & Real-time API Integration
* [x] **Task 5.1:** Implement FastAPI REST endpoints (`/api/agent/proposals`, `/api/agent/logs`) for cloud/workspace IDE Agent.
* [x] **Task 5.2:** Implement instant Telegram webhook command interception for proposal approval/rejection bypass logic.
* [x] **Task 5.3:** Support GitLab MCP Client Adapter routing JSON-RPC payloads to an external GitLab MCP Server based on `USE_MCP_SERVER`.
* [x] **Task 5.4:** Write integration tests in `tests/test_core.py` verifying proposal flow, webhook command intercepts, and MCP routing.

---

## 2. Timeline & Progress Tracking

```mermaid
gantt
    title MVP 1 Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Setup & Core
    Task 1.3 (New Config)    :done, 2026-06-11, 1d
    Task 2.4 & 2.5 (CTO Tools):done, 2026-06-11, 1d
    section Webhook UI
    Task 3.2 (Dashboard update):done, 2026-06-11, 1d
    section Testing
    Task 4.3 (CTO Test suite)  :done, 2026-06-11, 1d
    section MCP & Real-time APIs
    Task 5.1 - 5.4 (MCP & REST):done, 2026-06-11, 1d
```
