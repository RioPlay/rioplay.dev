---
title: "The Aden Series"
summary: "Everything written about Aden, the referential context compiler, in one place: what it is, how it works, and what changes as it ships."
ShowToc: false
cover:
  hidden: true
---

**Aden** turns any codebase or documentation set into a queryable [knowledge graph](/glossary/#_knowledge_graph), so humans and AI agents can assemble exactly the context a task needs. This series is the running record of that project: the ideas behind it, the architecture, and the improvements as they land.

The posts below are in reading order. Start at the top with [**Introducing Aden**](/posts/introducing-aden/) (what Aden is, how it works, and how it came to be), then work straight down the list.

The two most recent entries are an in-progress research log on whether a computed language graph can beat a neural retrieval baseline. [**Don't Take the Dictionary's Word for It**](/posts/dont-take-the-dictionarys-word-for-it/) is the honest account of the negative results and a measurement leak I had to catch and undo. [**Two Graphs, One Funnel**](/posts/two-graphs-one-funnel/) is where it resolves: not one graph that wins, but two graphs that do different jobs (the corpus's own structure for code, an English dictionary for prose) auto-gated into one funnel, with the durable win staying structural. That line of work is ongoing, and updates will be posted as it is compiled and completed.

Still ahead: sense-splitting the language graph (one node per sense, not per spelling), and drift detection and contract healing, as that research continues.

> This is a [pillar page](/glossary/#_pillar_page): a hub for one topic that links down to the specific posts (the cluster) and that they link back up to. It is the same structure the rest of the site uses.
