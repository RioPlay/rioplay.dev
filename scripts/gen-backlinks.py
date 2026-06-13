#!/usr/bin/env python3
# Copyright (c) 2026 Ernest Hamblen <rioplay@rioplay.dev>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Aden-driven backlink generator.
#
# The blog documents Aden, a referential context compiler that turns prose and
# code into a typed knowledge graph. This script turns that graph back onto the
# blog itself and emits a Hugo data file the layouts render as "Referenced by"
# and "Concepts used here" rails. The blog's own navigation is compiled from the
# cross-references the author actually wrote. Nothing is hand-maintained: edit a
# link in a post, rerun, and the rails update.
#
# Two sources are merged, by necessity:
#   1. Aden's RelatesTo edges (the authoritative semantic graph). Aden models the
#      cross-document `<<anchor>>` / `xref:` references — which on this blog are
#      the glossary-term citations (post <-> glossary) and the term-to-term web.
#      This is the on-brand half: the concept graph is genuinely Aden's.
#   2. A scan of `link:/...[]` URL macros in the AsciiDoc sources. Post-to-post
#      links must use absolute Hugo URLs (`link:/posts/slug/`) because `xref:`
#      does not resolve to a published URL — so Aden does not see them as edges.
#      We harvest them here so page-to-page backlinks are complete. (This gap is
#      the same one the research-wiki's connections.md noted; it is a candidate
#      for a future Aden feature: model `link:` URL macros as RelatesTo edges.)
#
# Usage:  python3 scripts/gen-backlinks.py          (writes data/backlinks.json)
#         python3 scripts/gen-backlinks.py --check   (verify it is up to date)

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "data" / "backlinks.json"

# Edge types that represent an authored cross-reference between documents.
# PartOf / Contains are structural (module<->symbol) and are not backlinks.
PROSE_EDGE = "RelatesTo"


def blog_url(file_path: str, anchor: str | None):
    """Map an Aden node (source file + anchor) to a (page_url, fragment) pair.

    Mirrors the blogUrl() logic baked into the graph viewer (scripts/gen-graph.sh)
    so the two surfaces agree on where a node lives on the published site.
    """
    ci = file_path.find("/content/")
    if ci == -1:
        return None, None
    rel = file_path[ci + len("/content/") :]
    if rel == "glossary.adoc":
        page = "/glossary/"
    elif rel == "about.adoc":
        page = "/about/"
    elif rel.startswith("posts/") and rel.endswith("/index.adoc"):
        page = "/posts/" + rel[len("posts/") : -len("/index.adoc")] + "/"
    elif rel.startswith("devlog/") and rel.endswith("/index.adoc"):
        page = "/devlog/" + rel[len("devlog/") : -len("/index.adoc")] + "/"
    elif rel.endswith(".adoc"):
        page = "/" + rel[:-len(".adoc")] + "/"
    else:
        return None, None

    fragment = None
    if anchor:
        hi = anchor.find("#")
        if hi != -1:
            fragment = anchor[hi:]
        else:
            m = re.search(r"/h\d+(.+)$", anchor)
            if m:
                fragment = "#_" + m.group(1).replace("-", "_")
    return page, fragment


def read_title(file_path: str) -> str | None:
    """Pull the title from a content file's YAML front matter."""
    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        m = re.match(r'\s*title:\s*"?(.*?)"?\s*$', line)
        if m:
            return m.group(1)
    return None


def is_draft(file_path: str) -> bool:
    """True if a content file's YAML front matter sets draft: true."""
    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return False
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    for line in text[3:end].splitlines():
        m = re.match(r"\s*draft:\s*(true|false)\b", line, re.IGNORECASE)
        if m:
            return m.group(1).lower() == "true"
    return False


def parse_glossary_terms() -> dict[str, str]:
    """anchor (e.g. _blast_radius) -> human term name, from the glossary source."""
    terms: dict[str, str] = {}
    gloss = CONTENT / "glossary.adoc"
    if not gloss.exists():
        return terms
    # Matches:  [[_blast_radius]]Blast radius::
    pat = re.compile(r"\[\[(_[a-z0-9_]+)\]\]\s*(.+?)::")
    for line in gloss.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            terms[m.group(1)] = m.group(2).strip()
    return terms


def page_url_for_source(file_path: str):
    """Page URL for a content source file (the *source* side of a link)."""
    p = Path(file_path)
    try:
        rel = p.relative_to(CONTENT).as_posix()
    except ValueError:
        return None
    if rel == "glossary.adoc":
        return "/glossary/"
    if rel == "about.adoc":
        return "/about/"
    if rel.startswith("posts/") and rel.endswith("/index.adoc"):
        return "/posts/" + rel[len("posts/") : -len("/index.adoc")] + "/"
    if rel.startswith("devlog/") and rel.endswith("/index.adoc"):
        return "/devlog/" + rel[len("devlog/") : -len("/index.adoc")] + "/"
    if rel.endswith(".adoc"):
        return "/" + rel[:-len(".adoc")] + "/"
    return None


# link:/posts/slug/[label]  ·  link:/glossary/#_term[label]  ·  link:/about/[label]
LINK_MACRO = re.compile(r"link:(/[A-Za-z0-9/_#-]+?)(?:\[)")


