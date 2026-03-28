import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram.error import BadRequest
from telegram.ext import ConversationHandler

from app.bot import handlers


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


if __name__ == "__main__":
    unittest.main()
