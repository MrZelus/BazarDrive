import os
import sqlite3
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

        created_doc = repository.create_driver_document(
            profile_id="driver-main",
            type="passport",
            number="4010 123456",
            valid_until="2030-01-01",
            status="uploaded",
        )
        self.assertEqual(created_doc["type"], "passport")

        updated_doc = repository.update_driver_document(
            doc_id=created_doc["id"],
            type="passport",
            number="4010 999999",
            valid_until="2031-01-01",
            status="approved",
        )
        self.assertIsNotNone(updated_doc)
        self.assertEqual(updated_doc["number"], "4010 999999")

        listed_docs = repository.list_driver_documents(profile_id="driver-main")
        self.assertEqual(len(listed_docs), 1)
        self.assertEqual(listed_docs[0]["id"], created_doc["id"])

        deleted = repository.delete_driver_document(created_doc["id"])
        self.assertTrue(deleted)
        self.assertEqual(repository.list_driver_documents(profile_id="driver-main"), [])

    def test_guest_feed_comments_repository_crud_and_cascade(self) -> None:
        created_post = repository.create_guest_feed_post(
            author="Ivan Guest",
            text="Пост для проверки комментариев",
            guest_profile_id="guest-0001",
        )
        post_id = created_post["id"]

        created_comment = repository.create_guest_feed_comment(
            post_id=post_id,
            guest_profile_id="guest-0001",
            author="Ivan Guest",
            text="Первый комментарий",
        )
        self.assertEqual(created_comment["post_id"], post_id)
        comment_id = created_comment["id"]

        fetched = repository.get_guest_feed_comment(comment_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["text"], "Первый комментарий")

        listed = repository.list_guest_feed_comments(post_id=post_id, limit=50, offset=0)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], comment_id)

        updated = repository.update_guest_feed_comment(comment_id=comment_id, text="Обновлённый комментарий")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["text"], "Обновлённый комментарий")

        deleted = repository.delete_guest_feed_comment(comment_id)
        self.assertTrue(deleted)
        self.assertIsNone(repository.get_guest_feed_comment(comment_id))

        comment_for_cascade = repository.create_guest_feed_comment(
            post_id=post_id,
            guest_profile_id="guest-0001",
            author="Ivan Guest",
            text="Будет удалён каскадом",
        )
        cascade_comment_id = comment_for_cascade["id"]
        with sqlite3.connect(os.environ["BAZAR_DB_PATH"]) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("DELETE FROM guest_feed_posts WHERE id = ?", (post_id,))
            conn.commit()
        self.assertIsNone(repository.get_guest_feed_comment(cascade_comment_id))


if __name__ == "__main__":
    unittest.main()
