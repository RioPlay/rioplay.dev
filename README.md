# rioplay.dev

The source for [blog.rioplay.dev](https://blog.rioplay.dev) — a knowledge-base-flavored blog about
**Aden** and AI-native developer tooling, by RioPlay.

Built with [Hugo](https://gohugo.io) + [PaperMod](https://github.com/adityatelange/hugo-PaperMod),
authored in **AsciiDoc** (the same referential, plain-text format Aden is designed to read).

## Why it's shaped like a knowledge base

The site borrows conventions from a research wiki, adapted to a clean blog:

| Element | Where | Convention |
|---|---|---|
| **Glossary** | `content/glossary.adoc` | Every recurring term defined once, with a stable anchor (`#_term`). |
| **Deep links** | every post | Posts link into the glossary with `link:/glossary/#_term[…]` instead of re-explaining. |
| **Series = topics** | `content/series/<name>/_index.md` | A pillar page per topic; posts cluster under it via `series: ["…"]` front matter. |
| **Archive** | `content/archives.md` | The full index of everything published. |
| **Sources** | foot of each post | A `[.sources]` section listing references. |

> AsciiDoc `xref:` does **not** resolve to Hugo URLs. Always cross-link with root-relative
> paths — `link:/posts/slug/[…]` and `link:/glossary/#_term[…]` — which are stable because
> permalinks are pinned in `hugo.toml`.

## Local development

Prerequisites: Hugo **extended**, Ruby + `asciidoctor` + `rouge` gems.

```bash
gem install asciidoctor rouge        # one-time
git clone --recurse-submodules <repo-url>
cd rioplay.dev
hugo server -D                       # http://localhost:1313 , -D shows drafts
```

If you cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

Build for production:

```bash
hugo --gc --minify
```

## Writing a post

Posts are **page bundles** under `content/posts/<folder>/index.adoc`. Front matter is
Hugo YAML between `---`, then AsciiDoc below. Pin a `slug` so the URL matches your links.

```asciidoc
---
title: "Your title"
slug: "your-slug"            # URL becomes /posts/your-slug/
date: 2026-01-15
draft: false
summary: "One-sentence summary used in lists and search."
series: ["Aden"]            # clusters the post under a pillar
tags: ["aden", "rust"]
ShowToc: true
---
[.lead]
Front-loaded opening sentence — the single most important claim.

[NOTE]
.The short version
====
A 40–55 word self-contained answer. Good for featured snippets.
====

== A heading that stands on its own
Body. Link terms into the glossary: link:/glossary/#_token_budget[token budget].
```

House style (from the writing research): sentence-case headings that read independently,
15–20 word sentences, active voice, a quick-answer box near the top, and a `[.sources]`
section at the foot.

## AsciiDoc styling

AsciiDoc-specific CSS (admonitions, callouts, quote blocks, glossary lists, confidence
labels) lives in `assets/css/extended/asciidoc.css`. PaperMod auto-loads anything in
`assets/css/extended/`, scoped under `.post-content`.

## Deployment — Cloudflare Pages

Two ways to wire it up; pick one.

**A. GitHub Actions (this repo ships `.github/workflows/deploy.yml`).**
Add two repository secrets, then every push to `main` builds and deploys:

- `CLOUDFLARE_API_TOKEN` — a token with the *Cloudflare Pages: Edit* permission.
- `CLOUDFLARE_ACCOUNT_ID` — your account ID.

Create the Pages project once (name `rioplay-dev`) so `wrangler pages deploy` can target it.

**B. Cloudflare Pages Git integration (no Actions).**
Connect the repo in the Cloudflare dashboard with:

- Build command: `gem install asciidoctor rouge && hugo --gc --minify`
- Output directory: `public`
- Environment variable: `HUGO_VERSION = 0.162.0`

Then point the `blog.rioplay.dev` custom domain at the Pages project in the dashboard.
```
