import re
import unittest
from pathlib import Path


class DriverStatusThemeRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path('public/web/js/feed.js').read_text(encoding='utf-8')

    def test_status_theme_map_contains_ui_kit_and_driver_profile_statuses(self) -> None:
        expected_keys = [
            'approved',
            'checking',
            'rejected',
            'expired',
            'expiring_soon',
            'ready',
            'blocked',
            'online',
            'busy',
            'offline',
            'pending_verification',
        ]
        for key in expected_keys:
            self.assertRegex(self.script, re.compile(rf"{key}:\s*\{{\s*tone:"))

    def test_unified_renderers_are_used_for_key_profile_status_nodes(self) -> None:
        self.assertIn('function renderStatusChip(element, status, options = {})', self.script)
        self.assertIn('function renderBanner(element, message = \'\', options = {})', self.script)
        self.assertIn('function renderProgressBlock(element, options = {})', self.script)
        self.assertIn('renderStatusChip(driverComplianceStatusBadge, statusKey', self.script)
        self.assertIn('renderStatusChip(profileVerificationBadge, verificationState', self.script)
        self.assertIn('renderBanner(', self.script)

    def test_progress_block_renderer_is_used_for_required_fields_chips(self) -> None:
        self.assertIn("renderProgressBlock(item, { status: 'ready' });", self.script)
        self.assertIn("renderProgressBlock(item, { status: 'expiring_soon' });", self.script)
        self.assertIn("renderProgressBlock(item, { status: 'offline' });", self.script)


if __name__ == '__main__':
    unittest.main()
