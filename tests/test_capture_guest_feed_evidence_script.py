import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path("scripts/capture_guest_feed_evidence.py")


class CaptureGuestFeedEvidenceScriptTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_rejects_unsupported_browser_before_playwright_import(self) -> None:
        result = self.run_script("--browsers", "safari")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Unsupported browser: safari", result.stdout)
        self.assertNotIn("Playwright is not installed", result.stdout)

    def test_reports_missing_playwright_with_actionable_message(self) -> None:
        result = self.run_script("--browsers", "chrome")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Playwright is not installed", result.stdout)
        self.assertIn("python -m playwright install chromium msedge", result.stdout)


if __name__ == "__main__":
    unittest.main()
