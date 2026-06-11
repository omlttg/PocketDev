import unittest
import sys
import os
from fastapi.testclient import TestClient

# Add project root directory to sys.path for importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
client = TestClient(app)

class TestPocketDevCore(unittest.TestCase):
    def test_imports(self):
        """Verify that all core components can be imported without errors."""
        from app.config import settings
        from app.telegram_bot import markdown_to_telegram_html
        from app.tools import GITLAB_TOOLS
        from app.agent import agent_manager
        
        self.assertEqual(len(GITLAB_TOOLS), 14, "Should detect exactly 14 tools (9 GitLab + 3 Team/IDE wrappers + 2 MVP2 tools).")

    def test_markdown_parser(self):
        """Test that the custom markdown parser yields correct Telegram-compatible HTML tags."""
        from app.telegram_bot import markdown_to_telegram_html
        
        test_markdown = "Hello **bold** and *italic* with `inline code` and [Link](https://gitlab.com)"
        expected_html = (
            "Hello <b>bold</b> and <i>italic</i> with "
            "<code>inline code</code> and <a href=\"https://gitlab.com\">Link</a>"
        )
        
        parsed_html = markdown_to_telegram_html(test_markdown)
        self.assertEqual(parsed_html, expected_html, "Markdown parser translation mismatch.")

    def test_team_tools_simulation(self):
        """Verify the mock behavior of Cloud IDE Agent and Team task tools."""
        import os
        import json
        from unittest.mock import patch
        from app.tools.team_tools import get_ide_agent_status, review_ide_agent_proposal, PROPOSALS_FILE
        
        test_proposals_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_proposals.json")
        
        # Initialize an empty test proposals file
        with open(test_proposals_file, "w", encoding="utf-8") as f:
            json.dump({}, f)
            
        with patch("app.tools.team_tools.PROPOSALS_FILE", test_proposals_file):
            # Test status retrieval when idle
            status = get_ide_agent_status()
            self.assertIn("IDLE", status)
            
            # Seed a test proposal
            with open(test_proposals_file, "w", encoding="utf-8") as f:
                json.dump({
                    "P-TEST": {
                        "id": "P-TEST",
                        "task": "Test Mock Task",
                        "status": "PENDING",
                        "changed_files": ["app/main.py"],
                        "description": "Test proposal description"
                    }
                }, f)
                
            status_with_prop = get_ide_agent_status()
            self.assertIn("P-TEST", status_with_prop)
            self.assertIn("Test Mock Task", status_with_prop)
            
            # Test rejection
            reject_res = review_ide_agent_proposal("P-TEST", "reject", feedback="Needs unit tests")
            self.assertIn("REJECTED", reject_res)
            self.assertIn("Needs unit tests", reject_res)
            
            # Verify status in file updated
            with open(test_proposals_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["P-TEST"]["status"], "REJECTED")
            
        if os.path.exists(test_proposals_file):
            os.remove(test_proposals_file)

    def test_ide_agent_proposals_api(self):
        """Test proposals registration API, status querying, logs posting, and Telegram webhook approvals."""
        import os
        import json
        from unittest.mock import patch, AsyncMock
        from app.config import settings
        
        test_proposals_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_proposals.json")
        with open(test_proposals_file, "w", encoding="utf-8") as f:
            json.dump({}, f)
            
        # Mock Telegram message pusher to avoid hits to Telegram servers
        mock_send_telegram = AsyncMock()
        
        # Override ALLOWED_TELEGRAM_USER_IDS to run webhook
        original_users = settings.ALLOWED_TELEGRAM_USER_IDS
        settings.ALLOWED_TELEGRAM_USER_IDS = "999"
        
        try:
            with patch("app.tools.team_tools.PROPOSALS_FILE", test_proposals_file), \
                 patch("app.main.send_telegram_message", mock_send_telegram):
                 
                # 1. Post a new proposal
                payload = {
                    "proposal_id": "P-API-01",
                    "task": "Register route",
                    "command": "python setup.py",
                    "changed_files": ["app/routes.py"],
                    "description": "Testing proposal flow"
                }
                response = client.post("/api/agent/proposals", json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "pending")
                self.assertEqual(mock_send_telegram.call_count, 1) # Sent push to user 999
                
                # Verify saved state
                with open(test_proposals_file, "r", encoding="utf-8") as f:
                    props = json.load(f)
                self.assertIn("P-API-01", props)
                self.assertEqual(props["P-API-01"]["status"], "PENDING")
                
                # 2. Query proposal status
                response = client.get("/api/agent/proposals/P-API-01")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "PENDING")
                
                # 3. Simulate CTO approving proposal through Webhook
                webhook_payload = {
                    "update_id": 100,
                    "message": {
                        "message_id": 1,
                        "from": {"id": 999, "is_bot": False, "first_name": "CTO"},
                        "chat": {"id": 999, "type": "private"},
                        "text": "Approve P-API-01"
                    }
                }
                webhook_response = client.post(
                    f"/webhook/telegram/{settings.WEBHOOK_SECRET_TOKEN}",
                    json=webhook_payload
                )
                self.assertEqual(webhook_response.status_code, 200)
                
                # Verify state updated in database
                with open(test_proposals_file, "r", encoding="utf-8") as f:
                    props = json.load(f)
                self.assertEqual(props["P-API-01"]["status"], "APPROVED")
                
                # 4. Check status transition via API
                response = client.get("/api/agent/proposals/P-API-01")
                self.assertEqual(response.json()["status"], "APPROVED")
                
                # 5. Post Execution Logs
                log_payload = {
                    "proposal_id": "P-API-01",
                    "log": "Route registered successfully."
                }
                response = client.post("/api/agent/logs", json=log_payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "logged")
        finally:
            settings.ALLOWED_TELEGRAM_USER_IDS = original_users
            if os.path.exists(test_proposals_file):
                os.remove(test_proposals_file)

    def test_agent_builder_tools_webhook(self):
        """Simulate a webhook request from GCP Agent Builder and verify API response formatting."""
        # Patch the Proposals file to avoid modifying user's production DB
        import os
        from unittest.mock import patch
        test_proposals_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_proposals_file.json")
        
        payload = {
            "fulfillmentInfo": {
                "tag": "get_ide_agent_status"
            },
            "sessionInfo": {
                "parameters": {}
            }
        }
        with patch("app.tools.team_tools.PROPOSALS_FILE", test_proposals_file):
            response = client.post("/webhook/tools", json=payload)
            self.assertEqual(response.status_code, 200, "Webhook endpoint failed to respond with 200 OK.")
            
            data = response.json()
            messages = data.get("fulfillmentResponse", {}).get("messages", [])
            self.assertTrue(len(messages) > 0, "Response must contain fulfillmentResponse messages.")
            
            text_content = messages[0].get("text", {}).get("text", [])[0]
            self.assertIn("Cloud IDE Agent Status", text_content, "Webhook output failed to run target tool.")
            
        if os.path.exists(test_proposals_file):
            os.remove(test_proposals_file)

    def test_analyze_codebase_architecture_mock(self):
        """Test code architecture analysis with mocked Gemini API."""
        from unittest.mock import patch, MagicMock
        from app.tools.architecture_tools import analyze_codebase_architecture
        from app.config import settings
        
        original_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = "test_key"
        
        try:
            with patch("google.generativeai.GenerativeModel") as MockModel:
                mock_model_instance = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Mocked Architecture Analysis Report"
                mock_model_instance.generate_content.return_value = mock_response
                MockModel.return_value = mock_model_instance
                
                # Test call for a specific file path
                result = analyze_codebase_architecture("app/config.py")
                self.assertEqual(result, "Mocked Architecture Analysis Report")
                mock_model_instance.generate_content.assert_called_once()
        finally:
            settings.GEMINI_API_KEY = original_key

    def test_decompose_task_into_subissues_mock(self):
        """Test task decomposition algorithm with mocked Gemini API and mocked GitLab calls."""
        import json
        from unittest.mock import patch, MagicMock
        from app.tools.decomposition_tools import decompose_task_into_subissues
        from app.config import settings
        
        original_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = "test_key"
        
        try:
            with patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("app.tools.decomposition_tools.create_gitlab_issue") as mock_create_issue, \
                 patch("app.tools.decomposition_tools.comment_on_issue") as mock_comment_issue, \
                 patch("app.tools.decomposition_tools.get_project") as mock_get_project:
                
                # Mock generative model returns structured json string
                mock_model_instance = MagicMock()
                mock_response = MagicMock()
                mock_response.text = json.dumps([
                    {
                        "title": "Subtask 1: Setup Auth",
                        "description": "Configure OAuth scopes and keys",
                        "labels": "subtask,auth"
                    },
                    {
                        "title": "Subtask 2: Implement Buttons",
                        "description": "Add Google/Facebook login buttons",
                        "labels": "subtask,frontend"
                    }
                ])
                mock_model_instance.generate_content.return_value = mock_response
                MockModel.return_value = mock_model_instance
                
                # Mock GitLab Issue creations
                mock_create_issue.side_effect = [
                    "Success: Created Issue #100 - Parent Task",
                    "Success: Created Issue #101 - Subtask 1\nLink: https://gitlab.com/test/101",
                    "Success: Created Issue #102 - Subtask 2\nLink: https://gitlab.com/test/102"
                ]
                
                mock_comment_issue.return_value = "Success: Commented"
                
                # Mock GitLab Project and Issue objects
                mock_project = MagicMock()
                mock_issue = MagicMock()
                mock_issue.web_url = "https://gitlab.com/test/100"
                mock_project.issues.get.return_value = mock_issue
                mock_get_project.return_value = mock_project
                
                result = decompose_task_into_subissues(
                    task_title="OAuth2 Integration",
                    task_description="Implement Google and Facebook Login"
                )
                
                self.assertIn("OAuth2 Integration", result)
                self.assertIn("Issue #100", result)
                self.assertIn("Subtask 1: Setup Auth", result)
                self.assertIn("Subtask 2: Implement Buttons", result)
                self.assertEqual(mock_create_issue.call_count, 3)  # 1 parent + 2 subtasks
                mock_comment_issue.assert_called_once()
        finally:
            settings.GEMINI_API_KEY = original_key

    def test_gitlab_mcp_client_routing(self):
        """Verify the MCP Client Adapter routes tool calls to MCP server or falls back to direct SDK."""
        from unittest.mock import patch, MagicMock
        from app.tools.gitlab_tools import create_gitlab_issue
        from app.config import settings
        
        original_mcp_flag = settings.USE_MCP_SERVER
        original_mcp_url = settings.MCP_SERVER_URL
        
        try:
            # Test Case 1: Route via MCP Server when enabled
            settings.USE_MCP_SERVER = True
            settings.MCP_SERVER_URL = "http://mcp-server-test"
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Success: Routed via GitLab MCP Server - Created Issue #999"
                        }
                    ]
                },
                "id": 1
            }
            
            with patch("httpx.post", return_value=mock_response) as mock_post:
                result = create_gitlab_issue(title="MCP Issue", description="Testing MCP payload")
                self.assertEqual(result, "Success: Routed via GitLab MCP Server - Created Issue #999")
                mock_post.assert_called_once()
                
                called_args, called_kwargs = mock_post.call_args
                self.assertEqual(called_args[0], "http://mcp-server-test/v1/tools/call")
                payload = called_kwargs["json"]
                self.assertEqual(payload["method"], "tools/call")
                self.assertEqual(payload["params"]["name"], "create_issue")
                self.assertEqual(payload["params"]["arguments"]["title"], "MCP Issue")
                
            # Test Case 2: Fallback to direct SDK when disabled
            settings.USE_MCP_SERVER = False
            with patch("app.tools.gitlab_tools.get_project") as mock_get_project:
                mock_project_instance = MagicMock()
                mock_issue = MagicMock()
                mock_issue.iid = 555
                mock_issue.title = "Direct SDK Issue"
                mock_issue.web_url = "https://gitlab.com/test/555"
                mock_project_instance.issues.create.return_value = mock_issue
                mock_get_project.return_value = mock_project_instance
                
                result_direct = create_gitlab_issue(title="Direct SDK Issue")
                self.assertIn("Created Issue #555", result_direct)
                self.assertIn("on GitLab", result_direct)
                mock_get_project.assert_called_once()
        finally:
            settings.USE_MCP_SERVER = original_mcp_flag
            settings.MCP_SERVER_URL = original_mcp_url

if __name__ == "__main__":
    unittest.main()
