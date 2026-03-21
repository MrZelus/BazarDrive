import os
import tempfile
import unittest

from app.db import repository


class GuestFeedRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.previous_db_path = os.environ.get("BAZAR_DB_PATH")
        os.environ["BAZAR_DB_PATH"] = self.temp_db.name
        repository.init_db()

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("BAZAR_DB_PATH", None)
        else:
            os.environ["BAZAR_DB_PATH"] = self.previous_db_path
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_create_update_list_count_posts_and_profile_upsert(self) -> None:
        profile = repository.upsert_guest_profile(
            profile_id="guest-0001",
            display_name="Ivan Guest",
            email="ivan@example.com",
            about="Первый профиль",
        )
        self.assertEqual(profile["id"], "guest-0001")
        self.assertEqual(profile["display_name"], "Ivan Guest")

        created = repository.create_guest_feed_post(
            author="Ivan Guest",
            text="Всем привет, это мой первый пост",
            image_url="https://example.com/image.jpg",
            guest_profile_id="guest-0001",
        )
        self.assertEqual(created["author"], "Ivan Guest")
        self.assertEqual(created["guest_profile_id"], "guest-0001")

        updated = repository.update_guest_feed_post(
            post_id=created["id"],
            author="Ivan Updated",
            text="Обновленный текст публикации",
            image_url="https://example.com/new.jpg",
            guest_profile_id="guest-0001",
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["author"], "Ivan Updated")
        self.assertEqual(updated["text"], "Обновленный текст публикации")

        profile_updated = repository.upsert_guest_profile(
            profile_id="guest-0001",
            display_name="Ivan Guest Updated",
            email="ivan.updated@example.com",
            phone="+1234567",
            about="Обновленный профиль",
            is_verified=True,
        )
        self.assertEqual(profile_updated["display_name"], "Ivan Guest Updated")
        self.assertEqual(profile_updated["is_verified"], 1)

        fetched_profile = repository.get_guest_profile("guest-0001")
        self.assertIsNotNone(fetched_profile)
        self.assertEqual(fetched_profile["email"], "ivan.updated@example.com")

        items = repository.list_guest_feed_posts(limit=10, offset=0)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], created["id"])

        total = repository.count_guest_feed_posts()
        self.assertEqual(total, 1)


if __name__ == "__main__":
    unittest.main()
