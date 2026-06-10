#!/usr/bin/env bash
# Generate Aden knowledge graph visualization of the blog
set -e
cd "$(git rev-parse --show-toplevel)"
echo "Generating blog knowledge graph..."
aden regen ./content
mkdir -p static/graph
aden view --mode graph --unlimited --no-open --out static/graph/index.html

# Post-process: replace VSCode editor links with blog URLs
python3 - <<'PYEOF'
import re

with open('static/graph/index.html', 'r') as f:
    html = f.read()

BLOG_URL_FN = (
    "function blogUrl(n) {\n"
    "  const file = n && n.file;\n"
    "  const anchor = n && n.anchor;\n"
    "  if (!file) return null;\n"
    "  const ci = file.indexOf('/content/');\n"
    "  if (ci === -1) return null;\n"
    "  const rel = file.slice(ci + 9);\n"
    "  let p;\n"
    "  if (rel === 'glossary.adoc') p = '/glossary/';\n"
    "  else if (rel === 'about.adoc') p = '/about/';\n"
    "  else if (rel.startsWith('posts/') && rel.endsWith('/index.adoc'))\n"
    "    p = '/posts/' + rel.slice(6, -'/index.adoc'.length) + '/';\n"
    "  else if (rel.endsWith('.adoc'))\n"
    "    p = '/' + rel.slice(0, -5) + '/';\n"
    "  else return null;\n"
    "  if (!anchor) return p;\n"
    "  const hi = anchor.indexOf('#');\n"
    "  if (hi !== -1) return p + anchor.slice(hi);\n"
    "  const m = anchor.match(/\\/h\\d+(.+)$/);\n"
    "  if (m) return p + '#_' + m[1].replace(/-/g, '_');\n"
    "  return p;\n"
    "}"
)

OPEN_EDITOR_FN = "function openEditor(n) { const u = blogUrl(n); if (u) window.open(u, '_blank'); }"

html = re.sub(r'const EDITOR = "[^"]+";', "// blog link (replaces VSCode editor link)", html)
html = re.sub(r"function editorUrl\(n\) \{[^\n]+\}", lambda m: BLOG_URL_FN, html)
html = re.sub(r"function openEditor\(n\) \{[^\n]+\}", lambda m: OPEN_EDITOR_FN, html)
html = html.replace("const ed = editorUrl(n);", "const ed = blogUrl(n);")
html = html.replace("o open in editor · right-click = editor", "o open in blog · right-click = blog")
html = html.replace("open in editor →", "open in blog →")
html = html.replace("// right-click = open in editor", "// right-click = open in blog")

with open('static/graph/index.html', 'w') as f:
    f.write(html)

print("✓ Blog links patched into graph viewer")
PYEOF

echo "✓ Graph written to static/graph/index.html"
