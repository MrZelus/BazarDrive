import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram.error import BadRequest
from telegram.ext import ConversationHandler

from app.bot import handlers
from app.services.exceptions import DriverOrderBlockedError


class BotHandlerResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def test_taxi_comment_handles_admin_chat_not_found(self) -> None:
        update = SimpleNamespace(
            message=SimpleNamespace(text="-", reply_text=AsyncMock()),
            effective_user=SimpleNamespace(id=12345),
        )
        context = SimpleNamespace(
            user_data={"from_addr": "A", "to_addr": "B", "ride_time": "now"},
            bot=SimpleNamespace(send_message=AsyncMock(side_effect=BadRequest("Chat not found"))),
        )

        with patch.object(handlers.repository, "create_taxi_request", return_value=77), patch.object(
            handlers, "get_settings", return_value=SimpleNamespace(admin_chat_id=999)
        ):
            state = await handlers.taxi_comment(update, context)

        self.assertEqual(state, ConversationHandler.END)
        update.message.reply_text.assert_awaited_once_with(
            "Заявка сохранена, но уведомить админа сейчас не удалось."
        )

    async def test_post_text_success_path_unchanged(self) -> None:
        update = SimpleNamespace(
            message=SimpleNamespace(text="Привет", reply_text=AsyncMock()),
            effective_user=SimpleNamespace(id=42),
        )
        context = SimpleNamespace(
            user_data={},
            bot=SimpleNamespace(send_message=AsyncMock(return_value=True)),
        )

        with patch.object(handlers.repository, "create_post", return_value=5), patch.object(
            handlers, "get_settings", return_value=SimpleNamespace(admin_chat_id=111)
        ):
            state = await handlers.post_text(update, context)

        self.assertEqual(state, ConversationHandler.END)
        update.message.reply_text.assert_awaited_once_with("Пост отправлен на модерацию.")

    async def test_driver_status_includes_actions_and_reminders(self) -> None:
        update = SimpleNamespace(
            message=SimpleNamespace(reply_text=AsyncMock()),
            effective_user=SimpleNamespace(id=77),
        )
        context = SimpleNamespace()
        summary = SimpleNamespace(
            title="⛔ Выход на линию запрещён",
            reason="Нет допуска",
            problems=["Нет открытого путевого листа"],
            actions=["Открыть смену", "Загрузить документы"],
        )

        with patch.object(handlers.DriverSummaryService, "build", return_value=summary), patch.object(
            handlers.DriverReminderService, "get_reminders", return_value=[{"message": "Смена не закрыта"}]
        ):
            await handlers.driver_status(update, context)

        update.message.reply_text.assert_awaited_once()
        sent_text = update.message.reply_text.await_args.args[0]
        self.assertIn("Проблемы:", sent_text)
        self.assertIn("🔔 Напоминания:", sent_text)
        self.assertIsNotNone(update.message.reply_text.await_args.kwargs["reply_markup"])

    async def test_open_shift_callback_success(self) -> None:
        query = SimpleNamespace(
            answer=AsyncMock(),
            from_user=SimpleNamespace(id=88),
            message=SimpleNamespace(reply_text=AsyncMock()),
        )
        update = SimpleNamespace(callback_query=query)
        context = SimpleNamespace()

        with patch.object(handlers.WaybillService, "open_shift", return_value=123):
            await handlers.open_shift_callback(update, context)

        query.answer.assert_awaited_once()
        query.message.reply_text.assert_awaited_once_with("✅ Смена открыта")

    async def test_accept_order_blocked_by_guard(self) -> None:
        update = SimpleNamespace(
            message=SimpleNamespace(reply_text=AsyncMock()),
            effective_user=SimpleNamespace(id=99),
        )
        context = SimpleNamespace()

        with patch.object(
            handlers.DriverGuardService,
            "ensure_can_accept_order",
            side_effect=DriverOrderBlockedError(reason="Нет открытого путевого листа"),
        ):
            await handlers.accept_order_handler(update, context)

        update.message.reply_text.assert_awaited_once_with("⛔ Нет открытого путевого листа")


if __name__ == "__main__":
    unittest.main()
