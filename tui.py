"""ProjectHub TUI — API-backed Textual terminal UI."""
import os
import subprocess
import tempfile

import httpx
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import (
    Footer, Header, Input, Label, ListItem, ListView, Static, TabbedContent, TabPane,
)
from textual import work
from rich.text import Text

from db import parse_meta, set_status

EDITOR = os.environ.get("EDITOR", "vim")
HUB_URL = os.environ.get("HUB_URL", "http://127.0.0.1:5000").rstrip("/")

STATUS_COLORS = {
    "active": "green",
    "done": "dim",
    "hold": "yellow",
    "paused": "yellow",
    "backlog": "blue",
    "unknown": "white",
}
STATUS_CYCLE = ["active", "hold", "paused", "backlog", "done"]


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class ApiClient:
    def __init__(self, base_url: str = HUB_URL) -> None:
        self.base = base_url
        self._client = httpx.Client(timeout=5.0)

    def get_projects(self) -> list | None:
        try:
            r = self._client.get(f"{self.base}/api/projects")
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def toggle_todo(self, project_id: str, line_index: int) -> bool:
        try:
            r = self._client.post(
                f"{self.base}/api/toggle-todo",
                json={"projectId": project_id, "lineIndex": line_index},
            )
            return r.status_code == 200
        except Exception:
            return False

    def save_order(self, contents: list[str]) -> bool:
        try:
            r = self._client.post(f"{self.base}/api/save-order", json=contents)
            return r.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrich(projects: list) -> list:
    for p in projects:
        p["meta"] = parse_meta(p["content"])
    return projects


def _load_bar(load: int, width: int = 10) -> str:
    filled = round(load / 100 * width)
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Projects view
# ---------------------------------------------------------------------------

class ProjectItem(ListItem):
    def __init__(self, project: dict) -> None:
        super().__init__()
        self.project = project

    def compose(self) -> ComposeResult:
        meta = self.project["meta"]
        status = meta["status"]
        color = STATUS_COLORS.get(status, "white")
        bar = _load_bar(meta["load"])
        cat = f"  #{meta['category']}" if meta["category"] else ""
        line = Text()
        line.append(f"{self.project['title']:<28}", style="bold")
        line.append(f" [{status}]", style=f"bold {color}")
        line.append(f"  {bar} {meta['load']:>3}%", style="dim")
        line.append(cat, style="cyan")
        yield Label(line)


class ProjectsView(Widget):
    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("e", "open_editor", "edit"),
        Binding("s", "cycle_status", "status"),
        Binding("slash", "focus_filter", "filter"),
        Binding("escape", "clear_filter", show=False),
        Binding("r", "reload", "reload"),
    ]

    def __init__(self, api: ApiClient, projects: list) -> None:
        super().__init__()
        self._api = api
        self._projects = projects
        self._filter = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-bar"):
            yield Label("Filter: ", id="filter-label")
            yield Input(placeholder="type to filter…", id="filter-input")
        yield ListView(id="project-list")

    def on_mount(self) -> None:
        self.query_one("#filter-input", Input).display = False
        self._rebuild()

    def _rebuild(self, keep: int | None = None) -> None:
        lv = self.query_one("#project-list", ListView)
        saved = keep if keep is not None else lv.index
        lv.clear()
        q = self._filter.lower()
        for p in self._projects:
            if p["meta"].get("hidden"):
                continue
            if q and q not in p["title"].lower() and q not in p["content"].lower():
                continue
            lv.append(ProjectItem(p))

        def _restore() -> None:
            count = len(list(lv.query(ListItem)))
            if count and saved is not None:
                lv.index = min(saved, count - 1)
            lv.focus()

        self.call_after_refresh(_restore)

    def set_projects(self, projects: list) -> None:
        self._projects = projects
        self._rebuild()

    def action_cursor_down(self) -> None:
        self.query_one("#project-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#project-list", ListView).action_cursor_up()

    def _selected(self):
        lv = self.query_one("#project-list", ListView)
        child = lv.highlighted_child
        return child.project if child is not None else None  # type: ignore[attr-defined]

    def action_open_editor(self) -> None:
        proj = self._selected()
        if proj is None:
            return
        lv = self.query_one("#project-list", ListView)
        saved_idx = lv.index
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(proj["content"])
            tmp = f.name
        with self.app.suspend():
            subprocess.run([EDITOR, tmp])
        with open(tmp, "r", encoding="utf-8") as f:
            new_content = f.read().strip()
        os.unlink(tmp)
        if new_content and new_content != proj["content"]:
            proj["content"] = new_content
            proj["meta"] = parse_meta(new_content)
            self._api.save_order([p["content"] for p in self._projects])
        self._rebuild(keep=saved_idx)

    def action_cycle_status(self) -> None:
        proj = self._selected()
        if proj is None:
            return
        lv = self.query_one("#project-list", ListView)
        saved_idx = lv.index
        current = proj["meta"]["status"]
        try:
            idx = STATUS_CYCLE.index(current)
        except ValueError:
            idx = -1
        new_status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]
        updated = set_status(self._projects, proj["id"], new_status)
        self._projects[:] = updated
        for p in self._projects:
            p["meta"] = parse_meta(p["content"])
        self._api.save_order([p["content"] for p in self._projects])
        self._rebuild(keep=saved_idx)

    def action_focus_filter(self) -> None:
        inp = self.query_one("#filter-input", Input)
        inp.display = True
        inp.focus()

    def action_clear_filter(self) -> None:
        inp = self.query_one("#filter-input", Input)
        inp.value = ""
        inp.display = False
        self._filter = ""
        self._rebuild()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter = event.value
        self._rebuild()

    def action_reload(self) -> None:
        self.app.action_reload()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# TODOs view
