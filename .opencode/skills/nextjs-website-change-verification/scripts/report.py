"""Interactive HTML report rendering.

A self-contained single file built from the JSON report dict — issues listed
in a left sidebar; clicking one scrolls the full-page screenshot to the
issue's region and highlights it. Only critical-severity, high-confidence
findings are shown; the JSON sidecar keeps the complete data.
"""

from __future__ import annotations

import base64
import html as _html
import os

from models import (
    TYPE_BLOCKED,
    TYPE_CLIPPING,
    TYPE_COLLISION,
    TYPE_CONTRAST,
)

_ISSUE_TYPE_LABELS = {
    TYPE_COLLISION: "Element Collision",
    TYPE_CLIPPING: "Content Clipping",
    TYPE_CONTRAST: "Contrast Issue",
    TYPE_BLOCKED: "Blocked Interaction",
}


# ---------------------------------------------------------------------------
# Interactive HTML report
# ---------------------------------------------------------------------------

_HTML_STYLE = """
:root { --bg:#0f1115; --panel:#171a21; --line:#2a2f3a; --text:#e6e8ee; --dim:#9aa3b2;
        --critical:#ff5252; --high:#ff9800; --medium:#ffd54f; --low:#81c784; }
* { box-sizing:border-box; }
body { margin:0; display:flex; height:100vh; background:var(--bg); color:var(--text);
       font:14px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
#sidebar { width:400px; min-width:400px; display:flex; flex-direction:column;
           background:var(--panel); border-right:1px solid var(--line); }
#sidebar header { padding:14px 16px; border-bottom:1px solid var(--line); }
#sidebar header h1 { margin:0 0 4px; font-size:16px; }
#sidebar header .meta { color:var(--dim); font-size:12px; word-break:break-all; }
#filters { display:flex; gap:6px; flex-wrap:wrap; padding:10px 16px;
           border-bottom:1px solid var(--line); }
#filters button { background:#222734; color:var(--text); border:1px solid var(--line);
                  border-radius:12px; padding:3px 10px; font-size:12px; cursor:pointer; }
#filters button.on { background:#3b82f6; border-color:#3b82f6; }
#issues { list-style:none; margin:0; padding:0; overflow-y:auto; flex:1; }
.issue { padding:12px 16px; border-bottom:1px solid var(--line); cursor:pointer; }
.issue:hover { background:#1d222c; }
.issue.active { background:#243044; box-shadow:inset 3px 0 0 #3b82f6; }
.issue .row { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
.badge { font-size:11px; padding:1px 8px; border-radius:10px; background:#2c3444;
         color:#c7d2fe; text-transform:uppercase; letter-spacing:.4px; }
.sev { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.4px; }
.sev.critical { color:var(--critical); } .sev.high { color:var(--high); }
.sev.medium { color:var(--medium); } .sev.low { color:var(--low); }
.issue .desc { margin:0; color:var(--text); font-size:13px; }
.issue .ref { margin:6px 0 0; color:var(--dim); font-size:12px; font-family:ui-monospace,monospace;
              word-break:break-all; }
.issue .noloc { color:var(--dim); font-style:italic; font-size:12px; }
#canvas { flex:1; overflow:auto; position:relative; }
#stage { position:relative; display:inline-block; }
#stage img { display:block; }
.hl { position:absolute; border:2px solid; border-radius:3px; cursor:pointer;
      transition:box-shadow .2s; }
.hl.critical { border-color:var(--critical); background:rgba(255,82,82,.14); }
.hl.high { border-color:var(--high); background:rgba(255,152,0,.14); }
.hl.medium { border-color:var(--medium); background:rgba(255,213,79,.12); }
.hl.low { border-color:var(--low); background:rgba(129,199,132,.12); }
.hl.active { box-shadow:0 0 0 4px rgba(59,130,246,.9), 0 0 24px 6px rgba(59,130,246,.5);
             animation:pulse 1.2s ease-in-out 3; z-index:10; }
@keyframes pulse { 50% { box-shadow:0 0 0 8px rgba(59,130,246,.5), 0 0 32px 10px rgba(59,130,246,.3); } }
.hl .tag { position:absolute; top:-20px; left:-2px; font-size:11px; padding:0 6px;
           border-radius:3px 3px 0 0; background:#3b82f6; color:#fff; white-space:nowrap;
           display:none; }
.hl.active .tag { display:block; }
#empty { padding:40px; color:var(--dim); }
"""

_HTML_SCRIPT = """
function activate(id) {
  document.querySelectorAll('.issue.active, .hl.active')
      .forEach(function (e) { e.classList.remove('active'); });
  var li = document.getElementById('li-' + id);
  var hl = document.getElementById('hl-' + id);
  if (li) { li.classList.add('active'); li.scrollIntoView({block: 'nearest'}); }
  if (hl) { hl.classList.add('active'); hl.scrollIntoView({block: 'center', behavior: 'smooth'}); }
}
document.querySelectorAll('.issue').forEach(function (li) {
  li.addEventListener('click', function () { activate(li.dataset.id); });
});
document.querySelectorAll('.hl').forEach(function (hl) {
  hl.addEventListener('click', function () { activate(hl.dataset.id); });
});
document.querySelectorAll('#filters button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('#filters button').forEach(function (b) { b.classList.remove('on'); });
    btn.classList.add('on');
    var type = btn.dataset.type;
    document.querySelectorAll('.issue, .hl').forEach(function (el) {
      el.style.display = (type === 'all' || el.dataset.type === type) ? '' : 'none';
    });
  });
});
"""


