# Changelog

All notable changes to the **PocketDev** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-mvp1] - 2026-06-11

This is the initial release of PocketDev for the **"Building Agents for Real-World Challenges" Hackathon (GitLab MCP Track)**.

### Added
*   **FastAPI Webhook Server:** Set up a production-ready async web server to handle inbound Telegram events.
*   **High-fidelity Landing Page:** Integrated a Glassmorphic dark-themed HTML5 dashboard to view backend setup status.
*   **Gemini Agent Core:** Wired up the `gemini-1.5-flash` model with customized English System Instructions.
*   **GitLab Tools Suite (12 Tools):**
    *   *Issues:* Create issues, list issues, and add comments.
    *   *Repository:* List branches, read file code contents, and open Merge Requests.
    *   *CI/CD Pipelines:* List pipeline statuses, retry failed pipelines, and accept/merge MRs.
    *   *Team Delegation (New):* Automatically create GitLab issues and tag developers in the Telegram Group Chat to assign tasks.
    *   **IDE Agent Supervision (Updated):** Rebuilt static mock tools into a real-time REST API integration. Implemented `POST /api/agent/proposals`, `GET /api/agent/proposals/{proposal_id}`, and `POST /api/agent/logs` for live communication, and intercepted Telegram Approve/Reject commands in webhook for real-time mobile supervision.
*   **Telegram Helper & Parser:** Created a robust async messaging handler featuring a custom Markdown-to-HTML parser compatible with Telegram formatting limits.
*   **Local Session Memory:** Developed a lightweight JSON-backed local storage system to preserve user chat contexts across server restarts.
*   **GitLab CI/CD Integration:** Configured `.gitlab-ci.yml` pipeline with automated unit testing for python code.
*   **Open Source Packaging:** Added official MIT license, `CONTRIBUTING.md` guide, and comprehensive English documentation.
