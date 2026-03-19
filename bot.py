import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db import (
    add_user,
    create_ad,
    create_post,
    create_taxi_request,
    get_ad,
    get_post,
    init_db,
    list_pending_content,
    update_ad_status,
    update_post_status,
)

# ========= НАСТРОЙКИ =========
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-1001234567890"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1009876543210"))
ADMIN_IDS = {
    int(uid)
    for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip()
}
# =============================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MAIN_MENU = [["🚕 Такси", "📢 Объявление"], ["📝 Пост в группу"]]

# States taxi
TAXI_FROM, TAXI_TO, TAXI_TIME, TAXI_COMMENT = range(4)
# States ad
AD_TITLE, AD_TEXT = range(10, 12)
# States post
POST_TEXT = 20


def moderation_kb(kind: str, object_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Одобрить", callback_data=f"approve:{kind}:{object_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{kind}:{object_id}"),
            ]
        ]
    )


def is_admin(user_id: int) -> bool:
    return bool(ADMIN_IDS) and user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    add_user(user.id, user.username or "", user.full_name or "")
    kb = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=kb)


# -------- Такси --------
async def taxi_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Откуда вас забрать?")
    return TAXI_FROM


async def taxi_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["from_addr"] = update.message.text
    await update.message.reply_text("Куда ехать?")
    return TAXI_TO


async def taxi_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["to_addr"] = update.message.text
    await update.message.reply_text("Когда ехать? (например: сейчас / 18:30)")
    return TAXI_TIME


async def taxi_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ride_time"] = update.message.text
    await update.message.reply_text("Комментарий водителю (или '-' ):" )
    return TAXI_COMMENT


async def taxi_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    comment = update.message.text
    user_id = update.effective_user.id

    req_id = create_taxi_request(
        user_tg_id=user_id,
        from_addr=context.user_data["from_addr"],
        to_addr=context.user_data["to_addr"],
        ride_time=context.user_data["ride_time"],
        comment=comment,
    )

    text = (
        f"🚕 Новая заявка #{req_id}\n"
        f"От: {context.user_data['from_addr']}\n"
        f"До: {context.user_data['to_addr']}\n"
        f"Время: {context.user_data['ride_time']}\n"
        f"Комментарий: {comment}\n"
        f"User ID: {user_id}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    await update.message.reply_text("Заявка принята! Мы скоро свяжемся.")
    return ConversationHandler.END


# -------- Объявление --------
async def ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите заголовок объявления:")
    return AD_TITLE


async def ad_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ad_title"] = update.message.text
    await update.message.reply_text("Введите текст объявления:")
    return AD_TEXT


async def ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = context.user_data["ad_title"]
    text = update.message.text
    user_id = update.effective_user.id

    ad_id = create_ad(user_id, title, text)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"📢 Объявление #{ad_id} (модерация)\n"
            f"Заголовок: {title}\n"
            f"Текст: {text}\n"
            f"User ID: {user_id}"
        ),
        reply_markup=moderation_kb("ad", ad_id),
    )

    await update.message.reply_text("Объявление отправлено на модерацию.")
    return ConversationHandler.END


# -------- Пост в группу --------
async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите текст поста для группы:")
    return POST_TEXT


async def post_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    post_id = create_post(user_id, text)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📝 Пост #{post_id} на модерацию:\n{text}\nUser ID: {user_id}",
        reply_markup=moderation_kb("post", post_id),
    )
    await update.message.reply_text("Пост отправлен на модерацию.")
    return ConversationHandler.END


async def moderation_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not query.from_user or not is_admin(query.from_user.id):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("У вас нет прав на модерацию.")
        return

    action, kind, object_id_raw = (query.data or "::").split(":", maxsplit=2)
    object_id = int(object_id_raw)

    if kind == "ad":
        item = get_ad(object_id)
        if not item:
            await query.edit_message_text("Объявление не найдено.")
            return

        if action == "approve":
            update_ad_status(object_id, "approved")
            published = f"📢 {item['title']}\n\n{item['text']}"
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=published)
            await query.edit_message_text(f"✅ Объявление #{object_id} одобрено и опубликовано.")
        else:
            update_ad_status(object_id, "rejected")
            await query.edit_message_text(f"❌ Объявление #{object_id} отклонено.")

    elif kind == "post":
        item = get_post(object_id)
        if not item:
            await query.edit_message_text("Пост не найден.")
            return

        if action == "approve":
            update_post_status(object_id, "approved")
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=item["text"])
            await query.edit_message_text(f"✅ Пост #{object_id} одобрен и опубликован.")
        else:
            update_post_status(object_id, "rejected")
            await query.edit_message_text(f"❌ Пост #{object_id} отклонен.")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_admin(user_id):
        await update.message.reply_text("Команда доступна только администраторам.")
        return

    rows = list_pending_content()
    if not rows:
        await update.message.reply_text("Нет ожидающих заявок на модерацию.")
        return

    for row in rows:
        if row["kind"] == "ad":
            text = (
                f"📢 Объявление #{row['id']} (pending)\n"
                f"Заголовок: {row['title']}\n"
                f"Текст: {row['text']}\n"
                f"User ID: {row['user_tg_id']}"
            )
        else:
            text = (
                f"📝 Пост #{row['id']} (pending)\n"
                f"Текст: {row['text']}\n"
                f"User ID: {row['user_tg_id']}"
            )

        await update.message.reply_text(
            text,
            reply_markup=moderation_kb(row["kind"], row["id"]),
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


def main() -> None:
    if BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        raise ValueError("Укажите BOT_TOKEN через переменную окружения BOT_TOKEN")

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", pending))

    taxi_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚕 Такси$"), taxi_start)],
        states={
            TAXI_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_from)],
            TAXI_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_to)],
            TAXI_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_time)],
            TAXI_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    ad_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Объявление$"), ad_start)],
        states={
            AD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_title)],
            AD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    post_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Пост в группу$"), post_start)],
        states={
            POST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(taxi_conv)
    app.add_handler(ad_conv)
    app.add_handler(post_conv)
    app.add_handler(CallbackQueryHandler(moderation_action, pattern=r"^(approve|reject):(ad|post):\\d+$"))

    app.run_polling()


if __name__ == "__main__":
    main()
