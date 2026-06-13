#!/usr/bin/env python3
# Copyright (c) 2026 Ernest Hamblen <rioplay@rioplay.dev>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Import a lightly-cleaned Aden devlog entry into the blog as a timeline page.
#
# Source of truth is ~/Projects/aden-devlog/log/<date>.adoc — the raw, honest,
# internal development log. This brings an entry onto the public blog without
# losing its voice: it keeps the rounds, the dead ends, and the self-corrections,
# and only neutralizes the internal scaffolding that should not be published:
#   - strips the AsciiDoc doc header + the prev/next xref nav bars (the blog's
#     theme and the timeline page supply navigation),
#   - rewrites cross-day xref: links into Hugo /devlog/<date>/ URLs,
#     de-links references to the (unpublished) research roadmap to plain text,
#   - rewrites ~/Projects/... paths to neutral names,
#   - promotes the entry's === round headings to == so the page has a clean
#     heading hierarchy and a table of contents.
#
# Commit hashes are intentionally left as inline code, not auto-linked: the
# devlog narrates with pre-rebase SHAs that no longer resolve on origin (see the
# SHA-remap note inside the 06-09 entry), so linking them would 404. Wiring live
# commit links is a deferred follow-up.
#
# Usage:  python3 scripts/import-devlog.py 2026-06-09
#         python3 scripts/import-devlog.py --all

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVLOG_SRC = Path.home() / "Projects" / "aden-devlog" / "log"
OUT_DIR = ROOT / "content" / "devlog"

PATH_SUBS = [
    ("~/Projects/rioplay.dev", "the blog repo"),
    ("~/Projects/aden-devlog", "the devlog"),
    ("~/Projects/research", "the research notes"),
    ("~/Projects/aden", "the aden repo"),
]


def extract_lead(lines):
    """Pull the [.lead] paragraph for the front-matter summary."""
    out = []
    grab = False
    for ln in lines:
        if ln.strip() == "[.lead]":
            grab = True
            continue
        if grab:
            if not ln.strip():
                break
            out.append(ln.strip())
    text = " ".join(out)
    text = re.sub(r"\s+", " ", text)
    # Drop AsciiDoc inline markup for a clean plain-text summary.
    text = re.sub(r"[*_`]", "", text)
    if len(text) > 280:
        cut = text.rfind(". ", 0, 280)
        text = text[: cut + 1] if cut > 120 else text[:277] + "..."
    return text.strip()


def clean_body(lines):
    body = []
    in_header = True
    for ln in lines:
        # Strip the leading doc header: the `= Title` line and `:attr:` lines.
        if in_header:
            if ln.startswith("= ") or re.match(r"^:[^:]+:.*$", ln):
                continue
            if not ln.strip():
                continue
            in_header = False
        # Drop nav bars (xref pipe lines) at top and bottom.
        if ln.startswith("xref:") and "|" in ln:
            continue
        body.append(ln)

    text = "\n".join(body)

    # Cross-day links -> Hugo /devlog/<date>/ URLs.
    text = re.sub(
        r"xref:(\d{4}-\d{2}-\d{2})\.adoc\[([^\]]*)\]",
        lambda m: f"link:/devlog/{m.group(1)}/[{m.group(2) or m.group(1)}]",
        text,
    )
    # Research-roadmap xrefs -> plain text (that knowledge base is not published).
    text = re.sub(
        r"xref:(?:\.\./)+topics/aden-roadmap/([^\[]+?)\.adoc\[([^\]]*)\]",
        lambda m: m.group(2) or m.group(1),
        text,
    )
    # Devlog home / roadmap xrefs -> plain text (handled by the page footer).
    text = re.sub(r"xref:\.\./README\.adoc\[([^\]]*)\]", r"\1", text)
    text = re.sub(r"xref:\.\./roadmap\.adoc\[([^\]]*)\]", r"\1", text)

    # Neutralize local filesystem paths.
    for src, dst in PATH_SUBS:
        text = text.replace(src, dst)

    # Promote === round headings to == for a clean hierarchy + TOC.
    text = re.sub(r"^=== ", "== ", text, flags=re.MULTILINE)
    text = re.sub(r"^== Next$", "== What came next", text, flags=re.MULTILINE)

    # Trim leftover trailing horizontal rule / whitespace.
    text = text.rstrip()
    text = re.sub(r"\n'''\s*$", "", text)
    return text.strip()


def import_entry(date: str):
    src = DEVLOG_SRC / f"{date}.adoc"
    if not src.exists():
        raise SystemExit(f"no devlog entry at {src}")
    lines = src.read_text(encoding="utf-8").splitlines()
    summary = extract_lead(lines)
    body = clean_body(lines)

    fm = "\n".join(
        [
            "---",
            f'title: "Devlog: {date}"',
            f'slug: "{date}"',
            f"date: {date}",
            f"lastmod: {date}",
            "draft: false",
            f'summary: "{summary.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"',
            'categories: ["Devlog"]',
            'tags: ["aden", "devlog"]',
            "cover:",
            "  hidden: true",
            "ShowToc: true",
            "TocOpen: false",
            "---",
        ]
    )

    footer = (
        "\n\n'''\n"
        "[.devlog-foot]\n"
        "This is a lightly cleaned entry from the raw "
        "link:/devlog/[Aden devlog]. The polished stories that draw on these days "
        "live in the link:/series/aden/[Aden series]."
    )

    out = OUT_DIR / date / "index.adoc"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + "\n" + body + footer + "\n", encoding="utf-8")
    print(f"✓ {out.relative_to(ROOT)}  ({len(body.splitlines())} body lines)")


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit("usage: import-devlog.py <YYYY-MM-DD> | --all")
    if args[0] == "--all":
        dates = sorted(p.stem for p in DEVLOG_SRC.glob("*.adoc"))
    else:
        dates = args
    for d in dates:
        import_entry(d)


if __name__ == "__main__":
    main()
