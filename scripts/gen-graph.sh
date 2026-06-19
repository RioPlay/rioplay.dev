#!/usr/bin/env bash
# Generate the public Aden knowledge-graph visualization of the blog.
#
# Aden's `view` bakes the FULL graph into the HTML — one node per heading, plus
# the repo's own script source, each carrying a raw `snippet`, an absolute file
# path, and line numbers, plus a git-replay `activity` timeline. That is far more
# than a public page should ship. So after generating the viewer we REPLACE its
# embedded DATA with a sanitized, page-and-term-relevancy-only graph built from
# data/backlinks.json (itself compiled from Aden's RelatesTo edges + the blog's
# link macros). Result: one node per published page + one per glossary term,
# relevancy edges only — no snippets, no file paths, no headings, no script code,
# no drafts. A privacy gate at the end fails the build if any of those leak.
set -e
cd "$(git rev-parse --show-toplevel)"
echo "Generating blog knowledge graph..."
aden regen ./content
mkdir -p static/graph
aden view --mode graph --unlimited --no-open --out static/graph/index.html

# backlinks.json is the sanitized, page-level source of truth for the graph.
python3 scripts/gen-backlinks.py >/dev/null

python3 - <<'PYEOF'
import json
import re
import sys
from collections import Counter

PATHS = ['static/graph/index.html', 'static/graph/index-3d.html']
DRAFT_GUARD = 'the-merge-engine-that-landed'  # current draft slug; see content/posts/

# ── Build the sanitized page+term graph from backlinks.json ──────────────────
bl = json.load(open('data/backlinks.json'))

titles = {}
def learn(u, t):
    if t and u not in titles:
        titles[u] = t
for url, e in bl.items():
    for k in ('referenced_by', 'related'):
        for it in e.get(k, []):
            learn(it['url'], it['title'])
    for _, t in e.get('terms', {}).items():
        for it in t.get('used_in', []):
            learn(it['url'], it['title'])

def group_of(url):
    if url.startswith('/posts/'):  return 'posts'
    if url.startswith('/devlog/'): return 'devlog'
    if url == '/about/':           return 'about'
    if url == '/glossary/':        return 'glossary'
    return 'page'

nodes = {}
def add_page(url):
    nodes.setdefault(url, {'id': url, 'url': url, 'label': titles.get(url, url),
                           'group': group_of(url), 'kind': 'Page'})
def add_term(url, term):
    nodes.setdefault(url, {'id': url, 'url': url, 'label': term,
                           'group': 'term', 'kind': 'Term'})

edges = set()
for url, e in bl.items():
    if url == '/glossary/':
        for anc, t in e.get('terms', {}).items():
            turl = '/glossary/#' + anc
            add_term(turl, t.get('term', anc))
            for it in t.get('used_in', []):
                add_page(it['url']); edges.add((it['url'], turl))
    for it in e.get('related', []):
        add_page(url); add_page(it['url']); edges.add((url, it['url']))
    for it in e.get('referenced_by', []):
        add_page(it['url']); add_page(url); edges.add((it['url'], url))
    for it in e.get('concepts', []):
        add_page(url); add_term(it['url'], it['term']); edges.add((url, it['url']))

edges = {(a, b) for (a, b) in edges if a != b}
deg = Counter()
for a, b in edges:
    deg[a] += 1; deg[b] += 1
groups = sorted({n['group'] for n in nodes.values()})
gid = {g: i for i, g in enumerate(groups)}
gsize = Counter(n['group'] for n in nodes.values())

node_list = [{
    'id': n['id'], 'label': n['label'], 'group': n['group'], 'kind': n['kind'],
    'url': n['url'], 'anchor': '', 'community': gid[n['group']], 'degree': deg[n['id']],
} for n in nodes.values()]
edge_list = [{'from': a, 'to': b, 'type': 'RelatesTo'} for a, b in sorted(edges)]
all_anchors = [{'a': n['id'], 'd': deg[n['id']], 'g': n['group'], 'k': n['kind'], 'n': n['label']}
               for n in nodes.values()]
communities = [{'id': gid[g], 'label': g, 'size': gsize[g]} for g in groups]

# ── DATA object extraction (brace-scan, string-aware) ────────────────────────
def extract_data(html):
    i = html.index('const DATA =') + len('const DATA =')
    s = html[i:]
    depth = 0; instr = False; esc = False; start = None
    for j, c in enumerate(s):
        if instr:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': instr = False
            continue
        if c == '"': instr = True
        elif c == '{':
            if depth == 0: start = j
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i + start, i + j + 1, s[start:j + 1]
    raise SystemExit('FATAL: could not find DATA object')

