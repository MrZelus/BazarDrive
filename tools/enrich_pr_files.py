#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PRS_PATH = Path("tmp/system_health/prs.json")


def main() -> None:
    if not PRS_PATH.exists():
        raise SystemExit(f"Missing PR data file: {PRS_PATH}")

    with PRS_PATH.open(encoding="utf-8") as f:
        prs = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]

    for pr in prs:
        number = pr.get("number")
        if not number:
            continue
        try:
            out = subprocess.check_output(
                ["gh", "api", f"repos/{repo}/pulls/{number}/files"],
                text=True,
            )
            files = json.loads(out)
            pr["changed_files_list"] = [item.get("filename") for item in files]
        except Exception:
            pr["changed_files_list"] = []

    PRS_PATH.write_text(json.dumps(prs, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
