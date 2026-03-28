import re
import unittest
from pathlib import Path


class MainTabsA11yRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        self.script = Path('public/web/js/feed.js').read_text(encoding='utf-8')

    def test_bottom_nav_uses_aria_tabs_pattern(self) -> None:
        self.assertIn('role="tablist" aria-label="Основное меню"', self.html)
        self.assertIn('id="main-tab-btn-feed" data-tab="feed" role="tab"', self.html)
        self.assertIn('id="main-tab-btn-rules" data-tab="rules" role="tab"', self.html)
        self.assertIn('id="main-tab-btn-profile" data-tab="profile" role="tab"', self.html)
        self.assertIn('aria-controls="screen-feed"', self.html)
        self.assertIn('aria-controls="screen-rules"', self.html)
        self.assertIn('aria-controls="screen-profile"', self.html)

    def test_panels_have_tabpanel_linking_and_hidden_state(self) -> None:
        self.assertIn('id="screen-feed" class="screen active animate-fadeInUp" role="tabpanel" aria-labelledby="main-tab-btn-feed"', self.html)
        self.assertIn('id="screen-rules" class="screen" role="tabpanel" aria-labelledby="main-tab-btn-rules" hidden aria-hidden="true" inert', self.html)
        self.assertIn('id="screen-profile" class="screen" role="tabpanel" aria-labelledby="main-tab-btn-profile" hidden aria-hidden="true" inert', self.html)

    def test_main_tabs_have_keyboard_navigation(self) -> None:
        self.assertIn('function handleMainTabsKeydown(event)', self.script)
        self.assertIn("const navigationKeys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];", self.script)
        self.assertIn("btn.addEventListener('keydown', handleMainTabsKeydown);", self.script)
        self.assertRegex(
            self.script,
            re.compile(r"function setActiveScreen\(tab\)[\s\S]+btn\.setAttribute\('aria-selected', String\(isActive\)\);[\s\S]+btn\.tabIndex = isActive \? 0 : -1;", re.MULTILINE),
        )

    def test_rules_search_has_mobile_a11y_hint_and_live_status(self) -> None:
        self.assertIn('id="docsSearchHint"', self.html)
        self.assertIn('id="docsSearchStatus"', self.html)
        self.assertIn('aria-describedby="docsSearchHint docsSearchStatus"', self.html)
        self.assertIn('role="status" aria-live="polite"', self.html)
        self.assertIn("const docsSearchStatus = document.getElementById('docsSearchStatus');", self.script)
        self.assertIn("const shouldFilter = normalized.length >= 2;", self.script)
        self.assertIn("docsSearchStatus.textContent = `Показаны все материалы: ${docs.length}.`;", self.script)


if __name__ == '__main__':
    unittest.main()
