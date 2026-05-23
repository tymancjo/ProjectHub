# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install deps (uses uv)
uv sync

# Run dev server
uv run python app.py
# OR activate venv first
source .venv/bin/activate && python app.py
```

App runs at `http://127.0.0.1:5000`. No build step.

## Architecture

Single-file app: **all backend + entire frontend HTML/CSS/JS lives in `app.py`**.

- `HTML_TEMPLATE` (line ~57) — one giant `render_template_string` holding every view
- `read_projects()` — parses `db/projects.md` by splitting on `## Project:` headers
- `save_projects_to_file()` — joins project content blocks with `\n\n` and overwrites file
- Auto-backup on save to `db/backup/` (timestamp-prefixed)

### API Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the full SPA |
| `/api/projects` | GET | Returns parsed projects as JSON |
| `/api/save-order` | POST | Accepts reordered project content array, writes file |
| `/api/toggle-todo` | POST | Toggles `TODO: [ ]` ↔ `TODO: [x]` by projectId + lineIndex |
| `/raw` | GET | Returns raw `db/projects.md` as plain text |

### Frontend Views (all in `HTML_TEMPLATE`)

Views are toggled with `setViewMode(mode)` in JS — no routing, no page reloads.

| Mode | Description |
|---|---|
| `home` | Map/dashboard view grouped by category |
| `board` | Kanban cards, drag-to-reorder via Sortable.js |
| `list` | Compact overview table |
| `todos` | Aggregated TODO list across all projects |
| `timeline` | Chronological date markers (list or grid mode) |
| `map` | Portfolio view with task progress bars |
| `network` | Project relationship graph |

Frontend libs (all CDN): Tailwind CSS, Marked.js, Sortable.js, CodeMirror 5 (editor with Vim keymap + Dracula theme).

Dark mode: toggled via `html.dark` class; CSS custom properties defined in `:root` and `html.dark`.

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
```

### Special Tags

| Tag | Effect |
|---|---|
| `#cat:name` | Groups project in Map view |
| `#_hidden` | Hides from default view (underscore prefix = hidden) |
| `#active` / `#done` / `#hold` / `#paused` / `#backlog` | Status badge in Map |
| `#load:N` | Numeric workload indicator |
| `#proj:name` | Links project to another (shown in Network view) |

## Config

`DB_PATH` env var overrides default `db/projects.md`. Copy `.env.example` to `.env` to set it.

`db/projects.md` is gitignored by default (line commented out in `.gitignore`) — uncomment to protect personal data.
