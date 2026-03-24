import subprocess
import sys
import tempfile
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

    def test_dry_run_writes_manifest_without_playwright(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "capture-manifest.json"
            result = self.run_script("--browsers", "chrome", "--dry-run", "--manifest", str(manifest_path))

            self.assertEqual(result.returncode, 0)
            self.assertIn("PLAN:", result.stdout)
            self.assertIn("Manifest:", result.stdout)
            self.assertTrue(manifest_path.exists())
            manifest_text = manifest_path.read_text(encoding="utf-8")
            self.assertIn('"dry_run": true', manifest_text)
            self.assertIn('"browser": "chrome"', manifest_text)

    def test_rejects_unsupported_tab_in_preflight(self) -> None:
        result = self.run_script("--dry-run", "--tabs", "feed,unknown")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Unsupported tab: unknown", result.stdout)

    def test_dry_run_filters_plan_by_tabs_and_viewports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "capture-manifest.json"
            result = self.run_script(
                "--browsers",
                "chrome",
                "--tabs",
                "profile",
                "--viewports",
                "mobile",
                "--dry-run",
                "--manifest",
                str(manifest_path),
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("profile-mobile-chrome-after.png", result.stdout)
            self.assertNotIn("feed-mobile-chrome-after.png", result.stdout)
            self.assertNotIn("profile-desktop-chrome-after.png", result.stdout)
            manifest_text = manifest_path.read_text(encoding="utf-8")
            self.assertIn('"tab": "profile"', manifest_text)
            self.assertIn('"viewport": "mobile"', manifest_text)
            self.assertNotIn('"tab": "feed"', manifest_text)

    def test_dry_run_writes_markdown_matrix_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "evidence-matrix.md"
            result = self.run_script(
                "--dry-run",
                "--browsers",
                "chrome",
                "--tabs",
                "feed,profile",
                "--viewports",
                "mobile",
                "--report-md",
                str(report_path),
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Markdown report:", result.stdout)
            self.assertTrue(report_path.exists())
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("| Tab | desktop/chrome | desktop/edge | mobile/chrome | mobile/edge |", report_text)
            self.assertIn(
                "| Лента | - | - | [artifacts/121/feed-mobile-chrome-after.png](artifacts/121/feed-mobile-chrome-after.png) | - |",
                report_text,
            )
            self.assertIn(
                "| Профиль | - | - | [artifacts/121/profile-mobile-chrome-after.png](artifacts/121/profile-mobile-chrome-after.png) | - |",
                report_text,
            )

    def test_dry_run_markdown_matrix_can_include_file_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "evidence-matrix.md"
            result = self.run_script(
                "--dry-run",
                "--browsers",
                "chrome",
                "--tabs",
                "feed",
                "--viewports",
                "mobile",
                "--out",
                tmpdir,
                "--report-md",
                str(report_path),
                "--report-md-check-files",
            )

            self.assertEqual(result.returncode, 0)
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("❌", report_text)

    def test_dry_run_fail_on_missing_files_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_script(
                "--dry-run",
                "--browsers",
                "chrome",
                "--tabs",
                "feed",
                "--viewports",
                "mobile",
                "--out",
                tmpdir,
                "--fail-on-missing-files",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("ERROR: Missing screenshot files: 1", result.stdout)
            self.assertIn("MISSING:", result.stdout)

    def test_dry_run_fail_on_missing_files_passes_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = Path(tmpdir) / "feed-mobile-chrome-after.png"
            screenshot_path.touch()
            result = self.run_script(
                "--dry-run",
                "--browsers",
                "chrome",
                "--tabs",
                "feed",
                "--viewports",
                "mobile",
                "--out",
                tmpdir,
                "--fail-on-missing-files",
            )

            self.assertEqual(result.returncode, 0)
            self.assertNotIn("ERROR: Missing screenshot files", result.stdout)


if __name__ == "__main__":
    unittest.main()