# ---------------------------------------------------------------------------

class TodoItem(ListItem):
    def __init__(self, todo: dict, project: dict) -> None:
        super().__init__()
        self.todo = todo
        self.project = project

    def compose(self) -> ComposeResult:
        done = self.todo["done"]
        check = "[x]" if done else "[ ]"
        line = Text()
        line.append(check + " ", style="green" if done else "white")
        line.append(f"{self.todo['text']:<42}", style="dim" if done else "bold")
        line.append(f"  ← {self.project['title']}", style="dim cyan")
        yield Label(line)


class TodosView(Widget):
    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("space", "toggle", "toggle"),
        Binding("t", "toggle", show=False),
        Binding("r", "reload", "reload"),
    ]

    def __init__(self, api: ApiClient, projects: list) -> None:
        super().__init__()
        self._api = api
        self._projects = projects

    def compose(self) -> ComposeResult:
        yield ListView(id="todo-list")

    def on_mount(self) -> None:
        self._rebuild()

    def _rebuild(self, keep: int | None = None) -> None:
        lv = self.query_one("#todo-list", ListView)
        saved = keep if keep is not None else lv.index
        lv.clear()
        for p in self._projects:
            if p["meta"].get("hidden"):
                continue
            for todo in p["meta"]["todos"]:
                lv.append(TodoItem(todo, p))

        def _restore() -> None:
            count = len(list(lv.query(ListItem)))
            if count and saved is not None:
                lv.index = min(saved, count - 1)
            lv.focus()

        self.call_after_refresh(_restore)

    def set_projects(self, projects: list) -> None:
        self._projects = projects
        self._rebuild()

    def action_cursor_down(self) -> None:
        self.query_one("#todo-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#todo-list", ListView).action_cursor_up()

    def action_toggle(self) -> None:
        lv = self.query_one("#todo-list", ListView)
        child = lv.highlighted_child
        if child is None:
            return
        item: TodoItem = child  # type: ignore[assignment]
        saved_idx = lv.index
        ok = self._api.toggle_todo(item.project["id"], item.todo["line_index"])
        if ok:
            fresh = self._api.get_projects()
            if fresh:
                self._projects[:] = _enrich(fresh)
        self._rebuild(keep=saved_idx)

    def action_reload(self) -> None:
        self.app.action_reload()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Ideas view
# ---------------------------------------------------------------------------

class IdeaItem(ListItem):
    def __init__(self, idea: str, project: dict) -> None:
        super().__init__()
        self.idea = idea
        self.project = project

    def compose(self) -> ComposeResult:
        line = Text()
        line.append("  ", style="yellow")
        line.append(f"{self.idea:<50}", style="bold")
        line.append(f"  ← {self.project['title']}", style="dim cyan")
        yield Label(line)