def scan_link_macros() -> list[tuple[str, str, str | None]]:
    """Harvest authored `link:/...` cross-references from the AsciiDoc sources.

    Returns (src_page, dst_page, fragment) tuples. These are the page-to-page
    edges Aden does not model (URL macros, not <<anchor>> refs).
    """
    edges: list[tuple[str, str, str | None]] = []
    for src in sorted(CONTENT.rglob("*.adoc")):
        src_page = page_url_for_source(str(src))
        if not src_page:
            continue
        text = src.read_text(encoding="utf-8")
        for m in LINK_MACRO.finditer(text):
            target = m.group(1)
            frag = None
            hi = target.find("#")
            if hi != -1:
                frag, target = target[hi:], target[:hi]
            if not target.endswith("/"):
                target += "/"
            # Only internal content pages we publish; ignore /tags etc. silently.
            if target in ("/glossary/", "/about/") or target.startswith("/posts/") or (target.startswith("/devlog/") and target != "/devlog/"):
                edges.append((src_page, target, frag))
    return edges


def load_graph() -> dict:
    proc = subprocess.run(
        ["aden", "viz", "--mode", "graph", "--full", "-j", "-p", str(CONTENT)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"aden viz failed (exit {proc.returncode})")
    return json.loads(proc.stdout)


def build() -> dict:
    graph = load_graph()
    nodes = {n["id"]: n for n in graph["nodes"]}
    glossary_terms = parse_glossary_terms()

    # Draft pages must never appear in the rails: Hugo does not publish them, so a
    # backlink into or out of a draft would point at (or come from) a 404.
    draft_pages = {
        url
        for src in CONTENT.rglob("*.adoc")
        if is_draft(str(src))
        for url in (page_url_for_source(str(src)),)
        if url
    }

    # url -> source title (first node we see for that page wins; they agree)
    titles: dict[str, str] = {}
    for n in nodes.values():
        page, _ = blog_url(n.get("file") or "", n.get("anchor"))
        if page and page not in titles:
            t = read_title(n.get("file") or "")
            if t:
                titles[page] = t

    # Aggregate RelatesTo edges to page level.
    # referenced_by[page] = set of OTHER content pages that link into it
    # concepts[page]      = set of glossary fragments this page links to
    # related[page]       = set of OTHER posts this page links to (outgoing)
    referenced_by: dict[str, set] = {}
    concepts: dict[str, set] = {}
    related: dict[str, set] = {}
    # term_used_in[fragment] = set of pages that reference that glossary term
    term_used_in: dict[str, set] = {}

    for e in graph.get("edges", []):
        if e.get("type") != PROSE_EDGE:
            continue
        src = nodes.get(e["from"])
        dst = nodes.get(e["to"])
        if not src or not dst:
            continue
        src_page, _ = blog_url(src.get("file") or "", src.get("anchor"))
        dst_page, dst_frag = blog_url(dst.get("file") or "", dst.get("anchor"))
        if not src_page or not dst_page or src_page == dst_page:
            continue
        if src_page in draft_pages or dst_page in draft_pages:
            continue

        if dst_page == "/glossary/" and dst_frag:
            concepts.setdefault(src_page, set()).add(dst_frag)
            term_used_in.setdefault(dst_frag, set()).add(src_page)
        else:
            referenced_by.setdefault(dst_page, set()).add(src_page)
            if dst_page.startswith("/posts/") or dst_page.startswith("/devlog/"):
                related.setdefault(src_page, set()).add(dst_page)

    # Merge the `link:/...` URL macros Aden does not model (page-to-page edges).
    for src_page, dst_page, frag in scan_link_macros():
        if src_page == dst_page:
            continue
        if src_page in draft_pages or dst_page in draft_pages:
            continue
        if dst_page == "/glossary/" and frag:
            concepts.setdefault(src_page, set()).add(frag)
            term_used_in.setdefault(frag, set()).add(src_page)
        else:
            referenced_by.setdefault(dst_page, set()).add(src_page)
            if dst_page.startswith("/posts/") or dst_page.startswith("/devlog/"):
                related.setdefault(src_page, set()).add(dst_page)

    def page_entries(pages: set) -> list:
        out = []
        for p in sorted(pages):
            out.append({"url": p, "title": titles.get(p, p)})
        return out

    def concept_entries(frags: set) -> list:
        out = []
        for f in sorted(frags):
            anchor = f[1:]  # drop leading '#'
            out.append(
                {
                    "url": "/glossary/" + f,
                    "term": glossary_terms.get(anchor, anchor.lstrip("_").replace("_", " ")),
                }
            )
        return out

    data: dict[str, dict] = {}
    all_pages = set(referenced_by) | set(concepts) | set(related)
    for page in sorted(all_pages):
        entry = {}
        if page in referenced_by:
            entry["referenced_by"] = page_entries(referenced_by[page])
        if page in concepts:
            entry["concepts"] = concept_entries(concepts[page])
        if page in related:
            entry["related"] = page_entries(related[page])
        if entry:
            data[page] = entry

    # Per-term "used in" for the glossary page.
    terms_block = {}
    for frag in sorted(term_used_in):
        anchor = frag[1:]
        terms_block[anchor] = {
            "term": glossary_terms.get(anchor, anchor.lstrip("_").replace("_", " ")),
            "used_in": page_entries(term_used_in[frag]),
        }
    if terms_block:
        data.setdefault("/glossary/", {})["terms"] = terms_block

    return data


def main():
    check = "--check" in sys.argv
    data = build()
    rendered = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            sys.stderr.write("data/backlinks.json is stale — run scripts/gen-backlinks.py\n")
            raise SystemExit(1)
        print("data/backlinks.json is up to date")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    pages = len([k for k in data if k != "/glossary/" or "referenced_by" in data[k]])
    edges = sum(
        len(v.get("referenced_by", [])) + len(v.get("concepts", [])) for v in data.values()
    )
    print(f"✓ data/backlinks.json — {len(data)} pages, {edges} aggregated backlinks")


if __name__ == "__main__":
    main()
