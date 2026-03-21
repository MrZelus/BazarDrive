from app.db import repository


def is_admin(user_id: int, admin_ids: set[int]) -> bool:
    return bool(admin_ids) and user_id in admin_ids


def moderation_keyboard_data(kind: str, object_id: int) -> tuple[str, str]:
    return f"approve:{kind}:{object_id}", f"reject:{kind}:{object_id}"


def approve_or_reject(kind: str, object_id: int, action: str) -> dict[str, object]:
    if kind == "ad":
        item = repository.get_ad(object_id)
        if not item:
            return {"error": "Объявление не найдено."}
        if action == "approve":
            repository.update_ad_status(object_id, "approved")
            return {
                "status_text": f"✅ Объявление #{object_id} одобрено и опубликовано.",
                "publish_text": f"📢 {item['title']}\n\n{item['text']}",
            }
        repository.update_ad_status(object_id, "rejected")
        return {"status_text": f"❌ Объявление #{object_id} отклонено."}

    if kind == "post":
        item = repository.get_post(object_id)
        if not item:
            return {"error": "Пост не найден."}
        if action == "approve":
            repository.update_post_status(object_id, "approved")
            return {"status_text": f"✅ Пост #{object_id} одобрен и опубликован.", "publish_text": item["text"]}
        repository.update_post_status(object_id, "rejected")
        return {"status_text": f"❌ Пост #{object_id} отклонен."}

    return {"error": "Неизвестный тип модерируемого объекта."}


def format_pending_item(row: dict[str, object]) -> str:
    if row["kind"] == "ad":
        return (
            f"📢 Объявление #{row['id']} (pending)\n"
            f"Заголовок: {row['title']}\n"
            f"Текст: {row['text']}\n"
            f"User ID: {row['user_tg_id']}"
        )
    return f"📝 Пост #{row['id']} (pending)\nТекст: {row['text']}\nUser ID: {row['user_tg_id']}"
