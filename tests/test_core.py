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
        
        self.assertEqual(len(GITLAB_TOOLS), 12, "Should detect exactly 12 tools (9 GitLab + 3 Team/IDE wrappers).")

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
        from app.tools.team_tools import get_ide_agent_status, review_ide_agent_proposal
        
        # Test status retrieval
        status = get_ide_agent_status()
        self.assertIn("Cloud IDE Agent Status", status)
        self.assertIn("P-01", status)
        
        # Test rejection proposal
        reject_res = review_ide_agent_proposal("P-01", "reject", feedback="Add more unit tests")
        self.assertIn("REJECTED", reject_res)
        self.assertIn("Add more unit tests", reject_res)
        
        # Test invalid proposal
        invalid_res = review_ide_agent_proposal("INVALID", "approve")
        self.assertIn("not found", invalid_res)

    def test_agent_builder_tools_webhook(self):
        """Simulate a webhook request from GCP Agent Builder and verify API response formatting."""
        payload = {
            "fulfillmentInfo": {
                "tag": "get_ide_agent_status"
            },
            "sessionInfo": {
                "parameters": {}
            }
        }
        response = client.post("/webhook/tools", json=payload)
        self.assertEqual(response.status_code, 200, "Webhook endpoint failed to respond with 200 OK.")
        
        data = response.json()
        messages = data.get("fulfillmentResponse", {}).get("messages", [])
        self.assertTrue(len(messages) > 0, "Response must contain fulfillmentResponse messages.")
        
        text_content = messages[0].get("text", {}).get("text", [])[0]
        self.assertIn("Cloud IDE Agent Status", text_content, "Webhook output failed to run target tool.")

if __name__ == "__main__":
    unittest.main()
