from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from .organizer import BookmarkOrganizer

if TYPE_CHECKING:
    from .settings import LLMSettings

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Safari Bookmark Preview</title>
    <style>
      :root { --bg: #0f1216; --panel: #171b21; --text: #e9eef5; --muted: #9aa6b2; --accent: #5ee4c4; }
      * { box-sizing: border-box; }
      body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); }
      header { padding: 24px; border-bottom: 1px solid #232a33; }
      h1 { margin: 0 0 6px 0; font-size: 22px; }
      .muted { color: var(--muted); font-size: 13px; }
      .grid { display: grid; grid-template-columns: 320px 1fr; min-height: calc(100vh - 80px); }
      aside { padding: 20px; border-right: 1px solid #232a33; background: var(--panel); }
      main { padding: 20px; }
      .stat { margin: 0 0 8px 0; }
      .tree details { margin: 6px 0; padding-left: 8px; border-left: 2px solid #2a323d; }
      .tree summary { cursor: pointer; font-weight: 600; }
      .bookmark { margin: 4px 0 4px 14px; color: var(--muted); }
      .pill { display: inline-block; padding: 2px 6px; border-radius: 12px; background: #222a33; color: var(--accent); font-size: 11px; }
      .search { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #2a323d; background: #0f1216; color: var(--text); }
    </style>
  </head>
  <body>
    <header>
      <h1>Safari Bookmark Organizer — Preview</h1>
      <div class="muted">Dry-run preview of the proposed structure</div>
    </header>
    <div class="grid">
      <aside>
        <div class="stat">Total bookmarks: <span class="pill" id="total"></span></div>
        <div class="stat">Categories: <span class="pill" id="categories"></span></div>
        <div class="stat">Folders to create: <span class="pill" id="folders"></span></div>
        <div class="stat">Bookmarks to move: <span class="pill" id="moves"></span></div>
        <div style="margin-top: 16px;">
          <input class="search" id="search" placeholder="Filter by title or URL..." />
        </div>
      </aside>
      <main>
        <div class="tree" id="tree"></div>
      </main>
    </div>
    <script>
      const DATA = __DATA__;
      const plan = DATA.plan;
      const tree = DATA.tree;
      document.getElementById("total").textContent = plan.total_bookmarks;
      document.getElementById("categories").textContent = Object.keys(plan.categories).length;
      document.getElementById("folders").textContent = plan.folders_to_create.length;
      document.getElementById("moves").textContent = plan.bookmarks_to_move.length;

      const renderTree = (node, container, filter) => {
        if (!node) return;
        const matches = (text) => !filter || text.toLowerCase().includes(filter);
        if (node.type === "folder") {
          const details = document.createElement("details");
          details.open = true;
          const summary = document.createElement("summary");
          summary.textContent = node.name;
          details.appendChild(summary);
          (node.children || []).forEach(child => renderTree(child, details, filter));
          if (details.querySelector(".bookmark, details")) container.appendChild(details);
        } else if (node.type === "bookmark") {
          const label = `${node.name} — ${node.url}`;
          if (matches(label)) {
            const div = document.createElement("div");
            div.className = "bookmark";
            div.textContent = label;
            container.appendChild(div);
          }
        }
      };

      const treeContainer = document.getElementById("tree");
      const refresh = () => {
        treeContainer.innerHTML = "";
        const filter = document.getElementById("search").value.trim().toLowerCase();
        renderTree(tree, treeContainer, filter);
      };
      document.getElementById("search").addEventListener("input", refresh);
      refresh();
    </script>
  </body>
</html>
"""


def build_preview_data(
    file_path: str,
    *,
    use_llm: bool | None = None,
    taxonomy: str = "default",
    settings: LLMSettings | None = None,
) -> dict[str, Any]:
    organizer = BookmarkOrganizer(
        file_path, use_llm=use_llm, taxonomy=taxonomy, settings=settings
    )
    organizer.load_and_parse()
    all_bookmarks = organizer._collect_bookmarks()
    categorized = organizer.categorizer.categorize_all(all_bookmarks)
    tree = organizer.categorizer.suggest_folder_structure(categorized)
    plan = organizer.get_organization_plan()
    return {"tree": tree.model_dump(), "plan": plan.model_dump()}


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_response(404)
            self.end_headers()
            return
        server = cast("PreviewHTTPServer", self.server)
        payload = HTML_TEMPLATE.replace("__DATA__", json.dumps(server.preview_data))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        return


class PreviewHTTPServer(HTTPServer):
    preview_data: dict[str, Any]


def run_preview(
    file_path: str,
    *,
    use_llm: bool | None = None,
    taxonomy: str = "default",
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    settings: LLMSettings | None = None,
) -> None:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Bookmarks file not found: {path}")

    data = build_preview_data(
        str(path), use_llm=use_llm, taxonomy=taxonomy, settings=settings
    )
    server = PreviewHTTPServer((host, port), PreviewHandler)
    server.preview_data = data

    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host  # noqa: S104
    url = f"http://{browser_host}:{port}"
    logger.info("Preview server running at http://{}:{}", host, port)

    if open_browser:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    finally:
        server.server_close()
