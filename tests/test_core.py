import unittest
import sys
import os

# Add project root directory to sys.path for importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPocketDevCore(unittest.TestCase):
    def test_imports(self):
        """Verify that all core components can be imported without errors."""
        from app.config import settings
        from app.telegram_bot import markdown_to_telegram_html
        from app.tools import GITLAB_TOOLS
        from app.agent import agent_manager
        from app.main import app
        
        self.assertEqual(len(GITLAB_TOOLS), 9, "Should detect exactly 9 GitLab tools wrapper.")
        self.assertIsNotNone(app, "FastAPI app instance should not be None.")

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

if __name__ == "__main__":
    unittest.main()
