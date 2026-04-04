#!/usr/bin/env python3
"""Headless e2e smoke for guest feed UI.

Scenario:
1) Fill profile.
2) Publish a post.
3) Search in rules.
4) Return to feed and add comment + reaction.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_STATIC_PORT = 8000
DEFAULT_API_PORT = 8001
DEFAULT_UI_CSP_CONNECT_SRC_DEV = "'self' http://localhost:8001 http://127.0.0.1:8001"


@dataclass
class SmokeConfig:
    static_port: int
    api_port: int
    host: str
    timeout_seconds: float
    no_start_servers: bool
    dry_run: bool
    post_text: str
    rules_query: str


class SmokeError(RuntimeError):
    """Domain error for smoke execution failures."""


def parse_args() -> SmokeConfig:
    parser = argparse.ArgumentParser(description="Run guest feed e2e smoke with headless browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for static/api servers (default: 127.0.0.1)")
    parser.add_argument("--static-port", type=int, default=DEFAULT_STATIC_PORT)
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--post-text", default="QA smoke post 2026-04-04")
    parser.add_argument("--rules-query", default="580-ФЗ")
    parser.add_argument("--no-start-servers", action="store_true", help="Use already-running servers")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only, without Playwright")
    args = parser.parse_args()
    return SmokeConfig(
        static_port=args.static_port,
        api_port=args.api_port,
        host=args.host,
        timeout_seconds=args.timeout_seconds,
        no_start_servers=args.no_start_servers,
        dry_run=args.dry_run,
        post_text=args.post_text,
        rules_query=args.rules_query,
    )


def healthcheck(url: str, timeout_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:  # nosec B310
                if 200 <= response.status < 300:
                    return
                last_error = f"HTTP {response.status}"
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise SmokeError(f"Service healthcheck failed for {url}: {last_error or 'unknown error'}")


def _spawn(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.Popen[str]:
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )


def stop_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


def build_urls(config: SmokeConfig) -> tuple[str, str, str]:
    api_base = f"http://{config.host}:{config.api_port}"
    static_base = f"http://{config.host}:{config.static_port}"
    query = urllib.parse.urlencode({"apiBase": api_base})
    guest_feed_url = f"{static_base}/public/guest_feed.html?{query}"
    return api_base, static_base, guest_feed_url


def build_api_process_env(config: SmokeConfig) -> dict[str, str]:
    env = dict(os.environ)
    env["FEED_API_HOST"] = config.host
    env["FEED_API_PORT"] = str(config.api_port)
    return env


def _parse_connect_src_origins(raw_value: str) -> set[tuple[str, int]]:
    origins: set[tuple[str, int]] = set()
    for item in raw_value.split():
        candidate = item.strip()
        if not candidate.startswith("http://") and not candidate.startswith("https://"):
            continue
        parsed = urllib.parse.urlparse(candidate)
        if not parsed.hostname or parsed.port is None:
            continue
        origins.add((parsed.hostname, parsed.port))
    return origins


def validate_api_base_against_ui_csp(config: SmokeConfig) -> None:
    raw_connect_src = os.getenv("GUEST_FEED_CSP_CONNECT_SRC_DEV", DEFAULT_UI_CSP_CONNECT_SRC_DEV)
    allowed_origins = _parse_connect_src_origins(raw_connect_src)
    key = (config.host, config.api_port)
    if key in allowed_origins:
        return
    allowed = ", ".join(f"http://{host}:{port}" for host, port in sorted(allowed_origins))
    raise SmokeError(
        "Configured apiBase is blocked by UI CSP connect-src. "
        f"Requested: http://{config.host}:{config.api_port}. "
        f"Allowed by GUEST_FEED_CSP_CONNECT_SRC_DEV: {allowed or '(none)'}."
    )


def run_playwright_scenario(guest_feed_url: str, config: SmokeConfig) -> dict[str, str]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SmokeError(
            "Playwright is not installed. Install dependency and browser binaries with: "
            "pip install playwright && python -m playwright install chromium"
        )

    result = {
        "profile": "pending",
        "publish": "pending",
        "rules_search": "pending",
        "feed_actions": "pending",
    }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.goto(guest_feed_url, wait_until="networkidle", timeout=20_000)

            page.click("#main-tab-btn-profile")
            page.fill("#profileName", "QA Smoke")
            page.fill("#profileEmail", "qa-smoke@example.com")
            page.click("#saveProfileBtn")
            page.wait_for_selector("#appNotification:not(.hidden)", timeout=10_000)
            result["profile"] = "passed"

            page.click("#main-tab-btn-feed")
            page.fill("#newPostInput", config.post_text)
            page.click("#publishBtn")
            page.wait_for_selector("article", timeout=12_000)
            page.wait_for_selector(f"text={config.post_text}", timeout=12_000)
            result["publish"] = "passed"

            page.click("#main-tab-btn-rules")
            page.fill("#docsSearch", config.rules_query)
            page.wait_for_timeout(400)
            docs_status = page.locator("#docsSearchStatus").inner_text().strip()
            if "Найдено" not in docs_status and "Показаны" not in docs_status:
                raise SmokeError(f"Rules search status unexpected: {docs_status!r}")
            result["rules_search"] = "passed"

            page.click("#main-tab-btn-feed")
            first_article = page.locator("article").first
            first_article.get_by_role("button", name="Лайк").click()
            comment_input = first_article.locator("form input[placeholder='Напишите комментарий...']")
            comment_input.fill("smoke comment")
            first_article.get_by_role("button", name="Отправить комментарий").click()
            page.wait_for_selector("text=Комментарий добавлен.", timeout=12_000)
            result["feed_actions"] = "passed"

            context.close()
            browser.close()
    except PlaywrightTimeoutError as exc:
        raise SmokeError(f"Playwright timeout: {exc}")

    return result


def ensure_playwright_dependency() -> None:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        raise SmokeError(
            "Playwright is not installed. Install dependency and browser binaries with: "
            "pip install playwright && python -m playwright install chromium"
        )


def main() -> int:
    config = parse_args()
    api_base, static_base, guest_feed_url = build_urls(config)
    plan = {
        "api_base": api_base,
        "static_base": static_base,
        "guest_feed_url": guest_feed_url,
        "steps": [
            "fill_profile",
            "publish_post",
            "search_rules",
            "comment_and_react",
        ],
        "dry_run": config.dry_run,
        "no_start_servers": config.no_start_servers,
    }
    print("PLAN:")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if config.dry_run:
        return 0

    repo_root = Path(__file__).resolve().parent.parent
    api_proc: subprocess.Popen[str] | None = None
    static_proc: subprocess.Popen[str] | None = None

    try:
        validate_api_base_against_ui_csp(config)
        ensure_playwright_dependency()
        if not config.no_start_servers:
            api_proc = _spawn([sys.executable, "run_api.py"], cwd=repo_root, env=build_api_process_env(config))
            static_proc = _spawn([sys.executable, "-m", "http.server", str(config.static_port), "--bind", config.host], cwd=repo_root)

        healthcheck(f"{api_base}/health", config.timeout_seconds)
        healthcheck(guest_feed_url, config.timeout_seconds)
        summary = run_playwright_scenario(guest_feed_url, config)

        print("RESULT:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeError as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        if static_proc:
            stop_process(static_proc)
        if api_proc:
            stop_process(api_proc)


if __name__ == "__main__":
    raise SystemExit(main())