class IdeasView(Widget):
    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("e", "open_editor", "edit"),
        Binding("r", "reload", "reload"),
    ]

    def __init__(self, api: ApiClient, projects: list) -> None:
        super().__init__()
        self._api = api
        self._projects = projects

    def compose(self) -> ComposeResult:
        yield ListView(id="ideas-list")

    def on_mount(self) -> None:
        self._rebuild()

    def _rebuild(self, keep: int | None = None) -> None:
        lv = self.query_one("#ideas-list", ListView)
        saved = keep if keep is not None else lv.index
        lv.clear()
        for p in self._projects:
            if p["meta"].get("hidden"):
                continue
            for idea in p["meta"]["ideas"]:
                lv.append(IdeaItem(idea, p))

        def _restore() -> None:
            count = len(list(lv.query(ListItem)))
            if count and saved is not None:
                lv.index = min(saved, count - 1)
            lv.focus()

        self.call_after_refresh(_restore)

    def set_projects(self, projects: list) -> None:
        self._projects = projects
        self._rebuild()

    def action_cursor_down(self) -> None:
        self.query_one("#ideas-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#ideas-list", ListView).action_cursor_up()

    def action_open_editor(self) -> None:
        lv = self.query_one("#ideas-list", ListView)
        child = lv.highlighted_child
        if child is None:
            return
        item: IdeaItem = child  # type: ignore[assignment]
        proj = item.project
        saved_idx = lv.index
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(proj["content"])
            tmp = f.name
        with self.app.suspend():
            subprocess.run([EDITOR, tmp])
        with open(tmp, "r", encoding="utf-8") as f:
            new_content = f.read().strip()
        os.unlink(tmp)
        if new_content and new_content != proj["content"]:
            proj["content"] = new_content
            proj["meta"] = parse_meta(new_content)
            self._api.save_order([p["content"] for p in self._projects])
        self._rebuild(keep=saved_idx)

    def action_reload(self) -> None:
        self.app.action_reload()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class ProjectHubApp(App):
    CSS = """
    Screen { background: $surface; }

    ProjectsView, TodosView, IdeasView { height: 1fr; }

    #filter-bar {
        height: 3;
        padding: 0 1;
        align: left middle;
    }
    #filter-label { margin-top: 1; color: $text-muted; }
    #filter-input { width: 32; }

    ListView {
        height: 1fr;
        border: round $primary-darken-2;
    }
    ListItem { padding: 0 1; }
    ListItem:hover { background: $boost; }
    ListItem.-highlighted { background: $accent 30%; }

    TabbedContent { height: 1fr; }
    TabPane { height: 1fr; padding: 0; }

    #status-bar {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("1", "switch_tab('projects')", "Projects"),
        Binding("2", "switch_tab('todos')", "TODOs"),
        Binding("3", "switch_tab('ideas')", "Ideas"),
        Binding("r", "reload", "Reload"),
        Binding("q", "quit", "Quit"),
    ]

    TITLE = "ProjectHub TUI"

    def __init__(self) -> None:
        super().__init__()
        self._api = ApiClient()
        self._projects: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Connecting to server…", id="status-bar")
        with TabbedContent(initial="projects"):
            with TabPane("Projects [1]", id="projects"):
                yield ProjectsView(self._api, self._projects)
            with TabPane("TODOs [2]", id="todos"):
                yield TodosView(self._api, self._projects)
            with TabPane("Ideas [3]", id="ideas"):
                yield IdeasView(self._api, self._projects)
        yield Footer()

    def on_mount(self) -> None:
        self._do_load()

    @work(thread=True)
    def _do_load(self) -> None:
        data = self._api.get_projects()
        self.call_from_thread(self._on_loaded, data)

    def _on_loaded(self, data: list | None) -> None:
        bar = self.query_one("#status-bar", Static)
        if data is None:
            bar.update(
                f"[red]Server unreachable[/red] — start with: uv run python app.py  "
                f"(HUB_URL={HUB_URL})"
            )
            return
        self._projects[:] = _enrich(data)
        bar.update(
            f"[green]Connected[/green]  {len(self._projects)} projects  "
            f"[dim]{HUB_URL}[/dim]"
        )
        self._broadcast(self._projects)

    def _broadcast(self, projects: list) -> None:
        for v in self.query(ProjectsView):
            v.set_projects(projects)
        for v in self.query(TodosView):
            v.set_projects(projects)
        for v in self.query(IdeasView):
            v.set_projects(projects)

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        for lv in event.pane.query(ListView):
            lv.focus()
            break

    def action_reload(self) -> None:
        self.query_one("#status-bar", Static).update("Reloading…")
        self._do_load()


def main() -> None:
    ProjectHubApp().run()


if __name__ == "__main__":
    main()
