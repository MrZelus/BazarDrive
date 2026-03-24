#!/usr/bin/env python3
"""Capture #121 visual evidence screenshots for guest_feed tabs.

Requires Playwright with Chromium and (optionally) Edge channel installed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
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


def parse_csv_list(raw: str) -> list[str]:
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def build_capture_plan(
    browsers: list[str],
    out_dir: Path,
    tabs: list[str],
    viewports: list[str],
) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    for browser_name in browsers:
        for viewport_name in viewports:
            for tab_name in tabs:
                target = out_dir / f"{tab_name}-{viewport_name}-{browser_name}-after.png"
                plan.append(
                    {
                        "tab": tab_name,
                        "viewport": viewport_name,
                        "browser": browser_name,
                        "path": str(target),
                    }
                )
    return plan


def build_markdown_matrix(capture_plan: list[dict[str, str]], check_files: bool = False) -> str:
    matrix: dict[str, dict[str, str]] = {tab: {} for tab in TAB_SELECTORS}
    for item in capture_plan:
        key = f"{item['viewport']}/{item['browser']}"
        matrix[item["tab"]][key] = item["path"]

    header = "| Tab | desktop/chrome | desktop/edge | mobile/chrome | mobile/edge |"
    separator = "|---|---|---|---|---|"
    rows = [header, separator]

    for tab in TAB_SELECTORS:
        label = {
            "feed": "Лента",
            "rules": "Правила",
            "profile": "Профиль",
        }[tab]
        row = [label]
        for key in ("desktop/chrome", "desktop/edge", "mobile/chrome", "mobile/edge"):
            path = matrix[tab].get(key, "")
            if not path:
                row.append("-")
                continue
            if check_files:
                status = "✅" if Path(path).exists() else "❌"
                row.append(f"{status} [{path}]({path})")
            else:
                row.append(f"[{path}]({path})")
        rows.append("| " + " | ".join(row) + " |")
    return "\n".join(rows)


def find_missing_capture_files(capture_plan: list[dict[str, str]]) -> list[str]:
    return [item["path"] for item in capture_plan if not Path(item["path"]).exists()]


async def capture_for_browser(
    async_playwright,
    browser_name: str,
    page_url: str,
    out_dir: Path,
    edge_channel: str | None,
    tabs: list[str],
    viewports: list[str],
) -> None:
    async with async_playwright() as p:
        launcher = p.chromium
        launch_kwargs = {"headless": True}
        if browser_name == "edge":
            if not edge_channel:
                raise RuntimeError("Edge channel is not configured. Pass --edge-channel msedge.")
            launch_kwargs["channel"] = edge_channel

        browser = await launcher.launch(**launch_kwargs)
        try:
            for viewport_name in viewports:
                context = await browser.new_context(viewport=VIEWPORTS[viewport_name])
                page = await context.new_page()
                await page.goto(page_url, wait_until="networkidle")
                await page.wait_for_timeout(400)

                for tab_name in tabs:
                    selector = TAB_SELECTORS[tab_name]
                    await page.click(selector)
                    await page.wait_for_timeout(250)
                    target = out_dir / f"{tab_name}-{viewport_name}-{browser_name}-after.png"
                    await page.screenshot(path=str(target), full_page=True)
                    print(f"Saved: {target}")

                await context.close()
        finally:
            await browser.close()


def validate_values(values: list[str], allowed: set[str], label: str) -> None:
    unsupported = [value for value in values if value not in allowed]
    if unsupported:
        raise RuntimeError(f"Unsupported {label}: {unsupported[0]}")


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
    parser.add_argument(
        "--tabs",
        default="feed,rules,profile",
        help="Comma-separated tab keys to capture: feed,rules,profile",
    )
    parser.add_argument(
        "--viewports",
        default="desktop,mobile",
        help="Comma-separated viewport keys to capture: desktop,mobile",
    )
    parser.add_argument("--manifest", default="", help="Optional path to write JSON capture manifest")
    parser.add_argument(
        "--report-md",
        default="",
        help="Optional path to write Markdown evidence matrix based on selected capture plan",
    )
    parser.add_argument(
        "--report-md-check-files",
        action="store_true",
        help="Annotate Markdown matrix cells with ✅/❌ based on actual file existence",
    )
    parser.add_argument(
        "--fail-on-missing-files",
        action="store_true",
        help="Exit with code 1 when expected screenshot files from the selected capture plan are missing",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print capture plan without running Playwright")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    browsers = parse_csv_list(args.browsers)
    tabs = parse_csv_list(args.tabs)
    viewports = parse_csv_list(args.viewports)
    edge_channel = args.edge_channel or None

    validate_values(browsers, {"chrome", "edge"}, "browser")
    validate_values(tabs, set(TAB_SELECTORS), "tab")
    validate_values(viewports, set(VIEWPORTS), "viewport")

    capture_plan = build_capture_plan(
        browsers=browsers,
        out_dir=out_dir,
        tabs=tabs,
        viewports=viewports,
    )
    manifest_path = Path(args.manifest) if args.manifest else None
    report_md_path = Path(args.report_md) if args.report_md else None

    def write_outputs(dry_run: bool) -> None:
        if manifest_path:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "url": args.url,
                        "dry_run": dry_run,
                        "captures": capture_plan,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"Manifest: {manifest_path}")
        if report_md_path:
            report_md_path.parent.mkdir(parents=True, exist_ok=True)
            report_md_path.write_text(
                build_markdown_matrix(capture_plan, check_files=args.report_md_check_files) + "\n",
                encoding="utf-8",
            )
            print(f"Markdown report: {report_md_path}")

    if args.dry_run:
        for item in capture_plan:
            print(f"PLAN: {item['path']}")
        write_outputs(dry_run=True)
        if args.fail_on_missing_files:
            missing_files = find_missing_capture_files(capture_plan)
            if missing_files:
                print(f"ERROR: Missing {len(missing_files)} expected screenshot file(s).")
                for missing_path in missing_files:
                    print(f"MISSING: {missing_path}")
                return 1
        return 0

    try:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright is not installed. Install dependency and browser binaries with: "
            "pip install playwright && python -m playwright install chromium msedge"
        ) from exc

    for browser_name in browsers:
        try:
            await capture_for_browser(
                async_playwright,
                browser_name,
                args.url,
                out_dir,
                edge_channel,
                tabs,
                viewports,
            )
        except PlaywrightError as exc:
            raise RuntimeError(
                "Playwright runtime error. Ensure browser binaries are installed: "
                "python -m playwright install chromium msedge"
            ) from exc

    write_outputs(dry_run=False)
    if args.fail_on_missing_files:
        missing_files = find_missing_capture_files(capture_plan)
        if missing_files:
            print(f"ERROR: Missing {len(missing_files)} expected screenshot file(s).")
            for missing_path in missing_files:
                print(f"MISSING: {missing_path}")
            return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
