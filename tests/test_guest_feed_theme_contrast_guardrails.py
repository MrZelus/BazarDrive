import re
import unittest
from pathlib import Path


class GuestFeedThemeContrastGuardrails(unittest.TestCase):
    def setUp(self) -> None:
        self.feed_css = Path("public/web/css/feed.css").read_text(encoding="utf-8")

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

    def _css_rgb_var(self, name: str, selector: str = r":root") -> tuple[int, int, int]:
        block_pattern = re.compile(rf"{selector}\s*\{{(?P<body>.*?)\}}", re.DOTALL)
        block_match = block_pattern.search(self.feed_css)
        self.assertIsNotNone(block_match, msg=f"CSS selector `{selector}` not found")
        block_body = block_match.group("body")
        pattern = re.compile(rf"--{re.escape(name)}:\s*(\d+)\s+(\d+)\s+(\d+);", re.MULTILINE)
        match = pattern.search(block_body)
        self.assertIsNotNone(match, msg=f"CSS variable `--{name}` not found")
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    def _theme_hex(self, css_selector: str, css_var: str) -> str:
        return self._rgb_to_hex(self._css_rgb_var(css_var, css_selector))

    def _assert_theme_contrast(self, css_selector: str) -> None:
        bg = self._theme_hex(css_selector, "feed-bg-rgb")
        panel = self._theme_hex(css_selector, "feed-panel-rgb")
        text = self._theme_hex(css_selector, "feed-text-rgb")
        text_soft = self._theme_hex(css_selector, "feed-text-soft-rgb")
        accent = self._theme_hex(css_selector, "feed-accent-rgb")

        self.assertGreaterEqual(self._contrast_ratio(text, bg), 7.0)
        self.assertGreaterEqual(self._contrast_ratio(text, panel), 7.0)
        self.assertGreaterEqual(self._contrast_ratio(text_soft, bg), 4.5)
        self.assertGreaterEqual(self._contrast_ratio(text_soft, panel), 4.5)
        self.assertGreaterEqual(self._contrast_ratio(accent, bg), 4.5)

    def _assert_theme_surface_separation(
        self,
        css_selector: str,
        min_bg_panel: float = 1.3,
        min_bg_panel_soft: float = 1.5,
    ) -> None:
        bg = self._theme_hex(css_selector, "feed-bg-rgb")
        panel = self._theme_hex(css_selector, "feed-panel-rgb")
        panel_soft = self._theme_hex(css_selector, "feed-panel-soft-rgb")

        self.assertGreaterEqual(self._contrast_ratio(bg, panel), min_bg_panel)
        self.assertGreaterEqual(self._contrast_ratio(bg, panel_soft), min_bg_panel_soft)

    def test_dark_theme_tokens_keep_accessible_text_contrast(self) -> None:
        self._assert_theme_contrast(r":root")

    def test_light_theme_tokens_keep_accessible_text_contrast(self) -> None:
        self._assert_theme_contrast(r":root\[data-theme='light'\]")

    def test_dark_theme_surfaces_keep_minimum_visual_separation(self) -> None:
        self._assert_theme_surface_separation(r":root", min_bg_panel=1.1, min_bg_panel_soft=1.25)

    def test_light_theme_surfaces_keep_minimum_visual_separation(self) -> None:
        self._assert_theme_surface_separation(r":root\[data-theme='light'\]")


if __name__ == "__main__":
    unittest.main()
