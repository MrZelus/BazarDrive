import re
import unittest
from pathlib import Path


class FeedImageRenderingRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")
        map_match = re.search(r"function mapApiPost\(item\) \{([\s\S]+?)\n    \}\n\n    function mapApiComment", self.script)
        self.assertIsNotNone(map_match, "mapApiPost block was not found in web/js/feed.js")
        self.map_block = map_match.group(1)

        render_match = re.search(r"function renderFeed\(\) \{([\s\S]+?)\n    \}\n\n    async function loadPosts", self.script)
        self.assertIsNotNone(render_match, "renderFeed block was not found in web/js/feed.js")
        self.render_block = render_match.group(1)

    def test_map_api_post_sanitizes_legacy_none_and_null_image_values(self) -> None:
        self.assertIn("function normalizeFeedMediaUrl(rawUrl) {", self.script)
        self.assertIn("if (value.startsWith('/uploads/feed/')) {", self.script)
        self.assertIn("return `${FEED_API_BASE}${value}`;", self.script)
        self.assertIn("url: normalizeFeedMediaUrl(entry?.url),", self.map_block)
        self.assertIn("const safeLegacyImage = (", self.map_block)
        self.assertIn("normalizedLegacyImage !== 'none'", self.map_block)
        self.assertIn("normalizedLegacyImage !== 'null'", self.map_block)
        self.assertIn(") ? normalizeFeedMediaUrl(legacyImage) : '';", self.map_block)
        self.assertIn("image: safeLegacyImage", self.map_block)

    def test_render_feed_uses_object_contain_for_post_images(self) -> None:
        self.assertIn("image.className = 'h-auto w-full max-h-[420px] snap-center rounded-xl object-contain';", self.render_block)
        self.assertIn("image.className = 'mb-3 h-auto w-full max-h-[420px] rounded-xl object-contain';", self.render_block)
        self.assertNotIn("image.className = 'max-h-[420px] min-w-full snap-center rounded-xl object-cover';", self.render_block)
        self.assertNotIn("image.className = 'mb-3 max-h-[420px] w-full rounded-xl object-cover';", self.render_block)


if __name__ == "__main__":
    unittest.main()