def _issue_title(raw: dict) -> str:
    """Short human title for a JSON-report issue."""
    label = _ISSUE_TYPE_LABELS.get(raw.get("type", ""), str(raw.get("type", "issue")).title())
    return label


def _first_code_ref(raw: dict) -> str:
    refs = raw.get("code_references") or []
    if refs:
        file = refs[0].get("file") or ""
        line = refs[0].get("line")
        if file and line:
            return f"{file}:{line}"
        return file
    return ""


def _is_shown_in_html_report(issue: dict) -> bool:
    """The human-facing report's cut — DELIBERATELY narrower than
    ``models.is_actionable`` (which also admits "high" severity): a product
    decision (2026-07-10) limits the report to critical-severity,
    high-confidence, non-dropped findings so humans only see the defects that
    matter most. The JSON sidecar keeps everything.
    """
    return (
        issue.get("severity") == "critical"
        and issue.get("confidence_level") == "high"
        and not issue.get("dropped")
    )


def render_html_report(report: dict) -> str:
    """Render the JSON report dict as an interactive, self-contained HTML page.

    The full-page screenshot referenced by ``report['full_page_screenshot']``
    is embedded as a base64 data URI so the file can be moved or shared alone.
    Issues carrying a document-absolute ``region`` get a clickable highlight
    overlay; clicking a sidebar issue scrolls the screenshot to its region.

    Only findings passing ``_is_shown_in_html_report`` appear; everything else
    stays in the JSON sidecar.
    """
    issues = [i for i in (report.get("issues") or []) if _is_shown_in_html_report(i)]
    url = str(report.get("url", ""))
    scanned_at = str(report.get("scanned_at", ""))

    img_uri = ""
    shot = report.get("full_page_screenshot")
    if shot and os.path.isfile(shot):
        try:
            with open(shot, "rb") as fh:
                img_uri = "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")
        except OSError:
            img_uri = ""

    items: list[str] = []
    overlays: list[str] = []
    types_seen: list[str] = []
    for idx, raw in enumerate(issues):
        iid = _html.escape(str(raw.get("id") or f"issue-{idx}"), quote=True)
        typ = _html.escape(str(raw.get("type", "unknown")), quote=True)
        if typ not in types_seen:
            types_seen.append(typ)
        sev = _html.escape(str(raw.get("severity", "medium")), quote=True)
        desc = _html.escape(str(raw.get("ai_reasoning") or raw.get("reasoning") or ""))
        title = _html.escape(_issue_title(raw))
        ref = _html.escape(_first_code_ref(raw))
        region = raw.get("region")
        has_hl = bool(img_uri and isinstance(region, dict) and region.get("width"))

        parts = [
            f'<li class="issue" id="li-{iid}" data-id="{iid}" data-type="{typ}">',
            f'<div class="row"><span class="badge">{typ}</span>'
            f'<span class="sev {sev}">{sev}</span></div>',
            f'<p class="desc"><strong>{title}.</strong> {desc}</p>',
        ]
        if ref:
            parts.append(f'<p class="ref">{ref}</p>')
        if not has_hl:
            parts.append('<p class="noloc">No on-page location available.</p>')
        parts.append("</li>")
        items.append("".join(parts))

        if has_hl:
            x = float(region.get("x", 0))
            y = float(region.get("y", 0))
            w = float(region.get("width", 0))
            h = float(region.get("height", 0))
            overlays.append(
                f'<div class="hl {sev}" id="hl-{iid}" data-id="{iid}" data-type="{typ}" '
                f'style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px">'
                f'<span class="tag">{iid}</span></div>'
            )

    filters = ['<button data-type="all" class="on">All</button>'] + [
        f'<button data-type="{t}">{t}</button>' for t in types_seen
    ]

    if img_uri:
        canvas = f'<div id="stage"><img src="{img_uri}" alt="full page">{"".join(overlays)}</div>'
    else:
        canvas = '<div id="empty">No full-page screenshot was captured for this scan.</div>'

    issues_html = (
        "".join(items) if items else '<li class="issue"><p class="desc">No issues found.</p></li>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QA Report — {_html.escape(url)}</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<aside id="sidebar">
  <header>
    <h1>QA Report — {len(issues)} issue(s)</h1>
    <div class="meta">{_html.escape(url)}<br>{_html.escape(scanned_at)}</div>
  </header>
  <div id="filters">{"".join(filters)}</div>
  <ul id="issues">{issues_html}</ul>
</aside>
<main id="canvas">{canvas}</main>
<script>{_HTML_SCRIPT}</script>
</body>
</html>
"""


def write_html_report(report: dict, path: str) -> None:
    """Render and write the interactive HTML report to ``path``."""
    content = render_html_report(report)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
