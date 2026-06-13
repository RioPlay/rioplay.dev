---
title: "The Aden Series"
summary: "Everything written about Aden, the referential context compiler, in one place: what it is, how it works, and what changes as it ships."
ShowToc: false
cover:
  hidden: true
---

**Aden** turns any codebase or documentation set into a queryable [knowledge graph](/glossary/#_knowledge_graph), so humans and AI agents can assemble exactly the context a task needs. This series is the running record of that project: the ideas behind it, the architecture, and the improvements as they land.

### Start here

1. [**Introducing Aden**](/posts/introducing-aden/) covers the context problem, what Aden does, how the pipeline works, and how it has evolved.
2. [**The Graph That Audited Itself**](/posts/the-graph-that-audited-itself/) builds the interactive graph viewer, points Aden at its own codebase to find real bugs, and chases a five-cause non-determinism hunt to a reproducible 0.2.0 release.
3. [**Six Live Edges**](/posts/six-live-edges/) audits the graph model itself: most declared edge types had no emitter, `impact-diff` was walking the wrong direction, and three new types — `Tests`, `Implements`, `Mutates` — earn their names.
4. [**Prose Joins the Graph**](/posts/prose-joins-the-graph/) makes prose a first-class graph citizen: cross-document `<<refs>>`, `xref:` links, and Markdown heading anchors become bidirectional `RelatesTo` edges. 58 unresolved warnings become 0, and this blog's own glossary links become real graph edges.

### Filling in the gaps

These posts go back through the git history to cover pieces the series skipped the first time, dated to when the work actually landed:

- [**What Survives Regeneration**](/posts/what-survives-regeneration/) — `aden gen` re-parses everything; any annotation in generated output is overwritten. Intent overlays fix this with a three-way merge: a git-tracked file holds the `[human]` and `[agent]` context for a symbol and `reconcile_anchor` ensures it survives every rebuild. (Dated: 2026-06-02)
- [**What You're About to Break**](/posts/what-youre-about-to-break/) — `aden impact-diff` maps a git diff to the symbols it touches and reports the downstream blast radius before you commit, built in one session by wiring existing graph primitives to a new diff parser. (Dated: 2026-06-07)
- [**The Shape the Graph Already Had**](/posts/the-shape-the-graph-already-had/) — `aden communities` groups symbols into functional clusters using deterministic Louvain without being told the groupings. On Aden's own code it confirms the crate structure; on a foreign TypeScript codebase it separated CLI from docs. (Dated: 2026-06-07)
- [**The Empty Context Window**](/posts/the-empty-context-window/) — `ask` was routing correctly and then assembling almost nothing: a 4,115-token budget returning 22 tokens. The three-layer fix — render repairs, source hydration, and an escalation ladder — that fills the window without overrunning it. (Dated: 2026-06-09)
- [**A Green Pipeline Lies**](/posts/a-green-pipeline-lies/) — an audit day surfaced three failures every check had called success: every Python docstring dropped, every Kotlin method dropped, and a `license-check` CI job that had never run. All were found by asserting content instead of the absence of a crash. (Dated: 2026-06-12)

### Coming up

More backlog still to write: drift detection and contract healing, broader retrieval benchmarks. Each links back to the [glossary](/glossary/) for shared terms, and every post ends in a set of connections compiled from this blog's own [knowledge graph](/graph/).

> This is a [pillar page](/glossary/#_pillar_page): a hub for one topic that links down to the specific posts (the cluster) and that they link back up to. It is the same structure the rest of the site uses.
