import re
import unittest
from pathlib import Path


class FeedImageRenderingRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")
        match = re.search(r"function mapApiPost\(item\) \{([\s\S]+?)\n    \}\n\n    function mapApiComment", self.script)
        self.assertIsNotNone(match, "mapApiPost block was not found in web/js/feed.js")
        self.block = match.group(1)

    def test_map_api_post_sanitizes_legacy_none_and_null_image_values(self) -> None:
        self.assertIn("const safeLegacyImage = (", self.block)
        self.assertIn("normalizedLegacyImage !== 'none'", self.block)
        self.assertIn("normalizedLegacyImage !== 'null'", self.block)
        self.assertIn("image: safeLegacyImage", self.block)


if __name__ == "__main__":
    unittest.main()
