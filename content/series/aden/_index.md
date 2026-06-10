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

### Coming up

Future posts will go deeper on individual pieces: prose joining the graph as a first-class citizen, drift detection, the graph algorithms, and broader benchmarks. Each links back to the [glossary](/glossary/) for shared terms.

> This is a [pillar page](/glossary/#_pillar_page): a hub for one topic that links down to the specific posts (the cluster) and that they link back up to. It is the same structure the rest of the site uses.
