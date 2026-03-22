import unittest

from app.services.feed_service import FeedService


class FeedAPIPublishSmokeTests(unittest.TestCase):
    def test_valid_post_passes_publication_rules(self) -> None:
        FeedService.validate_publication_rules("Ищу попутчика до аэропорта, выезд в 08:30.")

    def test_invalid_post_with_prohibited_topic_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "запрещ"):
            FeedService.validate_publication_rules("Казино бонусы и ставки на спорт каждый день")

    def test_spam_like_repeated_tokens_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "спам"):
            FeedService.validate_publication_rules("скидка скидка скидка скидка скидка очень выгодно")


if __name__ == "__main__":
    unittest.main()
