import os
import sqlite3
import tempfile
import unittest

from app.db import repository
from app.services.waybill_service import WaybillService


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
        self.assertEqual(len(created["media"]), 1)
        self.assertEqual(created["media"][0]["url"], "https://example.com/image.jpg")

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
        self.assertEqual(len(items[0]["media"]), 1)

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

    def test_close_driver_waybill_persists_shift_facts_and_status(self) -> None:
        created_doc = repository.create_driver_document(
            profile_id="driver-main",
            type="waybill",
            number="WB-500790280312",
            valid_until="2026-03-29",
            status="open",
        )

        closed_doc = repository.close_driver_waybill(
            created_doc["id"],
            {
                "postshift_medical_at": "2026-03-29T00:10:00Z",
                "postshift_medical_result": "Допущен",
                "actual_return_at": "2026-03-29T00:08:00Z",
                "odometer_end": 171_599,
                "distance_km": 289.4,
                "fuel_spent_liters": 22.3,
                "vehicle_condition": "Технически исправен",
                "stops_info": "Город / пригород",
                "notes": "Смена завершена штатно",
                "closed_at": "2026-03-29T00:12:00Z",
            },
        )
        self.assertIsNotNone(closed_doc)
        self.assertEqual(closed_doc["status"], "closed")
        self.assertEqual(closed_doc["postshift_medical_result"], "Допущен")
        self.assertEqual(closed_doc["actual_return_at"], "2026-03-29T00:08:00Z")
        self.assertEqual(closed_doc["odometer_end"], 171_599)
        self.assertAlmostEqual(float(closed_doc["distance_km"]), 289.4, places=3)
        self.assertAlmostEqual(float(closed_doc["fuel_spent_liters"]), 22.3, places=3)
        self.assertEqual(closed_doc["vehicle_condition"], "Технически исправен")
        self.assertEqual(closed_doc["notes"], "Смена завершена штатно")

    def test_close_driver_waybill_fails_for_non_waybill_document(self) -> None:
        created_doc = repository.create_driver_document(
            profile_id="driver-main",
            type="passport",
            number="4010 123456",
            status="uploaded",
        )
        with self.assertRaises(ValueError):
            repository.close_driver_waybill(
                created_doc["id"],
                {
                    "postshift_medical_at": "2026-03-29T00:10:00Z",
                    "postshift_medical_result": "Допущен",
                    "actual_return_at": "2026-03-29T00:08:00Z",
                    "odometer_end": 1,
                    "distance_km": 1.0,
                    "vehicle_condition": "Исправен",
                },
            )

    def test_get_active_waybill_expires_outdated_open_shift(self) -> None:
        outdated = repository.create_driver_document(
            profile_id="driver-main",
            type="waybill",
            number="WB-OLD-1",
            valid_until="2000-01-01",
            status="open",
        )
        active_waybill = WaybillService.get_active_waybill("driver-main")
        self.assertIsNone(active_waybill)

        listed_docs = repository.list_driver_documents(profile_id="driver-main")
        expired_waybill = next(item for item in listed_docs if item["id"] == outdated["id"])
        self.assertEqual(expired_waybill["status"], "expired")

    def test_open_shift_ignores_outdated_open_waybill_after_auto_expire(self) -> None:
        repository.create_driver_document(
            profile_id="driver-main",
            type="waybill",
            number="WB-OLD-2",
            valid_until="2000-01-01",
            status="open",
        )

        new_waybill_id = WaybillService.open_shift(profile_id="driver-main", vehicle_condition="Исправен")
        self.assertGreater(new_waybill_id, 0)

        listed_docs = repository.list_driver_documents(profile_id="driver-main")
        statuses = {item["id"]: item["status"] for item in listed_docs}
        self.assertIn("expired", statuses.values())
        self.assertEqual(statuses[new_waybill_id], "open")

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
        self.assertEqual(repository.count_guest_feed_comments(post_id=post_id), 1)

        updated = repository.update_guest_feed_comment(comment_id=comment_id, text="Обновлённый комментарий")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["text"], "Обновлённый комментарий")

        deleted = repository.delete_guest_feed_comment(comment_id)
        self.assertTrue(deleted)
        self.assertIsNone(repository.get_guest_feed_comment(comment_id))
        self.assertEqual(repository.count_guest_feed_comments(post_id=post_id), 0)

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

    def test_guest_feed_reactions_upsert_aggregate_and_delete(self) -> None:
        post = repository.create_guest_feed_post(author="Ivan", text="Пост с реакциями", guest_profile_id="guest-1")
        post_id = post["id"]

        repository.set_guest_feed_reaction(post_id=post_id, guest_profile_id="guest-a", reaction_type="like")
        repository.set_guest_feed_reaction(post_id=post_id, guest_profile_id="guest-a", reaction_type="like")
        repository.set_guest_feed_reaction(post_id=post_id, guest_profile_id="guest-b", reaction_type="dislike")

        aggregated = repository.aggregate_guest_feed_reactions([post_id])
        self.assertEqual(aggregated[post_id].get("like"), 1)
        self.assertEqual(aggregated[post_id].get("dislike"), 1)

        my_reactions = repository.get_guest_feed_my_reactions([post_id], guest_profile_id="guest-a")
        self.assertEqual(my_reactions.get(post_id), "like")

        deleted = repository.delete_guest_feed_reaction(post_id=post_id, guest_profile_id="guest-a")
        self.assertTrue(deleted)
        after_delete = repository.aggregate_guest_feed_reactions([post_id])
        self.assertEqual(after_delete[post_id].get("like", 0), 0)

    def test_guest_feed_post_media_crud_and_ordering(self) -> None:
        created = repository.create_guest_feed_post(
            author="Media Author",
            text="Пост с несколькими вложениями",
            image_url="https://example.com/legacy.jpg",
            guest_profile_id="guest-media",
            media=[
                {"media_type": "image", "url": "https://example.com/2.jpg", "position": 1},
                {"media_type": "video", "url": "https://example.com/1.mp4", "position": 0},
            ],
        )
        self.assertEqual([item["media_type"] for item in created["media"]], ["video", "image"])
        self.assertEqual([item["position"] for item in created["media"]], [0, 1])

        updated = repository.update_guest_feed_post(
            post_id=created["id"],
            author="Media Author",
            text="Пост с обновлёнными вложениями",
            image_url="https://example.com/fallback.jpg",
            media=[
                {"media_type": "image", "url": "https://example.com/new.jpg", "position": 0},
            ],
        )
        self.assertIsNotNone(updated)
        self.assertEqual(len(updated["media"]), 1)
        self.assertEqual(updated["media"][0]["url"], "https://example.com/new.jpg")

    def test_list_guest_feed_posts_by_cursor_without_duplicates(self) -> None:
        created_ids: list[int] = []
        for idx in range(5):
            created = repository.create_guest_feed_post(
                author=f"Author {idx}",
                text=f"Post {idx}",
                guest_profile_id="guest-cursor",
            )
            created_ids.append(int(created["id"]))

        first_page = repository.list_guest_feed_posts_by_cursor(limit=2)
        self.assertEqual(len(first_page), 2)
        cursor_post = first_page[-1]

        second_page = repository.list_guest_feed_posts_by_cursor(
            limit=2,
            cursor_created_at=str(cursor_post["created_at"]),
            cursor_id=int(cursor_post["id"]),
        )
        self.assertEqual(len(second_page), 2)

        first_ids = {int(item["id"]) for item in first_page}
        second_ids = {int(item["id"]) for item in second_page}
        self.assertEqual(len(first_ids.intersection(second_ids)), 0)

    def test_guest_feed_search_case_insensitive_for_cyrillic_in_list_cursor_and_count(self) -> None:
        repository.create_guest_feed_post(
            author="ИВАН",
            text="Поездка до МОСКВА",
            guest_profile_id="guest-search-ru",
        )
        repository.create_guest_feed_post(
            author="ПЕТР",
            text="Поездка до СОЧИ",
            guest_profile_id="guest-search-ru",
        )
        repository.create_guest_feed_post(
            author="Мария",
            text="Маршрут через Москва",
            guest_profile_id="guest-search-ru",
        )

        listed_by_author = repository.list_guest_feed_posts(limit=10, offset=0, search_query="иван")
        self.assertEqual(len(listed_by_author), 1)
        self.assertEqual(str(listed_by_author[0]["author"]), "ИВАН")

        listed_by_city = repository.list_guest_feed_posts(limit=10, offset=0, search_query="москва")
        self.assertEqual(len(listed_by_city), 2)
        self.assertEqual(repository.count_guest_feed_posts(search_query="москва"), 2)

        first_page = repository.list_guest_feed_posts_by_cursor(limit=1, search_query="москва")
        self.assertEqual(len(first_page), 1)
        next_cursor = first_page[-1]

        second_page = repository.list_guest_feed_posts_by_cursor(
            limit=1,
            cursor_created_at=str(next_cursor["created_at"]),
            cursor_id=int(next_cursor["id"]),
            search_query="москва",
        )
        self.assertEqual(len(second_page), 1)
        self.assertNotEqual(int(first_page[0]["id"]), int(second_page[0]["id"]))

    def test_guest_feed_search_normalizes_width_and_case(self) -> None:
        repository.create_guest_feed_post(
            author="Ｔａｘｉ Driver",
            text="Маршрут до Москва",
            guest_profile_id="guest-search-normalized",
        )

        listed = repository.list_guest_feed_posts(limit=10, offset=0, search_query="taxi")
        self.assertEqual(len(listed), 1)
        self.assertEqual(str(listed[0]["author"]), "Ｔａｘｉ Driver")
        self.assertEqual(repository.count_guest_feed_posts(search_query="TAXI"), 1)


if __name__ == "__main__":
    unittest.main()