# blogUrl prefers the node's own url (our sanitized nodes carry it); falls back
# to anchor parsing for any node that still has one.
BLOG_URL_FN = r'''function blogUrl(n) {
  if (n && n.url) return n.url;
  const src = (n && n.file) || (n && n.anchor) || '';
  const ci = src.indexOf('content/');
  if (ci === -1) return null;
  const after = src.slice(ci + 'content/'.length);
  const a = after.indexOf('.adoc');
  if (a === -1) return null;
  const rel = after.slice(0, a + 5);
  const tail = after.slice(a + 5);
  let p;
  if (rel === 'glossary.adoc') p = '/glossary/';
  else if (rel === 'about.adoc') p = '/about/';
  else if (rel.startsWith('posts/') && rel.endsWith('/index.adoc')) p = '/posts/' + rel.slice(6, -11) + '/';
  else if (rel.startsWith('devlog/') && rel.endsWith('/index.adoc')) p = '/devlog/' + rel.slice(7, -11) + '/';
  else p = '/' + rel.slice(0, -5) + '/';
  if (!tail) return p;
  if (tail.charAt(0) === '#') return p + tail;
  const m = tail.match(/\/h\d+(.+)$/);
  if (m) return p + '#_' + m[1].replace(/-/g, '_');
  return p;
}
'''

def patch_links(html):
    if 'function blogUrl' not in html:
        html = html.replace('function editorUrl(n)', BLOG_URL_FN + 'function editorUrl(n)', 1)
    html, n_edit = re.subn(r'function editorUrl\(n\) \{.*?\n\}',
                           'function editorUrl(n) { return blogUrl(n); }',
                           html, count=1, flags=re.DOTALL)
    html = re.sub(r"function openEditor\(n\) \{[^\n]*\}",
                  "function openEditor(n) { const u = blogUrl(n); if (u) window.open(u, '_blank'); }",
                  html, count=1)
    html = html.replace("const ed = editorUrl(n);", "const ed = blogUrl(n);")
    # 4) Reader UX: a plain left-click on a node opens its blog page (new tab).
    #    The stock viewer uses left-click to focus and only right-click to open,
    #    which reads as "clicking does not go to the doc." Fall back to the
    #    original focus behaviour for any node without a resolvable URL.
    #    2D viewer binds onNodeClick(onClick); 3D binds onNodeClick(focusOn).
    html = html.replace(
        "onNodeClick(onClick)",
        "onNodeClick(function (n) { var u = blogUrl(n); if (u) { window.open(u, '_blank'); } else { onClick(n); } })",
    )
    html = html.replace(
        "onNodeClick(focusOn)",
        "onNodeClick(function (n) { var u = blogUrl(n); if (u) { window.open(u, '_blank'); } else { focusOn(n); } })",
    )
    return html, n_edit

for path in PATHS:
    try:
        html = open(path).read()
    except FileNotFoundError:
        continue
    a, b, obj = extract_data(html)
    data = json.loads(obj)
    # Replace the content-bearing graph with the sanitized page+term graph and
    # neutralize the other content/leak-bearing keys.
    data['nodes'] = node_list
    data['edges'] = edge_list
    data['all_anchors'] = all_anchors
    data['all_anchors_total'] = len(node_list)
    data['communities'] = communities
    data['activity'] = []                  # drop git-replay timeline (per-commit anchors)
    data['shown_nodes'] = len(node_list)
    data['total_nodes'] = len(node_list)
    data.pop('git_hash', None)             # internal build metadata — not needed publicly
    html = html[:a] + ' ' + json.dumps(data) + html[b:]
    html, n_edit = patch_links(html)

    # ── Privacy + correctness gate ──────────────────────────────────────────
    problems = []
    if '"snippet"' in html:                 problems.append('raw snippets still present')
    if '/home/' in html:                    problems.append('absolute filesystem path still present')
    if DRAFT_GUARD in html:                 problems.append('draft content still present')
    if 'function blogUrl' not in html:      problems.append('blogUrl() not injected')
    if n_edit != 1:                         problems.append('editorUrl() not rerouted')
    if problems:
        sys.exit(f"FATAL: graph sanitization failed for {path}:\n  - " + "\n  - ".join(problems))
    open(path, 'w').write(html)
    print(f"✓ {path}: {len(node_list)} page/term nodes, {len(edge_list)} relevancy edges "
          f"(snippets/paths/scripts/headings/draft stripped)")
PYEOF

echo "✓ Graph written to static/graph/index.html"
