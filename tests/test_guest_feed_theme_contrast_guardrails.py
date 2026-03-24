import re
import unittest
from pathlib import Path


class GuestFeedThemeContrastGuardrails(unittest.TestCase):
    def setUp(self) -> None:
        self.tailwind_config = Path("web/js/tailwind-config.js").read_text(encoding="utf-8")
        self.feed_css = Path("web/css/feed.css").read_text(encoding="utf-8")

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.strip().lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    @staticmethod
    def _channel_to_linear(channel: int) -> float:
        srgb = channel / 255
        if srgb <= 0.03928:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    @classmethod
    def _relative_luminance(cls, hex_color: str) -> float:
        r, g, b = cls._hex_to_rgb(hex_color)
        rl = cls._channel_to_linear(r)
        gl = cls._channel_to_linear(g)
        bl = cls._channel_to_linear(b)
        return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl

    @classmethod
    def _contrast_ratio(cls, fg: str, bg: str) -> float:
        lighter = max(cls._relative_luminance(fg), cls._relative_luminance(bg))
        darker = min(cls._relative_luminance(fg), cls._relative_luminance(bg))
        return (lighter + 0.05) / (darker + 0.05)

    def _tailwind_color(self, name: str) -> str:
        pattern = re.compile(rf"{re.escape(name)}:\s*'(?P<hex>#[0-9a-fA-F]{{6}})'", re.MULTILINE)
        match = pattern.search(self.tailwind_config)
        self.assertIsNotNone(match, msg=f"Tailwind color token `{name}` not found")
        return match.group("hex")

    def _css_rgb_var(self, name: str) -> tuple[int, int, int]:
        pattern = re.compile(rf"--{re.escape(name)}:\s*(\d+)\s+(\d+)\s+(\d+);", re.MULTILINE)
        match = pattern.search(self.feed_css)
        self.assertIsNotNone(match, msg=f"CSS variable `--{name}` not found")
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    def test_theme_tokens_keep_accessible_text_contrast(self) -> None:
        bg = self._tailwind_color("bg")
        panel = self._tailwind_color("panel")
        text = self._tailwind_color("text")
        text_soft = self._tailwind_color("textSoft")
        accent = self._tailwind_color("accent")

        self.assertGreaterEqual(self._contrast_ratio(text, bg), 7.0)
        self.assertGreaterEqual(self._contrast_ratio(text, panel), 7.0)
        self.assertGreaterEqual(self._contrast_ratio(text_soft, bg), 4.5)
        self.assertGreaterEqual(self._contrast_ratio(text_soft, panel), 4.5)
        self.assertGreaterEqual(self._contrast_ratio(accent, bg), 4.5)

    def test_surfaces_keep_minimum_visual_separation(self) -> None:
        bg = self._tailwind_color("bg")
        panel = self._tailwind_color("panel")
        panel_soft = self._tailwind_color("panelSoft")

        self.assertGreaterEqual(self._contrast_ratio(bg, panel), 1.3)
        self.assertGreaterEqual(self._contrast_ratio(bg, panel_soft), 1.5)

    def test_css_variables_are_in_sync_with_tailwind_tokens(self) -> None:
        mapping = {
            "feed-bg-rgb": "bg",
            "feed-panel-rgb": "panel",
            "feed-panel-soft-rgb": "panelSoft",
            "feed-accent-rgb": "accent",
            "feed-text-rgb": "text",
            "feed-text-soft-rgb": "textSoft",
            "feed-success-rgb": "success",
            "feed-warning-rgb": "warning",
        }

        for css_var, token in mapping.items():
            expected_rgb = self._hex_to_rgb(self._tailwind_color(token))
            actual_rgb = self._css_rgb_var(css_var)
            self.assertEqual(
                actual_rgb,
                expected_rgb,
                msg=f"Expected --{css_var}: {' '.join(map(str, expected_rgb))} from `{token}` token",
            )


if __name__ == "__main__":
    unittest.main()
