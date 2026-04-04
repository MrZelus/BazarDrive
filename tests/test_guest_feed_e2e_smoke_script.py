import subprocess
import sys
import unittest
import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/run_guest_feed_e2e_smoke.py")


class GuestFeedE2ESmokeScriptTests(unittest.TestCase):
    @staticmethod
    def load_script_module():
        spec = importlib.util.spec_from_file_location("guest_feed_e2e_smoke_script", SCRIPT)
        if spec is None or spec.loader is None:
            raise AssertionError("Unable to load smoke script module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_dry_run_prints_plan_with_required_steps(self) -> None:
        result = self.run_script("--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertIn("PLAN:", result.stdout)
        self.assertIn("fill_profile", result.stdout)
        self.assertIn("publish_post", result.stdout)
        self.assertIn("search_rules", result.stdout)
        self.assertIn("comment_and_react", result.stdout)

    def test_dry_run_respects_custom_ports_and_host(self) -> None:
        result = self.run_script("--dry-run", "--host", "0.0.0.0", "--static-port", "8111", "--api-port", "8112")

        self.assertEqual(result.returncode, 0)
        self.assertIn('"static_base": "http://0.0.0.0:8111"', result.stdout)
        self.assertIn('"api_base": "http://0.0.0.0:8112"', result.stdout)

    def test_reports_missing_playwright_dependency_with_actionable_message(self) -> None:
        result = self.run_script("--no-start-servers")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Playwright is not installed", result.stdout)
        self.assertIn("python -m playwright install chromium", result.stdout)

    def test_build_api_process_env_honors_host_and_api_port(self) -> None:
        module = self.load_script_module()
        config = module.SmokeConfig(
            static_port=8000,
            api_port=9123,
            host="0.0.0.0",
            timeout_seconds=10.0,
            no_start_servers=False,
            dry_run=True,
            post_text="x",
            rules_query="y",
        )
        env = module.build_api_process_env(config)

        self.assertEqual(env["FEED_API_HOST"], "0.0.0.0")
        self.assertEqual(env["FEED_API_PORT"], "9123")


if __name__ == "__main__":
    unittest.main()
