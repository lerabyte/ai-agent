#!/usr/bin/env python3
"""Offline structural checks for the course repository."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PARTS = [
    "01-connect-model",
    "02-first-tool",
    "03-agent-loop",
    "04-multiple-tools",
    "05-error-recovery",
    "06-permissions-and-limits",
]


def require(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Missing required course file: {path.relative_to(ROOT)}")


def check_python(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
    if "TODO" in source and "/solution/" in path.as_posix():
        raise AssertionError(f"Solution still contains TODO: {path.relative_to(ROOT)}")


def check_internal_markdown_links() -> None:
    """Confirm that every relative Markdown link stays in the repo and exists."""
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for page in ROOT.rglob("*.md"):
        for raw_target in link_pattern.findall(page.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue

            resolved = (page.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError as error:
                raise AssertionError(
                    f"Link leaves repository: {page.relative_to(ROOT)} -> {target}"
                ) from error
            require(resolved)


def main() -> None:
    required_root_files = [
        ROOT / "README.md",
        ROOT / "START_HERE.md",
        ROOT / "UPLOAD_WITH_GITHUB_DESKTOP.md",
        ROOT / "SOCIAL_CAPTIONS.md",
        ROOT / "LICENSE",
        ROOT / "requirements.txt",
        ROOT / "course" / "index.html",
        ROOT / "course" / "styles.css",
        ROOT / "course" / "app.js",
    ]
    for path in required_root_files:
        require(path)

    for part in PARTS:
        part_root = ROOT / "parts" / part
        for relative in [
            "README.md",
            "challenge.md",
            "starter/agent.py",
            "solution/agent.py",
        ]:
            require(part_root / relative)
        check_python(part_root / "starter" / "agent.py")
        check_python(part_root / "solution" / "agent.py")

    check_internal_markdown_links()

    html = (ROOT / "course" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "course" / "app.js").read_text(encoding="utf-8")
    for part in PARTS:
        if part not in html and part not in javascript:
            raise AssertionError(f"Dashboard does not reference {part}")

    print("Course structure: OK")
    print("Python syntax: OK")
    print("Internal Markdown links: OK")
    print("Dashboard lesson links: OK")


if __name__ == "__main__":
    main()
