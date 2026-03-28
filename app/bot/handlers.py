import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.db import repository
from app.logging_setup import configure_logging
from app.models.bot_settings import load_bot_settings
from app.services import moderation_service


SETTINGS = None


def get_settings():
    global SETTINGS
    if SETTINGS is None:
        SETTINGS = load_bot_settings()
    return SETTINGS


MAIN_MENU = [["🚕 Такси", "📢 Объявление"], ["📝 Пост в группу"]]
TAXI_FROM, TAXI_TO, TAXI_TIME, TAXI_COMMENT = range(4)
AD_TITLE, AD_TEXT = range(10, 12)
POST_TEXT = 20
LOGGER = logging.getLogger(__name__)


async def _send_message_safe(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        return True
    except BadRequest as error:
        LOGGER.error(
            "Failed to send message due to bad Telegram request. Check chat id and bot permissions.",
            extra={"request_id": "telegram-bad-request", "client_ip": "-", "chat_id": str(chat_id)},
            exc_info=error,
        )
        return False
    except TelegramError as error:
        LOGGER.error(
            "Failed to send message to Telegram.",
            extra={"request_id": "telegram-send-failed", "client_ip": "-", "chat_id": str(chat_id)},
            exc_info=error,
        )
        return False


def moderation_kb(kind: str, object_id: int) -> InlineKeyboardMarkup:
    approve_cb, reject_cb = moderation_service.moderation_keyboard_data(kind, object_id)
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Одобрить", callback_data=approve_cb), InlineKeyboardButton("❌ Отклонить", callback_data=reject_cb)]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    repository.add_user(user.id, user.username or "", user.full_name or "")
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))


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
    await update.message.reply_text("Комментарий водителю (или '-' ):")
    return TAXI_COMMENT


async def taxi_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    comment = update.message.text
    user_id = update.effective_user.id
    req_id = repository.create_taxi_request(
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
    delivered = await _send_message_safe(context, get_settings().admin_chat_id, text)
    if delivered:
        await update.message.reply_text("Заявка принята! Мы скоро свяжемся.")
    else:
        await update.message.reply_text("Заявка сохранена, но уведомить админа сейчас не удалось.")
    return ConversationHandler.END


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
    ad_id = repository.create_ad(user_id, title, text)
    delivered = await _send_message_safe(
        context,
        get_settings().admin_chat_id,
        f"📢 Объявление #{ad_id} (модерация)\nЗаголовок: {title}\nТекст: {text}\nUser ID: {user_id}",
        reply_markup=moderation_kb("ad", ad_id),
    )
    if delivered:
        await update.message.reply_text("Объявление отправлено на модерацию.")
    else:
        await update.message.reply_text("Объявление сохранено, но отправка на модерацию не удалась.")
    return ConversationHandler.END


async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите текст поста для группы:")
    return POST_TEXT


async def post_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    post_id = repository.create_post(user_id, text)
    delivered = await _send_message_safe(
        context,
        get_settings().admin_chat_id,
        f"📝 Пост #{post_id} на модерацию:\n{text}\nUser ID: {user_id}",
        reply_markup=moderation_kb("post", post_id),
    )
    if delivered:
        await update.message.reply_text("Пост отправлен на модерацию.")
    else:
        await update.message.reply_text("Пост сохранен, но отправка на модерацию не удалась.")
    return ConversationHandler.END


async def moderation_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not query.from_user or not moderation_service.is_admin(query.from_user.id, get_settings().admin_ids):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("У вас нет прав на модерацию.")
        return

    action, kind, object_id_raw = (query.data or "::").split(":", maxsplit=2)
    result = moderation_service.approve_or_reject(kind, int(object_id_raw), action)

    if "error" in result:
        await query.edit_message_text(str(result["error"]))
        return

    if "publish_text" in result:
        delivered = await _send_message_safe(context, get_settings().group_chat_id, str(result["publish_text"]))
        if not delivered:
            await query.message.reply_text("Публикация одобрена, но отправка в группу не удалась.")
    await query.edit_message_text(str(result["status_text"]))


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    if not moderation_service.is_admin(user_id, get_settings().admin_ids):
        await update.message.reply_text("Команда доступна только администраторам.")
        return

    rows = repository.list_pending_content()
    if not rows:
        await update.message.reply_text("Нет ожидающих заявок на модерацию.")
        return

    for row in rows:
        await update.message.reply_text(
            moderation_service.format_pending_item(row),
            reply_markup=moderation_kb(str(row["kind"]), int(row["id"])),
        )


async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = repository.list_approved_posts(limit=10, offset=0, include_ads=True)
    if not rows:
        await update.message.reply_text("Пока нет одобренных публикаций в ленте.")
        return

    for row in rows:
        if row["kind"] == "ad":
            text = f"📢 Объявление #{row['id']}\nЗаголовок: {row['title']}\n{row['text']}"
        else:
            text = f"📝 Пост #{row['id']}\n{row['text']}"
        await update.message.reply_text(text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception(
        "Unhandled telegram update error",
        exc_info=context.error,
        extra={"request_id": "telegram-unhandled-error", "client_ip": "-"},
    )


def build_application() -> Application:
    repository.init_db()
    app = Application.builder().token(get_settings().bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("feed", feed))

    app.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🚕 Такси$"), taxi_start)],
            states={
                TAXI_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_from)],
                TAXI_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_to)],
                TAXI_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_time)],
                TAXI_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_comment)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📢 Объявление$"), ad_start)],
            states={
                AD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_title)],
                AD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_text)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📝 Пост в группу$"), post_start)],
            states={POST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_text)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

    app.add_handler(CallbackQueryHandler(moderation_action, pattern=r"^(approve|reject):(ad|post):\\d+$"))
    app.add_error_handler(_error_handler)
    return app


def run_bot() -> None:
    configure_logging("telegram-bot")
    logging.getLogger(__name__).info("Starting telegram bot", extra={"request_id": "startup", "client_ip": "-"})
    build_application().run_polling()
