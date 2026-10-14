import os
import re
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_PATH", os.path.join("db", "projects.md"))
DB_DIR = os.path.dirname(os.path.abspath(DB_FILE))

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

INITIAL_CONTENT = """## Project: Getting Started
**Short Desc:** Welcome to your new project board.
---
#tutorial #setup
Welcome! You can edit this text directly. Any word starting with a hash becomes a tag automatically.

## Project: Future Ideas
**Short Desc:** Things to build later.
---
#backlog #ideas #cat:engineering
### UI Roadmap
TODO: [ ] Add a calendar view
TODO: [ ] Integration with Jira/GitHub
TODO: [x] Dark mode toggle

**14-05-2026** initial roadmap written

#### Technical Debt
- Refactor the CSS into a separate file.
"""

STATUS_TAGS = ("active", "done", "hold", "paused", "backlog")
TT_MARKER = "## @TimeTrack"


def _split_content(text):
    """Split file text into (projects_text, timetrack_text). timetrack_text includes the marker line or is ''."""
    m = re.search(r'^' + re.escape(TT_MARKER) + r'[ \t]*$', text, re.MULTILINE)
    if not m:
        return text, ""
    return text[:m.start()], text[m.start():].strip()


def _read_raw():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write(INITIAL_CONTENT)
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return f.read()


def read_projects():
    content, _ = _split_content(_read_raw())
    raw_sections = re.split(r'(?=## Project:)', content)
    projects = []
    for section in raw_sections:
        if not section.strip():
            continue
        lines = section.strip().split('\n')
        title = lines[0].replace('## Project:', '').strip()
        clean_id = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())
        projects.append({"id": clean_id, "title": title, "content": section.strip()})
    return projects


def save_projects_to_file(projects_data, timetrack_text=None):
    """Write projects. timetrack_text=None keeps the existing @TimeTrack block."""
    if timetrack_text is None:
        timetrack_text = _split_content(_read_raw())[1] if os.path.exists(DB_FILE) else ""
    if os.path.exists(DB_FILE):
        backup_dir = os.path.join(DB_DIR, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_FILE, os.path.join(backup_dir, f"{ts}_projects.md"))
        try:
            backups = sorted(f for f in os.listdir(backup_dir) if f.endswith("_projects.md"))
            for old in backups[:-20]:
                os.remove(os.path.join(backup_dir, old))
        except OSError:
            pass
    content = "\n\n".join(projects_data)
    if timetrack_text.strip():
        content += "\n\n" + timetrack_text.strip() + "\n"
    tmp_path = DB_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, DB_FILE)


def read_timetrack():
    """Return [{ts, project, category, load}] from the @TimeTrack section."""
    _, tt = _split_content(_read_raw())
    rows = []
    for line in tt.split('\n')[1:]:
        parts = [p.strip() for p in line.strip().lstrip('-').split('|')]
        if len(parts) != 4 or not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', parts[0]):
            continue
        try:
            load = float(parts[3])
        except ValueError:
            continue
        rows.append({"ts": parts[0], "project": parts[1], "category": parts[2], "load": load})
    return rows


def _write_timetrack(rows):
    lines = [TT_MARKER] + [
        f"- {r['ts']} | {r['project']} | {r['category']} | {r['load']:g}" for r in rows
    ]
    projects = read_projects()
    save_projects_to_file([p["content"] for p in projects], "\n".join(lines) if rows else "")


def append_timetrack(items, ts=None):
    """Append one snapshot. items: [{project, category, load}]. Returns timestamp used."""
    ts = ts or datetime.now().strftime("%Y-%m-%d %H:%M")
    clean = lambda v: str(v).replace('|', '/').replace('\n', ' ').strip()
    rows = [r for r in read_timetrack() if r["ts"] != ts]
    for it in items:
        rows.append({
            "ts": ts,
            "project": clean(it.get("project", "")) or "?",
            "category": clean(it.get("category", "")) or "—",
            "load": float(it.get("load", 0)),
        })
    _write_timetrack(rows)
    return ts


def delete_timetrack(ts):
    _write_timetrack([r for r in read_timetrack() if r["ts"] != ts])


def parse_meta(content: str) -> dict:
    """Extract tags, status, load, todos, ideas from project content string."""
    tags = re.findall(r'#(\w[\w:]*)', content)
    status = "unknown"
    for tag in tags:
        if tag in STATUS_TAGS:
            status = tag
            break
    load_match = re.search(r'#load:(\d+)', content)
    load = int(load_match.group(1)) if load_match else 0
    cat_match = re.search(r'#cat:(\w+)', content)
    category = cat_match.group(1) if cat_match else ""
    todos = []
    for i, line in enumerate(content.split('\n')):
        m = re.search(r'TODO:\s*\[( |x)\]\s*(.*)', line)
        if m:
            todos.append({
                "line_index": i,
                "done": m.group(1) == 'x',
                "text": m.group(2).strip(),
            })
    ideas = []
    for line in content.split('\n'):
        if '**idea**' in line.lower():
            text = re.sub(r'\*\*idea\*\*', '', line, flags=re.IGNORECASE).strip('- ').strip()
            if text:
                ideas.append(text)
    short_desc = ""
    sd_match = re.search(r'\*\*Short Desc:\*\*\s*(.*)', content)
    if sd_match:
        short_desc = sd_match.group(1).strip()
    hidden = '#_hidden' in content
    return {
        "status": status,
        "load": load,
        "category": category,
        "tags": tags,
        "todos": todos,
        "ideas": ideas,
        "short_desc": short_desc,
        "hidden": hidden,
    }


def toggle_todo(projects: list, project_id: str, line_index: int) -> list:
    """Toggle TODO [ ] <-> [x] at line_index. Returns updated projects list."""
    for proj in projects:
        if proj["id"] == project_id:
            lines = proj["content"].split('\n')
            if 0 <= line_index < len(lines):
                line = lines[line_index]
                if 'TODO: [ ]' in line:
                    lines[line_index] = line.replace('TODO: [ ]', 'TODO: [x]', 1)
                elif 'TODO: [x]' in line:
                    lines[line_index] = line.replace('TODO: [x]', 'TODO: [ ]', 1)
                proj["content"] = '\n'.join(lines)
            break
    return projects


def set_status(projects: list, project_id: str, new_status: str) -> list:
    """Replace or add status tag in project content. Returns updated projects list."""
    for proj in projects:
        if proj["id"] == project_id:
            content = proj["content"]
            for s in STATUS_TAGS:
                content = re.sub(r'#' + s + r'\b', '', content)
            content = re.sub(r'  +', ' ', content)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('#') and not line.strip().startswith('## '):
                    lines[i] = ('#' + new_status + ' ' + line.strip()).rstrip()
                    break
            proj["content"] = '\n'.join(lines)
            break
    return projects
