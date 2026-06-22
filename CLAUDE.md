# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install deps (uses uv)
uv sync

# Option 1: launcher (starts server + menu for TUI or browser)
uv run python launcher.py

# Option 2: server only
uv run python app.py

# Option 3: TUI only (requires server already running)
uv run python tui.py
```

App runs at `http://127.0.0.1:5000`. No build step. `HUB_URL` env var overrides the default URL.

## Architecture

Three entry points, one data module:

- **`app.py`** — Flask server + entire frontend HTML/CSS/JS (`HTML_TEMPLATE` starts at line 9)
- **`db.py`** — data layer: `read_projects()`, `save_projects_to_file()`, `parse_meta()`, `toggle_todo()`, `set_status()`
- **`launcher.py`** — starts Flask subprocess, then offers TUI or browser via a Rich menu; shuts server on exit
- **`tui.py`** — Textual TUI; calls Flask API over httpx; tabs: Projects, TODOs, Ideas

### Data flow

`db.py` reads/writes `db/projects.md`. `app.py` imports from `db.py`. `tui.py` imports `parse_meta` and `set_status` from `db.py` but persists changes through the Flask API (`/api/save-order`).

Backup: every save auto-copies to `db/backup/YYYYMMDD_HHMMSS_projects.md`; keeps last 20.

### API Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the full SPA |
| `/api/projects` | GET | Returns parsed projects as JSON |
| `/api/save-order` | POST | Accepts `[content_str, …]`, writes file |
| `/api/toggle-todo` | POST | `{projectId, lineIndex}` — toggles `TODO: [ ]` ↔ `TODO: [x]` |
| `/api/update-tags` | POST | `{projectId, tagKey, tagValue}` — upserts a `#key:value` tag |
| `/api/backups` | GET | Lists available backup files |
| `/api/backup/<filename>` | GET | Returns raw backup content |
| `/api/restore` | POST | `{filename}` — restores a backup |
| `/raw` | GET | Returns raw `db/projects.md` as plain text |

### Frontend Views (all in `HTML_TEMPLATE`)

Views toggled with `setViewMode(mode)` — no routing, no page reloads.

| Mode | Description |
|---|---|
| `home` | Map/dashboard view grouped by category |
| `board` | Kanban cards, drag-to-reorder via Sortable.js |
| `list` | Compact overview table |
| `todos` | Aggregated TODO list across all projects |
| `timeline` | Chronological date markers (list or grid mode) |
| `map` | Portfolio view with task progress bars |
| `network` | Project relationship graph |

Frontend libs (all CDN): Tailwind CSS, Marked.js, Mermaid.js, Sortable.js, CodeMirror 5 (editor with Vim keymap + Dracula theme).

Dark mode: toggled via `html.dark` class; CSS custom properties defined in `:root` and `html.dark`.

### TUI Key Bindings

Projects tab: `e` edit in `$EDITOR`, `s` cycle status, `/` filter, `Esc` clear filter, `r` reload.  
TODOs tab: `Space`/`t` toggle todo, `r` reload.  
Ideas tab: `e` edit parent project, `r` reload.  
Global: `1/2/3` switch tabs, `j/k` navigate, `q` quit.

## Data Format (`db/projects.md`)

```markdown
## Project: Name
**Short Desc:** One-line summary.
---
#tag1 #cat:categoryname #active #load:100

Free-form Markdown notes.

**dd-mm-yyyy** Creates a Timeline entry.

TODO: [ ] Open task
TODO: [x] Done task

- **idea** something to explore
```

### Special Tags

| Tag | Effect |
|---|---|
| `#cat:name` | Groups project in Map/home view |
| `#_hidden` | Hides from default view (underscore prefix = hidden) |
| `#active` / `#done` / `#hold` / `#paused` / `#backlog` | Status badge |
| `#load:N` | Numeric workload indicator (0–100) |
| `#proj:name` | Links project to another (shown in Network view) |
| `#due:dd-mm-yyyy` / `#start:dd-mm-yyyy` | Date tags; upserted via `/api/update-tags` |

`**idea**` anywhere in a line (case-insensitive) surfaces it in the TUI Ideas tab and `parse_meta()`.

## Config

`DB_PATH` env var overrides default `db/projects.md`. Copy `.env.example` to `.env` to set it.

`db/projects.md` is gitignored by default (line commented out in `.gitignore`) — uncomment to protect personal data.
