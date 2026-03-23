import re
import unittest
from pathlib import Path


class FeedXssRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")

    def _render_feed_block(self) -> str:
        match = re.search(r"function renderFeed\(\) \{([\s\S]+?)\n    \}\n\n    async function loadPosts", self.script)
        self.assertIsNotNone(match, "renderFeed block was not found in web/js/feed.js")
        return match.group(1)

    def test_render_feed_uses_text_nodes_instead_of_html_injection(self) -> None:
        block = self._render_feed_block()
        self.assertIn("author.textContent = String(post.author || 'Гость');", block)
        self.assertIn("body.textContent = String(post.text || '');", block)
        self.assertNotIn("innerHTML", block, "renderFeed must not inject raw HTML")

    def test_render_feed_keeps_image_src_assignment_explicit(self) -> None:
        block = self._render_feed_block()
        self.assertIn("if (post.image) {", block)
        self.assertIn("image.src = String(post.image);", block)


if __name__ == "__main__":
    unittest.main()
