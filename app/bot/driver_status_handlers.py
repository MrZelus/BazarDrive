from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.services.driver_summary_service import DriverSummaryService
from app.services.waybill_service import WaybillService


def _build_status_keyboard(actions: list[str]) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []

    if "Открыть смену" in actions:
        rows.append([InlineKeyboardButton("🚕 Открыть смену", callback_data="driver:open_shift")])

    if "Загрузить документы" in actions or "Обновить документы" in actions or "Проверить документы" in actions:
        rows.append([InlineKeyboardButton("📄 Загрузить документы", callback_data="driver:upload_docs")])

    if not rows:
        return None

    return InlineKeyboardMarkup(rows)


def _render_summary_text(summary: dict) -> str:
    text = f"{summary['title']}\n\nПричина:\n{summary['reason']}"

    problems = summary.get("problems") or []
    if problems:
        text += "\n\nПроблемы:\n" + "\n".join(f"• {item}" for item in problems)

    actions = summary.get("actions") or []
    if actions:
        text += "\n\nЧто сделать:\n" + "\n".join(f"• {item}" for item in actions)

    return text


async def driver_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return

    profile_id = str(user.id)
    summary = DriverSummaryService.build(profile_id).to_dict()
    reply_markup = _build_status_keyboard(summary.get("actions", []))
    text = _render_summary_text(summary)

    message = update.effective_message
    if message:
        await message.reply_text(text, reply_markup=reply_markup)


async def open_shift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    profile_id = str(query.from_user.id)

    try:
        WaybillService.open_shift(profile_id=profile_id, vehicle_condition="OK")
        summary = DriverSummaryService.build(profile_id).to_dict()
        reply_markup = _build_status_keyboard(summary.get("actions", []))
        text = "✅ Смена открыта\n\n" + _render_summary_text(summary)
        if query.message:
            await query.message.reply_text(text, reply_markup=reply_markup)
    except Exception as exc:
        if query.message:
            await query.message.reply_text(f"❌ Не удалось открыть смену: {exc}")


async def upload_docs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    if query.message:
        await query.message.reply_text(
            "📄 Загрузка документов пока в следующем шаге.\n"
            "Сюда потом подключим сценарий отправки и проверки документов."
        )


def get_driver_status_handlers() -> list:
    return [
        CommandHandler("status", driver_status_command),
        MessageHandler(filters.Regex(r"^📊 Мой статус$"), driver_status_command),
        CallbackQueryHandler(open_shift_callback, pattern=r"^driver:open_shift$"),
        CallbackQueryHandler(upload_docs_callback, pattern=r"^driver:upload_docs$"),
    ]
