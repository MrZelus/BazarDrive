#!/usr/bin/env python3
"""Capture #121 visual evidence screenshots for guest_feed tabs.

Requires Playwright with Chromium and (optionally) Edge channel installed.
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path


TAB_SELECTORS = {
    "feed": "#main-tab-btn-feed",
    "rules": "#main-tab-btn-rules",
    "profile": "#main-tab-btn-profile",
}

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}


async def capture_for_browser(async_playwright, browser_name: str, page_url: str, out_dir: Path, edge_channel: str | None) -> None:
    async with async_playwright() as p:
        launcher = p.chromium
        launch_kwargs = {"headless": True}
        if browser_name == "edge":
            if not edge_channel:
                raise RuntimeError("Edge channel is not configured. Pass --edge-channel msedge.")
            launch_kwargs["channel"] = edge_channel

        browser = await launcher.launch(**launch_kwargs)
        try:
            for viewport_name, viewport in VIEWPORTS.items():
                context = await browser.new_context(viewport=viewport)
                page = await context.new_page()
                await page.goto(page_url, wait_until="networkidle")
                await page.wait_for_timeout(400)

                for tab_name, selector in TAB_SELECTORS.items():
                    await page.click(selector)
                    await page.wait_for_timeout(250)
                    target = out_dir / f"{tab_name}-{viewport_name}-{browser_name}-after.png"
                    await page.screenshot(path=str(target), full_page=True)
                    print(f"Saved: {target}")

                await context.close()
        finally:
            await browser.close()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Capture guest feed screenshots for issue #121 evidence")
    parser.add_argument("--url", default="http://127.0.0.1:8000/guest_feed.html", help="Page URL to capture")
    parser.add_argument("--out", default="artifacts/121", help="Output directory for screenshots")
    parser.add_argument(
        "--browsers",
        default="chrome,edge",
        help="Comma-separated browsers: chrome,edge",
    )
    parser.add_argument(
        "--edge-channel",
        default="msedge",
        help="Playwright Chromium channel for Edge (set empty string to disable)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    browsers = [item.strip() for item in args.browsers.split(",") if item.strip()]
    edge_channel = args.edge_channel or None

    try:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright is not installed. Install dependency and browser binaries with: "
            "pip install playwright && python -m playwright install chromium msedge"
        ) from exc

    for browser_name in browsers:
        if browser_name not in {"chrome", "edge"}:
            raise ValueError(f"Unsupported browser: {browser_name}")
        try:
            await capture_for_browser(async_playwright, browser_name, args.url, out_dir, edge_channel)
        except PlaywrightError as exc:
            raise RuntimeError(
                "Playwright runtime error. Ensure browser binaries are installed: "
                "python -m playwright install chromium msedge"
            ) from exc

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
