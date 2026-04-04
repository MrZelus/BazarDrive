import os
import threading
import unittest
from http.client import HTTPConnection

from app.api.http_handlers import FeedAPIHandler
from http.server import ThreadingHTTPServer


class GuestFeedCspConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FeedAPIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def tearDown(self) -> None:
        os.environ.pop("APP_ENV", None)
        os.environ.pop("GUEST_FEED_CSP_CONNECT_SRC_DEV", None)
        os.environ.pop("GUEST_FEED_CSP_IMG_SRC_DEV", None)
        os.environ.pop("GUEST_FEED_CSP_CONNECT_SRC_PROD", None)
        os.environ.pop("GUEST_FEED_CSP_IMG_SRC_PROD", None)

    def _get_raw(self, path: str) -> tuple[int, bytes, dict[str, str]]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        conn.request("GET", path)
        response = conn.getresponse()
        body = response.read()
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, body, headers

    def test_guest_feed_meta_uses_safe_base_csp(self) -> None:
        status, body, _ = self._get_raw("/public/guest_feed.html")
        html = body.decode("utf-8")

        self.assertEqual(status, 200)
        self.assertIn("connect-src 'self';", html)
        self.assertNotIn("http://localhost:8001", html)

    def test_guest_feed_csp_header_uses_dev_env_sources(self) -> None:
        os.environ["APP_ENV"] = "dev"
        os.environ["GUEST_FEED_CSP_CONNECT_SRC_DEV"] = "'self' http://127.0.0.1:8123"
        os.environ["GUEST_FEED_CSP_IMG_SRC_DEV"] = "'self' data: https: http://127.0.0.1:8123"
        status, _, headers = self._get_raw("/public/guest_feed.html?apiBase=http://127.0.0.1:8123")
        csp = headers.get("content-security-policy", "")

        self.assertEqual(status, 200)
        self.assertIn("connect-src 'self' http://127.0.0.1:8123;", csp)
        self.assertIn("img-src 'self' data: https: http://127.0.0.1:8123;", csp)

    def test_guest_feed_csp_header_uses_prod_env_sources(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["GUEST_FEED_CSP_CONNECT_SRC_PROD"] = "'self' https://api.example.com"
        status, _, headers = self._get_raw("/public/guest_feed.html?apiBase=https://api.example.com")
        csp = headers.get("content-security-policy", "")

        self.assertEqual(status, 200)
        self.assertIn("connect-src 'self' https://api.example.com;", csp)


if __name__ == "__main__":
    unittest.main()
