import os
import unittest

from app.api.http_handlers import FeedAPIHandler


class AuthFlowTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("APP_ENV", None)
        os.environ.pop("API_AUTH_KEYS", None)
        os.environ.pop("API_AUTH_BEARER_TOKENS", None)
        os.environ.pop("MODERATOR_API_KEYS", None)
        os.environ.pop("MODERATOR_BEARER_TOKENS", None)

    def _make_handler(self, headers: dict[str, str] | None = None) -> FeedAPIHandler:
        handler = object.__new__(FeedAPIHandler)
        handler.headers = headers or {}
        handler.command = "POST"
        return handler

    def test_prod_requires_valid_bearer_token_for_write_ops(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["API_AUTH_BEARER_TOKENS"] = "writer-token"

        unauthorized_handler = self._make_handler(headers={"Authorization": "Bearer wrong-token"})
        settings = unauthorized_handler._get_security_settings()
        unauthorized_ctx = unauthorized_handler._resolve_write_auth_context(settings)
        self.assertFalse(unauthorized_ctx.is_authorized)

        authorized_handler = self._make_handler(headers={"Authorization": "Bearer writer-token"})
        settings = authorized_handler._get_security_settings()
        authorized_ctx = authorized_handler._resolve_write_auth_context(settings)
        self.assertTrue(authorized_ctx.is_authorized)
        self.assertEqual(authorized_ctx.role, "author")

    def test_moderator_token_gets_moderator_role(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["MODERATOR_BEARER_TOKENS"] = "mod-token"

        handler = self._make_handler(headers={"Authorization": "Bearer mod-token"})
        settings = handler._get_security_settings()
        context = handler._resolve_write_auth_context(settings)

        self.assertTrue(context.is_authorized)
        self.assertTrue(context.is_moderator)


if __name__ == "__main__":
    unittest.main()
