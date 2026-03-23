import unittest
from pathlib import Path


class FeedInfiniteScrollTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")

    def test_infinite_scroll_uses_intersection_observer(self) -> None:
        self.assertIn("function ensureFeedInfiniteScroll()", self.script)
        self.assertIn("new IntersectionObserver", self.script)
        self.assertIn("loadPosts();", self.script)

    def test_feed_deduplicates_posts_by_id(self) -> None:
        self.assertIn("const postIds = new Set();", self.script)
        self.assertIn("if (postIds.has(postId)) return false;", self.script)
        self.assertIn("postIds.add(postId);", self.script)

    def test_feed_stops_loading_when_has_more_false(self) -> None:
        self.assertIn("feedHasMore = Boolean(payload.has_more) && Boolean(feedNextCursor);", self.script)
        self.assertIn("if (!feedHasMore) {", self.script)
        self.assertIn("stopFeedInfiniteScroll();", self.script)

    def test_feed_shows_loading_skeleton_and_error_without_alert(self) -> None:
        self.assertIn("function setFeedLoadingSkeleton(isVisible)", self.script)
        self.assertIn("animate-pulse", self.script)
        self.assertIn("function setFeedError(message = '')", self.script)
        self.assertNotIn("alert(", self.script)


if __name__ == "__main__":
    unittest.main()
