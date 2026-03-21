import unittest
from unittest.mock import patch

from app.services import moderation_service


class ModerationFlowTests(unittest.TestCase):
    def test_approve_ad_flow(self) -> None:
        with patch.object(moderation_service.repository, "get_ad", return_value={"title": "Sale", "text": "Big discount"}), \
             patch.object(moderation_service.repository, "update_ad_status", return_value=True) as update_status:
            result = moderation_service.approve_or_reject("ad", 10, "approve")

        update_status.assert_called_once_with(10, "approved")
        self.assertIn("status_text", result)
        self.assertIn("publish_text", result)

    def test_reject_post_flow(self) -> None:
        with patch.object(moderation_service.repository, "get_post", return_value={"text": "Need moderation"}), \
             patch.object(moderation_service.repository, "update_post_status", return_value=True) as update_status:
            result = moderation_service.approve_or_reject("post", 7, "reject")

        update_status.assert_called_once_with(7, "rejected")
        self.assertEqual(result["status_text"], "❌ Пост #7 отклонен.")

    def test_missing_entity_and_unknown_kind(self) -> None:
        with patch.object(moderation_service.repository, "get_ad", return_value=None):
            missing = moderation_service.approve_or_reject("ad", 999, "approve")
        self.assertEqual(missing["error"], "Объявление не найдено.")

        unknown = moderation_service.approve_or_reject("unknown", 1, "approve")
        self.assertEqual(unknown["error"], "Неизвестный тип модерируемого объекта.")


if __name__ == "__main__":
    unittest.main()
