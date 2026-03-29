#!/usr/bin/env python3
"""Generate a lightweight system health dashboard report for BazarDrive.

Inputs are read from local JSON files exported by GitHub Actions steps.
This keeps the script testable and avoids coupling report logic directly to API calls.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tmp" / "system_health"
OUTPUT = ROOT / "tmp" / "system_health_dashboard_report.md"


DOMAIN_RULES = {
    "docs": ["docs/", "README.md"],
    "web": ["public/", "web/"],
    "api": ["app/api/", "app/services/"],
    "bot": ["app/bot/"],
    "data": ["app/db/", "migrations/"],
    "tests": ["tests/"],
    "security": ["docs/security/"],
}


def load_json(name: str) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))



def detect_domains(files: list[str]) -> set[str]:
    domains: set[str] = set()
    for file in files:
        for domain, prefixes in DOMAIN_RULES.items():
            if any(file.startswith(prefix) for prefix in prefixes):
                domains.add(domain)
    return domains



def has_issue_link(body: str | None) -> bool:
    text = (body or "").lower()
    return "closes #" in text or "part of #" in text or "fixes #" in text



def needs_openapi_sync(files: list[str]) -> bool:
    touches_api = any(f.startswith("app/api/") or f.startswith("app/services/") for f in files)
    touches_openapi = any(f == "docs/openapi.yaml" for f in files)
    return touches_api and not touches_openapi



def needs_permissions_sync(files: list[str]) -> bool:
    sensitive = any(
        f.startswith("app/services/driver_compliance")
        or f.startswith("app/api/http_handlers.py")
        or "permissions" in f
        or "driver_documents" in f
        for f in files
    )
    touches_permissions = any(f == "docs/security/permissions_matrix.md" for f in files)
    return sensitive and not touches_permissions



def make_report() -> str:
    prs = load_json("prs.json")
    issues = load_json("issues.json")

    open_pr_count = len(prs)
    pr_without_issue = 0
    conflict_pr = 0
    oversized_pr = 0
    docs_sync_warnings = 0
    multi_domain_pr = 0

    pr_rows: list[str] = []

    for pr in prs:
        body = pr.get("body") or ""
        files = pr.get("changed_files_list") or []
        domains = sorted(detect_domains(files))
        risk_notes: list[str] = []

        if not has_issue_link(body):
            pr_without_issue += 1
            risk_notes.append("no issue link")
        if pr.get("mergeable") is False:
            conflict_pr += 1
            risk_notes.append("conflict")
        if len(files) > 10 or len(domains) > 3:
            oversized_pr += 1
            risk_notes.append("oversized")
        if len(domains) > 3:
            multi_domain_pr += 1
        if needs_openapi_sync(files):
            docs_sync_warnings += 1
            risk_notes.append("api without openapi sync")
        if needs_permissions_sync(files):
            docs_sync_warnings += 1
            risk_notes.append("compliance without permissions sync")

        pr_rows.append(
            f"| #{pr.get('number')} | {', '.join(domains) or '-'} | "
            f"{'yes' if has_issue_link(body) else 'no'} | {'; '.join(risk_notes) or 'ok'} |"
        )

    issues_without_owner = sum(1 for issue in issues if not issue.get("assignees"))

    lines = [
        "# BazarDrive System Health Auto Report",
        "",
        "## Summary",
        "",
        f"- Open PR count: **{open_pr_count}**",
        f"- PR without issue link: **{pr_without_issue}**",
        f"- Conflict PR count: **{conflict_pr}**",
        f"- Oversized PR count: **{oversized_pr}**",
        f"- Multi-domain PR count: **{multi_domain_pr}**",
        f"- Docs sync warnings: **{docs_sync_warnings}**",
        f"- Issues without owner: **{issues_without_owner}**",
        "",
        "## PR review table",
        "",
        "| PR | Domains | Issue link | Risk |",
        "|---|---|---|---|",
    ]

    if pr_rows:
        lines.extend(pr_rows)
    else:
        lines.append("| - | - | - | no open PR data |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is a lightweight generated report.",
            "- Treat warnings as review prompts, not absolute truth.",
            "- Extend rules over time for BazarDrive-specific governance.",
        ]
    )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(make_report(), encoding="utf-8")
    print(f"Wrote report to {OUTPUT}")
