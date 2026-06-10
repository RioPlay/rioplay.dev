#!/usr/bin/env bash
# Generate Aden knowledge graph visualization of the blog
set -e
cd "$(git rev-parse --show-toplevel)"
echo "Generating blog knowledge graph..."
aden regen ./content
mkdir -p static/graph
aden view --mode graph --unlimited --no-open --out static/graph/index.html
echo "✓ Graph written to static/graph/index.html"
