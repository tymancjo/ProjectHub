import os
import re
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DB_FILE = os.getenv("DB_PATH", os.path.join("db", "projects.md"))
DB_DIR  = os.path.dirname(os.path.abspath(DB_FILE))

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

def read_projects():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write(INITIAL_CONTENT)
    with open(DB_FILE, "r", encoding="utf-8") as f:
        content = f.read()
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

def save_projects_to_file(projects_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(projects_data))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Hub Pro</title>
    <script>tailwind.config={darkMode:'class'}</script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
    <link  rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.17/codemirror.min.css">
    <link  rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.17/theme/dracula.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.17/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.17/keymap/vim.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.17/mode/markdown/markdown.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --bg-app: #f8fafc; --bg-surface: #ffffff; --bg-subtle: #f8fafc; --bg-muted: #f1f5f9;
            --border: #e2e8f0; --border-subtle: #f1f5f9;
            --text-primary: #1e293b; --text-secondary: #475569; --text-muted: #94a3b8; --text-faint: #cbd5e1;
            --header-bg: #ffffff;
        }
        html.dark {
            --bg-app: #0f172a; --bg-surface: #1e293b; --bg-subtle: #1e293b; --bg-muted: #334155;
            --border: #334155; --border-subtle: #1e293b;
            --text-primary: #f1f5f9; --text-secondary: #cbd5e1; --text-muted: #64748b; --text-faint: #475569;
            --header-bg: #1e293b;
        }

        body { font-family: 'Inter', sans-serif; background-color: var(--bg-app); color: var(--text-primary); }

        /* Dark mode Tailwind class overrides */
        html.dark .bg-white   { background-color: var(--bg-surface) !important; }
        html.dark .bg-slate-50 { background-color: var(--bg-subtle) !important; }
        html.dark .bg-slate-100 { background-color: var(--bg-muted) !important; }
        html.dark .bg-white\/95 { background-color: rgba(30,41,59,0.97) !important; }
        html.dark .border-slate-200 { border-color: var(--border) !important; }
        html.dark .border-slate-100 { border-color: var(--border-subtle) !important; }
        html.dark .text-slate-900, html.dark .text-slate-800 { color: var(--text-primary) !important; }
        html.dark .text-slate-700, html.dark .text-slate-600 { color: var(--text-secondary) !important; }
        html.dark .text-slate-500, html.dark .text-slate-400 { color: var(--text-muted) !important; }
        html.dark .text-slate-300 { color: var(--text-faint) !important; }
        html.dark .divide-slate-50 > * { border-color: var(--border-subtle) !important; }
        html.dark .divide-y > * + * { border-color: var(--border-subtle) !important; }
        html.dark .shadow-sm, html.dark .shadow-md, html.dark .shadow-lg { box-shadow: 0 1px 8px rgba(0,0,0,0.4) !important; }
        html.dark .hover\\:bg-slate-50:hover { background-color: var(--bg-muted) !important; }
        html.dark .hover\\:bg-slate-100:hover { background-color: #475569 !important; }
        html.dark .bg-slate-900\\/80 { background-color: rgba(2,6,23,0.90) !important; }
        .project-column { min-width: 380px; max-width: 380px; height: calc(100vh - 200px); }

        .markdown-content h1 { font-size: 2em; font-weight: 800; margin-bottom: 0.8em; color: var(--text-primary); border-bottom: 1px solid var(--border); padding-bottom: 0.4em; }
        .markdown-content h2 { font-size: 1.5em; font-weight: 700; margin-top: 1.2em; margin-bottom: 0.6em; color: var(--text-primary); border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.2em; }
        .markdown-content h3 { font-size: 1.2em; font-weight: 700; margin-top: 1em; margin-bottom: 0.4em; color: var(--text-secondary); display: block; }
        .markdown-content p { margin-bottom: 1em; font-size: 1em; line-height: 1.6; color: var(--text-secondary); }
        .markdown-content ul { list-style-type: disc !important; padding-left: 1.5em !important; margin-bottom: 1em !important; display: block !important; }
        .markdown-content ol { list-style-type: decimal !important; padding-left: 1.5em !important; margin-bottom: 1em !important; display: block !important; }
        .markdown-content li { font-size: 1em; color: var(--text-secondary); margin-bottom: 0.4em; display: list-item !important; list-style: inherit !important; }
        .markdown-content code { background-color: var(--bg-muted); padding: 0.2em 0.4em; border-radius: 4px; color: #be185d; font-family: monospace; font-size: 0.9em; }
        .markdown-content pre { background-color: #1e293b; color: #f1f5f9; padding: 1rem; border-radius: 8px; overflow-x: auto; margin-bottom: 1em; font-size: 0.8em; }
        #board .markdown-content { font-size: 0.875rem; }

        .sortable-ghost { opacity: 0.4; border: 2px dashed #f7b705; }

        /* CodeMirror editor */
        #cm-wrapper { flex: 1; overflow: hidden; min-height: 0; }
        .CodeMirror { height: 100% !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.875rem; line-height: 1.6; }
        .CodeMirror-scroll { padding: 1.5rem 2rem; box-sizing: border-box; }
        .CodeMirror-cursor { border-left-color: #f7b705 !important; }

        .filter-pill { display: inline-flex; align-items: center; height: 28px; padding: 0 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; border: 1px solid #e2e8f0; background-color: #ffffff; color: #64748b; transition: all 0.2s ease; cursor: pointer; gap: 6px; white-space: nowrap; }
        .filter-pill:hover { border-color: #f7b705; color: #d4991a; }
        .filter-pill.active { background-color: #e11d48 !important; color: #ffffff !important; border-color: #e11d48 !important; box-shadow: 0 4px 12px rgba(225,29,72,0.3); }
        .filter-pill-hidden { border-style: dashed; background-color: #f8fafc; color: #94a3b8; }
        .filter-pill-clear { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; color: #94a3b8; cursor: pointer; }
        .filter-pill-clear.active { color: #d4991a; background-color: #fef9e7; }
        .filter-separator { color: #cbd5e1; font-weight: 300; margin: 0 4px; user-select: none; }

        #presentation-content { transition: font-size 0.2s ease; line-height: 1.6; }
        .presentation-card { max-width: 850px; width: 90%; margin: 0 auto; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

        .btn-accent { background: #f7b705; color: #1c1917; }
        .btn-accent:hover { background: #d9a204; }
        .nav-tab-active { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.07); color: #d4991a !important; }

        /* TODO view */
        .todo-checkbox { width: 17px; height: 17px; border-radius: 4px; border: 2px solid #cbd5e1; cursor: pointer; appearance: none; -webkit-appearance: none; flex-shrink: 0; transition: all 0.15s; background: white; }
        .todo-checkbox:checked { background-color: #f7b705; border-color: #f7b705; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 16 16' fill='%231c1917' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3E%3C/svg%3E"); background-size: 100%; }
        .todo-done { text-decoration: line-through; color: #94a3b8; }

        /* Timeline */
        .tl-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
        .tl-line { width: 2px; background: #e2e8f0; flex: 1; margin-top: 4px; min-height: 16px; }
        .tl-month { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #94a3b8; padding: 20px 0 8px; }

        /* Boss Map */
        .map-card { transition: transform 0.15s ease, box-shadow 0.15s ease; }
        .map-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.09); }
        .progress-track { height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 2px; }
        mark { background:#fef9e7; color:#92400e; border-radius:2px; padding:0 2px; }

        /* Priority tags */
        .priority-p1 { border-left: 3px solid #e11d48 !important; }
        .priority-p2 { border-left: 3px solid #f7b705 !important; }
        .priority-p3 { border-left: 3px solid #3b82f6 !important; }

        /* Quick Capture */
        #quick-capture-panel { transform: translateY(100%); transition: transform 0.28s cubic-bezier(.4,0,.2,1); }
        #quick-capture-panel.open { transform: translateY(0); }

        /* Gantt */
        .gantt-row-label { height: 42px; display: flex; align-items: center; padding: 0 12px; border-bottom: 1px solid rgba(226,232,240,0.5); cursor: pointer; gap: 6px; transition: background 0.1s; }
        .gantt-row-label:hover { background: rgba(247,183,5,0.06); }
        .gantt-group-label { height: 42px; display: flex; align-items: center; padding: 0 12px; background: var(--bg-muted); border-bottom: 1px solid var(--border); }

        /* Calendar */
        .cal-day { min-height: 86px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; padding: 6px; }
        .cal-day.today { background: #fef9e7; }
        .cal-day.other-month { background: var(--bg-subtle); opacity: 0.65; }
        .cal-event { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; margin-top: 2px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
    </style>
</head>
<body class="h-screen overflow-hidden flex flex-col">

    <header class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shrink-0 z-20">
        <div class="flex items-center gap-6">
            <div class="flex items-center gap-3">
                <div class="p-2 rounded-xl shadow-lg" style="background:#f7b705">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                </div>
                <h1 class="text-xl font-bold text-slate-900 tracking-tight">ProjectBoard</h1>
            </div>
            <nav class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                <button id="view-home"     onclick="setViewMode('home')"     class="px-4 py-1.5 rounded-md text-sm font-bold transition-all nav-tab-active">Home</button>
                <button id="view-board"    onclick="setViewMode('board')"    class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Board</button>
                <button id="view-list"     onclick="setViewMode('list')"     class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Overview</button>
                <button id="view-todos"    onclick="setViewMode('todos')"    class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">TODOs</button>
                <button id="view-timeline" onclick="setViewMode('timeline')" class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Timeline</button>
                <button id="view-map"      onclick="setViewMode('map')"      class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Map</button>
                <button id="view-network"  onclick="setViewMode('network')"  class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Network</button>
                <button id="view-gantt"    onclick="setViewMode('gantt')"    class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Gantt</button>
                <button id="view-calendar" onclick="setViewMode('calendar')" class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Calendar</button>
            </nav>
        </div>
        <div class="flex items-center gap-3">
            <div class="relative">
                <input id="search-input" type="text" placeholder="Search projects…"
                    oninput="onSearchInput(event)" onkeydown="onSearchKey(event)"
                    class="pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-amber-400 focus:bg-white w-48 transition-all" autocomplete="off">
                <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
            <button onclick="openHelp()" class="p-2 rounded-lg border border-slate-200 hover:border-amber-400 transition-all text-slate-400 hover:text-amber-500" title="Help &amp; syntax reference">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </button>
            <button id="dark-toggle" onclick="toggleDarkMode()" class="p-2 rounded-lg border border-slate-200 hover:border-amber-400 transition-all text-slate-400 hover:text-amber-500" title="Toggle dark mode">
                <svg id="dark-icon-moon" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                <svg id="dark-icon-sun"  class="h-4 w-4 hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
            </button>
            <button onclick="addNewProject()" class="flex items-center gap-2 px-4 py-2 btn-accent rounded-lg font-bold shadow-md transition-all text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" /></svg>
                New Project
            </button>
        </div>
    </header>

    <div id="filter-bar" class="bg-white border-b border-slate-200 px-8 py-2 flex items-center gap-2 shrink-0 overflow-x-auto no-scrollbar">
        <div id="filter-clear-btn" class="shrink-0"></div>
        <div class="h-6 w-px bg-slate-100 shrink-0 mx-1"></div>
        <div id="filter-tags" class="flex items-center gap-1 py-1"></div>
    </div>

    <main class="flex-1 flex overflow-hidden relative">
        <div id="home-view"     class="hidden flex-1 overflow-y-auto p-8"></div>
        <div id="board"         class="flex-1 overflow-x-auto flex gap-6 p-8 items-start"></div>
        <div id="list-view"     class="hidden flex-1 overflow-y-auto p-8 max-w-6xl mx-auto w-full">
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Project</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Description</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tags</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Load</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Chars</th>
                        </tr>
                    </thead>
                    <tbody id="list-body"></tbody>
                </table>
            </div>
        </div>
        <div id="todos-view"    class="hidden flex-1 overflow-y-auto p-8"></div>
        <div id="timeline-view" class="hidden flex-1 overflow-y-auto p-8"></div>
        <div id="map-view"      class="hidden flex-1 overflow-y-auto p-8"></div>
        <div id="search-view"  class="hidden flex-1 overflow-y-auto p-8"></div>
        <div id="network-view"  class="hidden flex-1 overflow-hidden p-6"></div>
        <div id="gantt-view"    class="hidden flex-1 overflow-hidden p-6"></div>
        <div id="calendar-view" class="hidden flex-1 overflow-y-auto p-8"></div>
    </main>

    <!-- Editor Modal -->
    <div id="editor-modal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex flex-col h-[85vh] overflow-hidden">
            <div class="px-6 py-4 border-b flex justify-between items-center bg-white">
                <div><h3 class="text-lg font-bold">Edit Project</h3><p class="text-xs text-slate-400">Markdown · <code>#tags</code> · <code>TODO: [ ] task</code> · <code>TODO: [ ] **date** = milestone</code> · <code>#cat:name</code> · <code>#proj:id</code> · <code>#load:N</code> · <code>#start:dd-mm-yyyy</code> · <code>#due:dd-mm-yyyy</code> · <code>#p1/#p2/#p3</code></p></div>
                <div class="flex items-center gap-2">
                    <button onclick="insertDateAtCursor()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold border">📅 Date</button>
                    <div class="relative" id="proj-link-container">
                        <button onclick="toggleProjLinkDropdown()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold border" title="Insert project link">🔗 Link</button>
                        <div id="proj-link-dropdown" class="hidden absolute right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-[60] w-72 max-h-72 overflow-y-auto">
                            <div class="px-3 py-2 border-b border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-400">Insert project link</div>
                            <div id="proj-link-list"></div>
                        </div>
                    </div>
                    <button id="vim-toggle" onclick="toggleVimMode()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold border" title="Toggle Vim mode">VIM</button>
                    <button onclick="closeModal()" class="p-2 hover:bg-slate-100 rounded-full text-slate-400">
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                </div>
            </div>
            <div id="cm-wrapper"></div>
            <div class="px-4 py-2 border-t bg-slate-50 flex justify-between items-center gap-3">
                <span id="vim-mode-indicator" class="text-[10px] font-mono font-black px-2 py-1 rounded bg-slate-200 text-slate-500" style="display:none">NORMAL</span>
                <div class="flex gap-3 ml-auto">
                    <button onclick="closeModal()" class="px-4 py-2 font-semibold text-slate-600">Cancel</button>
                    <button onclick="saveProjectUpdate()" class="px-8 py-2 btn-accent font-bold rounded-lg shadow-md">Save Changes</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Presentation Modal -->
    <div id="presentation-modal" class="fixed inset-0 bg-white/95 backdrop-blur-xl z-50 hidden flex flex-col overflow-hidden">
        <header class="px-8 py-4 border-b flex justify-between items-center bg-white sticky top-0 z-10">
            <div class="flex items-center gap-6">
                <h3 id="pres-title" class="text-xl font-black text-slate-900">Project Title</h3>
                <div class="flex items-center bg-slate-100 rounded-lg p-1 gap-1">
                    <button onclick="adjustFontSize(-2)" class="w-8 h-8 flex items-center justify-center rounded hover:bg-white transition-colors">
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/></svg>
                    </button>
                    <span id="font-size-label" class="text-[10px] font-bold px-2 text-slate-400 w-12 text-center">100%</span>
                    <button onclick="adjustFontSize(2)" class="w-8 h-8 flex items-center justify-center rounded hover:bg-white transition-colors">
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    </button>
                </div>
            </div>
            <div class="flex items-center gap-1">
                <button id="pres-edit-btn" class="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-amber-500 transition-colors" title="Edit project">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                </button>
                <button onclick="closePresentation()" class="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors" title="Close">
                    <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            </div>
        </header>
        <main class="flex-1 overflow-y-auto p-12"><div id="presentation-content" class="presentation-card markdown-content"></div></main>
    </div>

    <!-- Help Modal -->
    <div id="help-modal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4" onclick="if(event.target===this)closeHelp()">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[88vh] flex flex-col overflow-hidden">
            <!-- Header -->
            <div class="px-6 py-4 border-b flex justify-between items-center shrink-0">
                <div class="flex items-center gap-3">
                    <div class="p-2 rounded-xl shadow" style="background:#f7b705">
                        <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </div>
                    <div>
                        <h2 class="text-lg font-black text-slate-900">Help &amp; Reference</h2>
                        <p class="text-xs text-slate-400">Keyboard shortcuts · Data syntax · Views</p>
                    </div>
                </div>
                <button onclick="closeHelp()" class="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            </div>
            <!-- Scrollable body -->
            <div class="overflow-y-auto flex-1 px-6 py-5 space-y-6 text-sm text-slate-700">

                <!-- Keyboard shortcuts -->
                <section>
                    <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">⌨️ Keyboard Shortcuts</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <div class="flex items-center gap-3 p-2 rounded-lg bg-slate-50">
                            <kbd class="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-mono font-bold shadow-sm">Q</kbd>
                            <span class="text-slate-600">Quick capture note</span>
                        </div>
                        <div class="flex items-center gap-3 p-2 rounded-lg bg-slate-50">
                            <kbd class="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-mono font-bold shadow-sm">?</kbd>
                            <span class="text-slate-600">Open this help panel</span>
                        </div>
                        <div class="flex items-center gap-3 p-2 rounded-lg bg-slate-50">
                            <kbd class="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-mono font-bold shadow-sm">Esc</kbd>
                            <span class="text-slate-600">Close any modal / panel</span>
                        </div>
                        <div class="flex items-center gap-3 p-2 rounded-lg bg-slate-50">
                            <kbd class="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-mono font-bold shadow-sm">Enter</kbd>
                            <span class="text-slate-600">Save quick capture</span>
                        </div>
                    </div>
                </section>

                <!-- Project syntax -->
                <section>
                    <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">📄 Project File Syntax</h3>
                    <div class="bg-slate-900 rounded-xl p-4 font-mono text-xs leading-relaxed text-slate-200 overflow-x-auto">
<span class="text-amber-400">## Project: My Project Name</span>
<span class="text-slate-400">**Short Desc:** One-line summary shown in Overview &amp; Map.</span>
<span class="text-slate-500">---</span>
<span class="text-emerald-400">#active #cat:engineering #load:120 #p1</span>
<span class="text-slate-500">#start:01-05-2026 #due:30-06-2026</span>
<span class="text-slate-500">#proj:other-project-id</span>

Free-form Markdown notes here.

<span class="text-sky-400">**14-05-2026**</span> Creates a Timeline entry.

<span class="text-yellow-300">TODO: [ ] Open task</span>
<span class="text-yellow-300">TODO: [x] Completed task</span>
<span class="text-yellow-300">TODO: [ ] **30-06-2026** Milestone with due date</span>
                    </div>
                </section>

                <!-- Tags reference -->
                <section>
                    <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">🏷️ Special Tags</h3>
                    <div class="grid grid-cols-1 gap-1.5">
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#active / #done / #hold / #backlog</code>
                            <span class="text-slate-600 text-xs">Status badge on Map &amp; Gantt bar colour</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#cat:name</code>
                            <span class="text-slate-600 text-xs">Groups project in Map &amp; Gantt swimlanes</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#load:N</code>
                            <span class="text-slate-600 text-xs">Numeric workload (shown in Map &amp; Gantt tooltip)</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#start:dd-mm-yyyy</code>
                            <span class="text-slate-600 text-xs">Gantt bar start date (falls back to first <strong>**date**</strong> in content)</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#due:dd-mm-yyyy</code>
                            <span class="text-slate-600 text-xs">Deadline shown in Home dashboard &amp; Gantt bar end</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#proj:project-id</code>
                            <span class="text-slate-600 text-xs">Links to another project — shown in Network &amp; Gantt arrows</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#p1 / #p2 / #p3</code>
                            <span class="text-slate-600 text-xs">Priority: red / amber / blue left border on Board &amp; Map cards</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#_hidden</code>
                            <span class="text-slate-600 text-xs">Hides project from all default views (underscore prefix)</span>
                        </div>
                        <div class="grid grid-cols-[180px_1fr] gap-3 px-3 py-2 rounded-lg bg-slate-50 items-start">
                            <code class="text-xs font-mono font-bold text-rose-600">#inbox</code>
                            <span class="text-slate-600 text-xs">Quick Capture saves notes here; auto-created if missing</span>
                        </div>
                    </div>
                </section>

                <!-- Views -->
                <section>
                    <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">🗂️ Views</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">🏠 Home</div>
                            <div class="text-xs text-slate-500">Dashboard: active stats, deadlines urgency panel, quick links</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">📋 Board</div>
                            <div class="text-xs text-slate-500">Kanban cards, drag to reorder, filter by tag</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">📊 Overview</div>
                            <div class="text-xs text-slate-500">Compact table: title, desc, tags, load, size</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">✅ TODOs</div>
                            <div class="text-xs text-slate-500">All tasks across projects, live checkboxes</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">📅 Timeline</div>
                            <div class="text-xs text-slate-500">Chronological date markers — list or month-grid</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">🗺️ Map</div>
                            <div class="text-xs text-slate-500">Portfolio by category, progress bars, status badges</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">🕸️ Network</div>
                            <div class="text-xs text-slate-500">SVG graph of <code class="text-rose-600">#proj:</code> dependencies</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">📊 Gantt</div>
                            <div class="text-xs text-slate-500">Timeline bars with zoom week/month/quarter, dependency arrows</div>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50">
                            <div class="font-bold text-slate-800 text-xs mb-1">🗓️ Calendar</div>
                            <div class="text-xs text-slate-500">Monthly grid of all date markers and milestones</div>
                        </div>
                    </div>
                </section>

                <!-- Tips -->
                <section>
                    <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">💡 Tips</h3>
                    <ul class="space-y-1.5 text-xs text-slate-600">
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Click any Gantt bar or Network node to open the full project view.</li>
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Press 📅 Date in the editor to insert today's date in the correct format.</li>
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Toggle <strong>VIM</strong> in the editor for Vim keybindings (with Dracula theme).</li>
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Set <code class="text-rose-600">DB_PATH</code> env var (copy <code>.env.example → .env</code>) to use any Markdown file as your database.</li>
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Projects with <code class="text-rose-600">#_hidden</code> are invisible in views but still editable via direct URL or filter.</li>
                        <li class="flex gap-2"><span class="text-amber-500">▸</span> Gantt auto-detects date range from content if <code class="text-rose-600">#start:</code>/<code class="text-rose-600">#due:</code> are absent.</li>
                    </ul>
                </section>

            </div>
            <!-- Footer -->
            <div class="px-6 py-3 border-t bg-slate-50 flex justify-between items-center shrink-0">
                <span class="text-[10px] text-slate-400">ProjectBoard Pro · all data stays local in <code>db/projects.md</code></span>
                <button onclick="closeHelp()" class="px-4 py-2 btn-accent font-bold rounded-lg text-sm shadow-md">Got it</button>
            </div>
        </div>
    </div>

    <!-- Quick Capture Panel -->
    <div id="quick-capture-panel" class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 shadow-2xl z-40 px-8 py-4">
        <div class="max-w-2xl mx-auto">
            <div class="flex items-center gap-3 mb-2">
                <span class="text-xs font-black uppercase tracking-widest text-slate-400">⚡ Quick Capture</span>
                <span class="text-[10px] text-slate-300">Enter to save · Shift+Enter for newline · Esc to dismiss · saves to #inbox</span>
                <button onclick="closeQuickCapture()" class="ml-auto p-1 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            </div>
            <textarea id="quick-capture-input" rows="2" placeholder="Type a quick note…" onkeydown="handleQuickCaptureKey(event)" class="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:border-amber-400 bg-slate-50 focus:bg-white transition-all"></textarea>
        </div>
    </div>

    <script>
        let projects = [];
        let currentEditingId = null;
        let viewMode = 'home';
        let activeFilterTags = new Set();
        let presentationFontSize = 18;
        let timelineMode = 'grid';
        let timelineFilter = 'all';
        let searchQuery = '';
        let mapLoadMode = 'project';
        let cmEditor = null;
        let vimEnabled = localStorage.getItem('vimMode') === 'true';
        let ganttZoom = localStorage.getItem('ganttZoom') || 'month';
        let calendarYear = new Date().getFullYear();
        let calendarMonth = new Date().getMonth();
        let quickCaptureOpen = false;

        const COLORS = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#06b6d4','#64748b'];

        let darkMode = localStorage.getItem('darkMode') === 'true';
        function applyDarkMode() {
            document.documentElement.classList.toggle('dark', darkMode);
            document.getElementById('dark-icon-moon').classList.toggle('hidden',  darkMode);
            document.getElementById('dark-icon-sun').classList.toggle('hidden',  !darkMode);
        }
        function toggleDarkMode() { darkMode = !darkMode; localStorage.setItem('darkMode', darkMode); applyDarkMode(); }

        async function loadProjects() {
            const r = await fetch('/api/projects');
            projects = await r.json();
            setViewMode(viewMode);
        }

        // ── View mode ─────────────────────────────────────────────────────────
        function setViewMode(mode) {
            viewMode = mode;
            searchQuery = '';
            document.getElementById('search-input').value = '';
            const filterBound = ['board', 'list'];
            document.getElementById('filter-bar').classList.toggle('hidden', !filterBound.includes(mode));
            ['home','board','list','todos','timeline','map','network','gantt','calendar'].forEach(v => {
                const btn = document.getElementById('view-' + v);
                const el  = document.getElementById(v === 'board' ? 'board' : v + '-view');
                if (btn) btn.className = (mode === v)
                    ? 'px-4 py-1.5 rounded-md text-sm font-bold transition-all nav-tab-active'
                    : 'px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800';
                if (el) el.classList.toggle('hidden', mode !== v);
            });
            renderAll();
        }

        // ── Filters ───────────────────────────────────────────────────────────
        function toggleTagFilter(tag) {
            activeFilterTags.has(tag) ? activeFilterTags.delete(tag) : activeFilterTags.add(tag);
            renderAll();
        }
        function clearTagFilters() { activeFilterTags.clear(); renderAll(); }

        // ── Project CRUD ──────────────────────────────────────────────────────
        function addNewProject() {
            const tpl = "## Project: New Project Name\\n**Short Desc:** Description.\\n---\\n#new\\nStart writing here...";
            const id = 'new-' + Date.now();
            projects.push({ id, title: 'New Project Name', content: tpl });
            openModal(id);
        }

        function openModal(id) {
            currentEditingId = id;
            const content = projects.find(p => p.id === id).content;
            document.getElementById('editor-modal').classList.remove('hidden');

            const wrapper = document.getElementById('cm-wrapper');
            wrapper.innerHTML = '';
            cmEditor = CodeMirror(wrapper, {
                value: content,
                mode: 'markdown',
                theme: 'dracula',
                lineWrapping: true,
                keyMap: vimEnabled ? 'vim' : 'default',
                autofocus: true,
                extraKeys: { Tab: false },
            });
            cmEditor.setSize('100%', '100%');
            cmEditor.on('vim-mode-change', info => updateVimIndicator(info.mode));
            updateVimToggle();
            updateVimIndicator(vimEnabled ? 'normal' : 'insert');
        }

        function closeModal() {
            document.getElementById('editor-modal').classList.add('hidden');
            cmEditor = null;
            currentEditingId = null;
        }

        function toggleVimMode() {
            vimEnabled = !vimEnabled;
            localStorage.setItem('vimMode', vimEnabled);
            if (cmEditor) cmEditor.setOption('keyMap', vimEnabled ? 'vim' : 'default');
            updateVimToggle();
            updateVimIndicator(vimEnabled ? 'normal' : 'insert');
        }

        function updateVimToggle() {
            const btn = document.getElementById('vim-toggle');
            btn.className = vimEnabled
                ? 'px-3 py-1.5 rounded-lg text-xs font-bold border btn-accent'
                : 'px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold border text-slate-500';
            btn.title = vimEnabled ? 'Vim ON — click to disable' : 'Vim OFF — click to enable';
        }

        function updateVimIndicator(mode) {
            const el = document.getElementById('vim-mode-indicator');
            el.style.display = vimEnabled ? 'inline-block' : 'none';
            if (!vimEnabled) return;
            el.textContent = mode.toUpperCase();
            const cls = { insert: 'bg-amber-100 text-amber-700', normal: 'bg-slate-200 text-slate-600', visual: 'bg-purple-100 text-purple-700', replace: 'bg-red-100 text-red-600' };
            el.className = `text-[10px] font-mono font-black px-2 py-1 rounded ${cls[mode] || cls.normal}`;
        }

        function openPresentation(id) {
            const proj = projects.find(p => p.id === id);
            const body = proj.content.split('---').slice(-1)[0].trim();
            document.getElementById('pres-title').innerText = proj.title;
            document.getElementById('presentation-content').innerHTML = marked.parse(body);
            document.getElementById('pres-edit-btn').onclick = () => { closePresentation(); openModal(id); };
            document.getElementById('presentation-modal').classList.remove('hidden');
            presentationFontSize = 18; updateFontSizeDisplay();
        }
        function closePresentation() { document.getElementById('presentation-modal').classList.add('hidden'); }

        function adjustFontSize(d) {
            presentationFontSize = Math.max(12, Math.min(80, presentationFontSize + d));
            updateFontSizeDisplay();
        }
        function updateFontSizeDisplay() {
            document.getElementById('presentation-content').style.fontSize = presentationFontSize + 'px';
            document.getElementById('font-size-label').innerText = Math.round((presentationFontSize / 18) * 100) + '%';
        }

        function insertDateAtCursor() {
            if (!cmEditor) return;
            const ds = `**${new Date().toLocaleDateString('en-GB').replace(/\\//g, '-')}**`;
            cmEditor.replaceRange(ds, cmEditor.getCursor());
            cmEditor.focus();
        }

        async function saveProjectUpdate() {
            const idx = projects.findIndex(p => p.id === currentEditingId);
            if (idx !== -1 && cmEditor) projects[idx].content = cmEditor.getValue();
            await fetch('/api/save-order', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(projects.map(p => p.content)) });
            closeModal();
            loadProjects();
        }

        function toggleProjLinkDropdown() {
            const dd = document.getElementById('proj-link-dropdown');
            const isOpen = !dd.classList.contains('hidden');
            if (isOpen) { dd.classList.add('hidden'); return; }
            const list = document.getElementById('proj-link-list');
            list.innerHTML = projects
                .filter(p => p.id !== currentEditingId)
                .map(p => {
                    const cats = [...p.content.matchAll(/#cat:([\\w]+)/g)].map(m => m[1]);
                    const catBadge = cats.length ? `<span class="text-[9px] font-bold px-1.5 py-0.5 rounded-full text-white" style="background:#94a3b8">${cats[0]}</span>` : '';
                    return `<button onclick="insertProjectLink('${p.id}')"
                        class="w-full text-left px-3 py-2.5 hover:bg-amber-50 flex items-center justify-between gap-2 border-b border-slate-50 last:border-0">
                        <div>
                            <div class="text-sm font-semibold text-slate-800">${p.title}</div>
                            <div class="text-[10px] font-mono text-slate-400">#proj:${p.id}</div>
                        </div>
                        ${catBadge}
                    </button>`;
                }).join('');
            dd.classList.remove('hidden');
            if (cmEditor) cmEditor.focus();
        }

        function insertProjectLink(id) {
            document.getElementById('proj-link-dropdown').classList.add('hidden');
            if (!cmEditor) return;
            cmEditor.replaceRange('#proj:' + id + ' ', cmEditor.getCursor());
            cmEditor.focus();
        }

        document.addEventListener('click', e => {
            const container = document.getElementById('proj-link-container');
            if (container && !container.contains(e.target))
                document.getElementById('proj-link-dropdown').classList.add('hidden');
        });

        // ── TODO view ─────────────────────────────────────────────────────────
        function parseTodos() {
            return projects.map((proj, pi) => {
                const items = [];
                proj.content.split('\\n').forEach((line, i) => {
                    const m = line.match(/TODO:\\s*\\[([ x])\\]\\s*(.+)/i);
                    if (m) items.push({ lineIndex: i, done: m[1].toLowerCase() === 'x', task: m[2].trim() });
                });
                return { proj, pi, items };
            }).filter(g => g.items.length > 0);
        }

        function renderTodos() {
            const groups = parseTodos();
            let totalDone = 0, totalPending = 0;
            groups.forEach(g => g.items.forEach(t => t.done ? totalDone++ : totalPending++));

            let html = `<div class="max-w-3xl mx-auto">
                <div class="flex items-center gap-3 mb-8">
                    <h2 class="text-2xl font-black text-slate-900">All TODOs</h2>
                    <span class="px-3 py-1 bg-amber-50 text-amber-700 text-sm font-bold rounded-full">${totalPending} pending</span>
                    <span class="px-3 py-1 bg-emerald-50 text-emerald-700 text-sm font-bold rounded-full">${totalDone} done</span>
                </div>`;

            if (!groups.length) {
                html += `<p class="text-slate-400 text-center mt-16 text-sm">No TODOs found. Use <code class="bg-slate-100 px-1.5 py-0.5 rounded">TODO: [ ] task text</code> in any project.</p>`;
            } else {
                groups.forEach(({ proj, pi, items }) => {
                    const done = items.filter(t => t.done).length;
                    const pct  = Math.round((done / items.length) * 100);
                    const col  = COLORS[pi % COLORS.length];
                    html += `<div class="bg-white rounded-2xl shadow-sm border border-slate-200 mb-6 overflow-hidden">
                        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between" style="border-left:3px solid ${col}">
                            <div class="flex items-center gap-3">
                                <button onclick="openModal('${proj.id}')" class="text-base font-bold text-slate-900 hover:text-amber-600 transition-colors">${proj.title}</button>
                                <span class="text-xs font-mono text-slate-400">${done}/${items.length}</span>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                    <div class="h-full rounded-full transition-all" style="width:${pct}%;background:${col}"></div>
                                </div>
                                <span class="text-xs font-bold text-slate-400 w-8 text-right">${pct}%</span>
                            </div>
                        </div>
                        <div class="divide-y divide-slate-50">`;
                    items.forEach(({ lineIndex, done, task }) => {
                        html += `<label class="flex items-center gap-4 px-6 py-3 hover:bg-slate-50 cursor-pointer">
                            <input type="checkbox" class="todo-checkbox" ${done ? 'checked' : ''} onchange="toggleTodo('${proj.id}',${lineIndex})">
                            <span class="text-sm flex-1 ${done ? 'todo-done' : 'text-slate-700'}">${task}</span>
                        </label>`;
                    });
                    html += `</div></div>`;
                });
            }
            html += `</div>`;
            document.getElementById('todos-view').innerHTML = html;
        }

        async function toggleTodo(projectId, lineIndex) {
            await fetch('/api/toggle-todo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ projectId, lineIndex })
            });
            await loadProjects();
        }

        // ── Timeline view ─────────────────────────────────────────────────────
        function parseDates() {
            const events = [];
            projects.forEach((proj, pi) => {
                const color = COLORS[pi % COLORS.length];
                proj.content.split('\\n').forEach((line, lineIndex) => {
                    [...line.matchAll(/\\*\\*(\\d{2}-\\d{2}-\\d{4})\\*\\*/g)].forEach(m => {
                        const [dd, mm, yyyy] = m[1].split('-');
                        const date = new Date(+yyyy, +mm - 1, +dd);
                        const todoMatch = line.match(/TODO:\\s*\\[([ x])\\]/i);
                        const isMilestone = !!todoMatch;
                        const milestoneDone = isMilestone && todoMatch[1].toLowerCase() === 'x';
                        const ctx = line
                            .replace(/TODO:\\s*\\[[ x]\\]\\s*/gi, '')
                            .replace(/\\*\\*\\d{2}-\\d{2}-\\d{4}\\*\\*/g, '')
                            .replace(/[*#>`_]/g, '')
                            .trim();
                        events.push({ date, dateStr: m[1], context: ctx || proj.title, projectId: proj.id, projectTitle: proj.title, color, lineIndex, isMilestone, milestoneDone });
                    });
                });
            });
            return events.sort((a, b) => a.date - b.date);
        }

        function setTimelineMode(mode) { timelineMode = mode; renderTimeline(); }
        function setTimelineFilter(f) { timelineFilter = f; renderTimeline(); }

        function onSearchInput(e) { searchQuery = e.target.value; renderAll(); }
        function onSearchKey(e) {
            if (e.key === 'Escape') { searchQuery = ''; document.getElementById('search-input').value = ''; renderAll(); }
        }

        function renderSearch() {
            const q = searchQuery.trim().toLowerCase();
            function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
            function hl(text) {
                const s = String(text), idx = s.toLowerCase().indexOf(q);
                if (idx < 0) return escHtml(s);
                return escHtml(s.slice(0,idx)) + '<mark>' + escHtml(s.slice(idx,idx+q.length)) + '</mark>' + escHtml(s.slice(idx+q.length));
            }
            const results = [];
            projects.forEach(proj => {
                const hits = proj.content.split('\\n').map((line,i) => ({line,i})).filter(({line}) => line.toLowerCase().includes(q));
                if (hits.length) results.push({proj, hits});
            });
            let html = `<div class="max-w-3xl mx-auto">
                <div class="mb-6">
                    <h2 class="text-2xl font-black text-slate-900">Search</h2>
                    <p class="text-sm text-slate-400 mt-0.5">${results.length} project${results.length!==1?'s':''} matching <span class="text-amber-600 font-semibold">"${escHtml(searchQuery.trim())}"</span></p>
                </div>`;
            if (!results.length) {
                html += '<p class="text-slate-400 text-center mt-16 text-sm">No results found.</p>';
            } else {
                results.forEach(({proj, hits}) => {
                    html += `<div class="bg-white rounded-2xl shadow-sm border border-slate-200 mb-4 overflow-hidden">
                        <div class="px-6 py-3 border-b border-slate-100 flex items-center justify-between">
                            <button onclick="openPresentation('${proj.id}')" class="font-bold text-slate-900 hover:text-amber-600 transition-colors">${escHtml(proj.title)}</button>
                            <div class="flex items-center gap-3">
                                <span class="text-xs text-slate-400">${hits.length} match${hits.length!==1?'es':''}</span>
                                <button onclick="openModal('${proj.id}')" class="text-xs font-bold px-2 py-1 rounded bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors">Edit</button>
                            </div>
                        </div>
                        <div class="divide-y divide-slate-50">`;
                    hits.slice(0,6).forEach(({line}) => {
                        const cleaned = line.replace(/^#+\\s*/, '').replace(/^\\s*[-*>]\\s*/, '').trim();
                        if (!cleaned) return;
                        html += `<div class="px-6 py-2.5 text-sm text-slate-600 font-mono leading-relaxed">${hl(cleaned)}</div>`;
                    });
                    if (hits.length > 6) html += `<div class="px-6 py-2 text-xs text-slate-400 italic">…and ${hits.length-6} more lines</div>`;
                    html += `</div></div>`;
                });
            }
            html += '</div>';
            document.getElementById('search-view').innerHTML = html;
        }

        function renderTimeline() {
            if (timelineMode === 'grid') renderTimelineGrid();
            else renderTimelineList();
        }

        function renderTimelineList() {
            const allEvents = parseDates();
            const events = timelineFilter === 'milestones' ? allEvents.filter(e => e.isMilestone) : allEvents;
            const today  = new Date(); today.setHours(0,0,0,0);

            if (!events.length) {
                document.getElementById('timeline-view').innerHTML = timelineFilter === 'milestones'
                    ? '<p class="text-slate-400 text-center mt-16 text-sm">No milestones found. Use <code class="bg-slate-100 px-1.5 py-0.5 rounded">TODO: [ ] **dd-mm-yyyy** milestone name</code> in any project.</p>'
                    : '<p class="text-slate-400 text-center mt-16 text-sm">No dates found. Use <strong>**dd-mm-yyyy**</strong> in notes, or click 📅 in the editor.</p>';
                return;
            }

            const months = {};
            events.forEach(e => {
                const key = e.date.getFullYear() + '-' + String(e.date.getMonth()+1).padStart(2,'0');
                if (!months[key]) months[key] = { label: e.date.toLocaleDateString('en-GB',{month:'long',year:'numeric'}), events:[] };
                months[key].events.push(e);
            });

            let html = `<div class="max-w-2xl mx-auto">
                <div class="flex items-center justify-between mb-6">
                    <div>
                        <h2 class="text-2xl font-black text-slate-900">Timeline</h2>
                        <p class="text-sm text-slate-400 mt-0.5">${events.length} event${events.length!==1?'s':''} across ${projects.length} project${projects.length!==1?'s':''}</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                            <button onclick="setTimelineFilter('all')" class="px-3 py-1.5 text-xs font-bold rounded-md ${timelineFilter==='all'?'nav-tab-active':'text-slate-500 hover:text-slate-800'}">All</button>
                            <button onclick="setTimelineFilter('milestones')" class="px-3 py-1.5 text-xs font-bold rounded-md ${timelineFilter==='milestones'?'nav-tab-active':'text-slate-500 hover:text-slate-800'}">◆ Milestones</button>
                        </div>
                        <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                            <button class="px-3 py-1.5 text-xs font-bold rounded-md nav-tab-active">List</button>
                            <button onclick="setTimelineMode('grid')" class="px-3 py-1.5 text-xs font-bold rounded-md text-slate-500 hover:text-slate-800">Grid</button>
                        </div>
                    </div>
                </div>`;

            Object.values(months).forEach(month => {
                html += `<div class="tl-month">${month.label}</div>`;
                month.events.forEach((e, idx) => {
                    const isPast  = e.date < today;
                    const isToday = e.date.toDateString() === today.toDateString();
                    const isLast  = idx === month.events.length - 1;
                    const shouldFade = isPast && !isToday && !e.isMilestone;
                    const msColor = e.milestoneDone ? '#10b981' : '#f7b705';
                    const dotHtml = e.isMilestone
                        ? `<div style="width:11px;height:11px;transform:rotate(45deg);background:${msColor};flex-shrink:0;margin-top:3px;border-radius:2px"></div>`
                        : `<div class="tl-dot" style="background:${e.color}"></div>`;
                    const msTag = e.isMilestone
                        ? `<button onclick="toggleTodo('${e.projectId}',${e.lineIndex})" class="text-[9px] font-black px-1.5 py-0.5 rounded tracking-wide transition-colors" style="${e.milestoneDone ? 'background:#d1fae5;color:#059669' : 'background:#fef9e7;color:#d4991a'}">${e.milestoneDone ? '✓ Done' : '◆ Milestone'}</button>`
                        : '';
                    html += `<div class="flex gap-4 ${shouldFade ? 'opacity-50' : ''}">
                        <div class="flex flex-col items-center w-4">
                            ${dotHtml}
                            ${!isLast ? '<div class="tl-line"></div>' : ''}
                        </div>
                        <div class="pb-4 flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap mb-0.5">
                                <span class="text-xs font-mono font-bold" style="${isToday ? 'color:#d4991a' : 'color:#94a3b8'}">${e.dateStr}</span>
                                ${isToday ? '<span class="text-[9px] font-black px-1.5 py-0.5 rounded tracking-wide" style="background:#fef9e7;color:#d4991a">TODAY</span>' : ''}
                                ${msTag}
                                <button onclick="openPresentation('${e.projectId}')" class="text-[10px] font-bold px-2 py-0.5 rounded-full text-white hover:opacity-80 transition-opacity" style="background:${e.color}">${e.projectTitle}</button>
                            </div>
                            ${e.context ? `<p class="text-sm text-slate-600 truncate">${e.context}</p>` : ''}
                        </div>
                    </div>`;
                });
            });

            html += `</div>`;
            document.getElementById('timeline-view').innerHTML = html;
        }

        function renderTimelineGrid() {
            const allEvents = parseDates();
            const events = timelineFilter === 'milestones' ? allEvents.filter(e => e.isMilestone) : allEvents;
            const today  = new Date(); today.setHours(0,0,0,0);

            if (!events.length) {
                document.getElementById('timeline-view').innerHTML = timelineFilter === 'milestones'
                    ? '<p class="text-slate-400 text-center mt-16 text-sm">No milestones found. Use <code class="bg-slate-100 px-1.5 py-0.5 rounded">TODO: [ ] **dd-mm-yyyy** milestone name</code> in any project.</p>'
                    : '<p class="text-slate-400 text-center mt-16 text-sm">No dates found. Use <strong>**dd-mm-yyyy**</strong> in notes, or click 📅 in the editor.</p>';
                return;
            }

            const months = {};
            events.forEach(e => {
                const key = e.date.getFullYear() + '-' + String(e.date.getMonth()+1).padStart(2,'0');
                if (!months[key]) months[key] = {
                    label: e.date.toLocaleDateString('en-GB',{month:'long',year:'numeric'}),
                    year: e.date.getFullYear(), month: e.date.getMonth(), events: []
                };
                months[key].events.push(e);
            });

            const toggleHtml = `<div class="flex items-center justify-between mb-6">
                <div>
                    <h2 class="text-2xl font-black text-slate-900">Timeline</h2>
                    <p class="text-sm text-slate-400 mt-0.5">${events.length} event${events.length!==1?'s':''} across ${projects.length} project${projects.length!==1?'s':''}</p>
                </div>
                <div class="flex items-center gap-2">
                    <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                        <button onclick="setTimelineFilter('all')" class="px-3 py-1.5 text-xs font-bold rounded-md ${timelineFilter==='all'?'nav-tab-active':'text-slate-500 hover:text-slate-800'}">All</button>
                        <button onclick="setTimelineFilter('milestones')" class="px-3 py-1.5 text-xs font-bold rounded-md ${timelineFilter==='milestones'?'nav-tab-active':'text-slate-500 hover:text-slate-800'}">◆ Milestones</button>
                    </div>
                    <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                        <button onclick="setTimelineMode('list')" class="px-3 py-1.5 text-xs font-bold rounded-md text-slate-500 hover:text-slate-800">List</button>
                        <button class="px-3 py-1.5 text-xs font-bold rounded-md nav-tab-active">Grid</button>
                    </div>
                </div>
            </div>`;

            let rows = '';
            Object.values(months).forEach(m => {
                const dim       = new Date(m.year, m.month+1, 0).getDate();
                const todayHere = today.getFullYear()===m.year && today.getMonth()===m.month;
                const todayPct  = todayHere ? ((today.getDate()-1)/Math.max(dim-1,1)*100) : -1;

                const evs = m.events.map(e => ({
                    ...e,
                    pct: (e.date.getDate()-1) / Math.max(dim-1,1) * 100,
                    isPast: e.date < today,
                    isToday: e.date.toDateString()===today.toDateString()
                })).sort((a,b) => a.pct - b.pct);

                // Stagger events within 10% of each other onto different vertical levels
                const occupied = [];
                evs.forEach(e => {
                    let lv = 0;
                    while (occupied[lv] !== undefined && e.pct - occupied[lv] < 10) lv++;
                    occupied[lv] = e.pct;
                    e.level = lv;
                });
                const maxLv  = Math.max(...evs.map(e => e.level), 0);
                const trackH = 50 + maxLv * 46;

                let seps = '';
                for (let d = 7; d < dim; d += 7)
                    seps += `<div class="absolute top-0 bottom-0 w-px bg-slate-100" style="left:${((d-1)/(dim-1))*100}%"></div>`;

                let pins = '';
                evs.forEach(e => {
                    const topPx  = 14 + e.level * 46;
                    const msClr  = e.milestoneDone ? '#10b981' : '#f7b705';
                    const dotClr = e.isMilestone ? msClr : (e.isPast && !e.isToday ? '#cbd5e1' : e.color);
                    const txtClr = e.isMilestone ? msClr : (e.isPast && !e.isToday ? '#94a3b8' : e.color);
                    const short  = e.context.length > 18 ? e.context.substring(0,18)+'…' : e.context;
                    const dotEl  = e.isMilestone
                        ? `<button onclick="openPresentation('${e.projectId}')" style="width:12px;height:12px;transform:rotate(45deg);background:${dotClr};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2);border-radius:2px;cursor:pointer" class="hover:scale-125 transition-transform" title="${e.context} (${e.dateStr})"></button>`
                        : `<button onclick="openPresentation('${e.projectId}')" class="w-3 h-3 rounded-full border-2 border-white shadow-sm hover:scale-125 transition-transform" style="background:${dotClr}" title="${e.context} (${e.dateStr})"></button>`;
                    pins += `<div class="absolute flex flex-col items-center" style="left:${e.pct}%;top:${topPx}px;transform:translateX(-50%);z-index:1">
                        ${dotEl}
                        <div class="mt-0.5 text-[9px] font-semibold leading-tight text-center" style="color:${txtClr};max-width:72px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">${short}</div>
                        <div class="text-[8px] text-slate-300 font-mono leading-none">${e.dateStr.substring(0,5)}</div>
                    </div>`;
                });

                const todayLine = todayPct >= 0
                    ? `<div class="absolute top-0 bottom-0 w-0.5" style="left:${todayPct}%;background:#f7b705;opacity:0.5"></div>
                       <div class="absolute text-[8px] font-black leading-none" style="left:${todayPct}%;top:4px;transform:translateX(-50%);color:#d4991a">▼</div>`
                    : '';

                rows += `<div class="flex items-start gap-3 mb-4">
                    <div class="text-[10px] font-black uppercase tracking-wider text-slate-400 w-20 text-right pt-3 shrink-0 leading-tight">${m.label}</div>
                    <div class="flex-1 relative bg-white rounded-xl border border-slate-200 overflow-hidden" style="height:${trackH}px">
                        ${seps}
                        <div class="absolute left-0 right-0 h-px bg-slate-200" style="top:20px"></div>
                        ${pins}
                        ${todayLine}
                    </div>
                </div>`;
            });

            document.getElementById('timeline-view').innerHTML = `<div class="max-w-5xl mx-auto">${toggleHtml}${rows}</div>`;
        }

        // ── Boss Map view ─────────────────────────────────────────────────────
        function setMapLoadMode(m) { mapLoadMode = m; renderBossMap(); }

        function drawPie(slices, cx, cy, r) {
            const total = slices.reduce((s,sl) => s+sl.value, 0) || 1;
            let angle = -Math.PI/2, svg = '';
            slices.forEach(sl => {
                const sweep = sl.value/total*2*Math.PI;
                const x1=(cx+r*Math.cos(angle)).toFixed(2), y1=(cy+r*Math.sin(angle)).toFixed(2);
                const x2=(cx+r*Math.cos(angle+sweep)).toFixed(2), y2=(cy+r*Math.sin(angle+sweep)).toFixed(2);
                const large = sweep > Math.PI ? 1 : 0;
                svg += `<path d="M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2} Z" fill="${sl.color}" stroke="white" stroke-width="1.5"><title>${sl.label}: ${Math.round(sl.value/total*100)}%</title></path>`;
                angle += sweep;
            });
            return svg;
        }

        function statusStyle(tags) {
            if (tags.includes('done'))   return { color:'#10b981', label:'Done' };
            if (tags.includes('active')) return { color:'#f7b705', label:'Active' };
            if (tags.includes('hold') || tags.includes('paused')) return { color:'#f59e0b', label:'Hold' };
            if (tags.includes('backlog')) return { color:'#94a3b8', label:'Backlog' };
            return { color:'#cbd5e1', label:'' };
        }

        function renderBossMap() {
            const palette = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316'];
            const catColors = {}; let ci = 0;

            const enriched = projects.map(proj => {
                const allTags  = [...proj.content.matchAll(/#([a-zA-Z][\\w:]*)/g)].map(m => m[1]);
                const cats     = allTags.filter(t => t.startsWith('cat:')).map(t => t.slice(4));
                const plainTags = allTags.filter(t => !t.startsWith('cat:') && !t.startsWith('proj:') && !t.startsWith('load:') && !t.startsWith('_'));
                const todos    = [...proj.content.matchAll(/TODO:\\s*\\[([ x])\\]/gi)];
                const todoDone = todos.filter(m => m[1].toLowerCase() === 'x').length;
                const dateMs   = [...proj.content.matchAll(/\\*\\*(\\d{2}-\\d{2}-\\d{4})\\*\\*/g)].map(m => {
                    const [dd,mm,yyyy] = m[1].split('-');
                    return new Date(+yyyy, +mm-1, +dd).getTime();
                });
                const latestDate = dateMs.length ? new Date(Math.max(...dateMs)) : null;
                const rawDesc  = (proj.content.split('---')[0] || '').split('\\n').slice(1).join(' ')
                    .replace(/\\*\\*Short Desc:\\*\\*/gi,'').replace(/\\*\\*/g,'').trim();
                return { ...proj, cats: cats.length ? cats : ['—'], plainTags, todoDone, todoTotal: todos.length, latestDate, status: statusStyle(plainTags), desc: rawDesc };
            });

            const catMap = {};
            enriched.forEach(p => p.cats.forEach(cat => { if (!catMap[cat]) catMap[cat]=[]; catMap[cat].push(p); }));
            Object.keys(catMap).sort().forEach(cat => { if (cat !== '—') catColors[cat] = palette[ci++ % palette.length]; });
            catColors['—'] = '#94a3b8';

            // Load chart data — active projects only
            const activeEnriched = enriched.filter(p => p.plainTags.includes('active'));
            const projLoads = activeEnriched.map((p, pi) => {
                const lm = p.content.match(/#load:(\\d+)/);
                return { label: p.title, value: lm ? parseInt(lm[1]) : 100, color: COLORS[pi % COLORS.length] };
            });
            const catLoadTmp = {};
            activeEnriched.forEach((p, pi) => {
                const lv = projLoads[pi].value;
                p.cats.forEach(cat => {
                    if (!catLoadTmp[cat]) catLoadTmp[cat] = { label: cat==='—'?'Uncategorized':cat, value:0, color: catColors[cat]||'#94a3b8' };
                    catLoadTmp[cat].value += lv;
                });
            });
            const catLoads = Object.values(catLoadTmp);
            const pieSlices = mapLoadMode === 'category' ? catLoads : projLoads;
            const pieTotal = pieSlices.reduce((s,sl)=>s+sl.value,0)||1;
            const pieSvg = drawPie(pieSlices, 80, 80, 72);

            const totalPending = enriched.reduce((s,p) => s + p.todoTotal - p.todoDone, 0);
            const totalDone    = enriched.reduce((s,p) => s + p.todoDone, 0);
            const today = new Date().toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'});

            let html = `<div class="max-w-6xl mx-auto">
                <div class="flex items-start justify-between gap-6 mb-10 flex-wrap">
                    <div>
                        <h2 class="text-3xl font-black text-slate-900">Project Map</h2>
                        <p class="text-slate-400 mt-1 text-sm">${today}</p>
                        <div class="flex gap-8 mt-4">
                            <div class="text-right"><div class="text-2xl font-black text-slate-900">${projects.length}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Projects</div></div>
                            <div class="text-right"><div class="text-2xl font-black text-amber-500">${totalPending}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Open tasks</div></div>
                            <div class="text-right"><div class="text-2xl font-black text-emerald-500">${totalDone}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Completed</div></div>
                        </div>
                    </div>
                    <div class="bg-white rounded-2xl border border-slate-200 p-4 flex gap-5 items-start">
                        <div>
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Load</span>
                                <div class="flex bg-slate-100 p-0.5 rounded-md gap-0.5">
                                    <button onclick="setMapLoadMode('project')" class="px-2 py-0.5 text-[10px] font-bold rounded ${mapLoadMode==='project'?'nav-tab-active':'text-slate-400 hover:text-slate-600'}">Projects</button>
                                    <button onclick="setMapLoadMode('category')" class="px-2 py-0.5 text-[10px] font-bold rounded ${mapLoadMode==='category'?'nav-tab-active':'text-slate-400 hover:text-slate-600'}">Categories</button>
                                </div>
                            </div>
                            <svg width="160" height="160" viewBox="0 0 160 160">${pieSvg}</svg>
                        </div>
                        <div class="text-[10px] space-y-1.5 max-h-40 overflow-y-auto pr-1 pt-6">
                            ${pieSlices.map(sl=>`<div class="flex items-center gap-1.5"><div class="w-2 h-2 rounded-sm shrink-0" style="background:${sl.color}"></div><span class="text-slate-600 font-medium truncate max-w-[110px]">${sl.label}</span><span class="text-slate-400 font-mono ml-auto pl-2">${Math.round(sl.value/pieTotal*100)}%</span></div>`).join('')}
                        </div>
                    </div>
                </div>`;

            const sorted = Object.keys(catMap).sort((a,b) => a==='—'?1:b==='—'?-1:a.localeCompare(b));
            sorted.forEach(cat => {
                const cc   = catColors[cat];
                const list = catMap[cat];
                html += `<div class="mb-10">
                    <div class="flex items-center gap-3 mb-5">
                        <div class="w-2.5 h-2.5 rounded-sm" style="background:${cc}"></div>
                        <span class="text-xs font-black uppercase tracking-widest text-slate-500">${cat === '—' ? 'Uncategorized' : cat}</span>
                        <div class="flex-1 h-px bg-slate-200"></div>
                        <span class="text-xs text-slate-400">${list.length}</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">`;

                list.forEach(p => {
                    const pct = p.todoTotal > 0 ? Math.round((p.todoDone / p.todoTotal) * 100) : -1;
                    const dl  = p.latestDate ? p.latestDate.toLocaleDateString('en-GB',{day:'numeric',month:'short'}) : '';
                    const shortDesc = p.desc.length > 80 ? p.desc.substring(0,80) + '…' : p.desc;
                    const pCls = p.plainTags.includes('p1') ? ' priority-p1' : p.plainTags.includes('p2') ? ' priority-p2' : p.plainTags.includes('p3') ? ' priority-p3' : '';
                    html += `<div class="map-card bg-white rounded-xl border border-slate-200 p-4 cursor-pointer${pCls}" onclick="openPresentation('${p.id}')">
                        <div class="flex items-start justify-between gap-2 mb-1">
                            <h4 class="font-bold text-slate-900 text-sm leading-snug">${p.title}</h4>
                            ${p.status.label ? `<span class="text-[9px] font-black px-1.5 py-0.5 rounded-full text-white shrink-0" style="background:${p.status.color}">${p.status.label}</span>` : ''}
                        </div>
                        ${shortDesc ? `<p class="text-[11px] text-slate-400 italic mb-2 leading-relaxed">${shortDesc}</p>` : ''}
                        ${pct >= 0 ? `<div class="mb-3">
                            <div class="progress-track mb-1"><div class="progress-fill" style="width:${pct}%;background:${cc}"></div></div>
                            <div class="flex justify-between text-[9px] text-slate-300"><span>${p.todoDone}/${p.todoTotal} tasks</span><span>${pct}%</span></div>
                        </div>` : ''}
                        <div class="flex items-center justify-between mt-2">
                            <div class="flex flex-wrap gap-1">${p.plainTags.slice(0,3).map(t=>`<span class="text-[9px] font-bold px-1 py-0.5 bg-slate-100 text-slate-400 rounded">#${t}</span>`).join('')}</div>
                            ${dl ? `<span class="text-[9px] text-slate-300 font-mono shrink-0">${dl}</span>` : ''}
                        </div>
                    </div>`;
                });
                html += `</div></div>`;
            });
            html += `</div>`;
            document.getElementById('map-view').innerHTML = html;
        }

        // ── Network view ──────────────────────────────────────────────────────
        function renderNetwork() {
            const W = 1000, H = 660;
            const palette = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316'];
            const catColors = {}; let ci = 0;
            projects.forEach(p => {
                [...p.content.matchAll(/#cat:([\\w]+)/g)].map(m => m[1]).forEach(cat => {
                    if (!catColors[cat]) catColors[cat] = palette[ci++ % palette.length];
                });
            });

            const nodes = projects.map((proj, i) => {
                const cats = [...proj.content.matchAll(/#cat:([\\w]+)/g)].map(m => m[1]);
                const color = cats.length ? (catColors[cats[0]] || '#94a3b8') : '#94a3b8';
                const loadM = proj.content.match(/#load:(\\d+)/);
                const r = 14 + Math.min(loadM ? parseInt(loadM[1]) / 40 : 2.5, 14);
                return { id: proj.id, title: proj.title, color, r, x: 0, y: 0, vx: 0, vy: 0 };
            });

            const edges = [];
            projects.forEach((proj, i) => {
                [...proj.content.matchAll(/#proj:([\\w-]+)/g)].forEach(m => {
                    const j = projects.findIndex(p => p.id === m[1]);
                    if (j !== -1 && j !== i) edges.push([i, j]);
                });
            });

            const N = nodes.length, cx = W/2, cy = H/2, initR = Math.min(W,H)*0.32;
            nodes.forEach((n, i) => {
                n.x = cx + initR * Math.cos(2*Math.PI*i/N - Math.PI/2);
                n.y = cy + initR * Math.sin(2*Math.PI*i/N - Math.PI/2);
            });

            const REPEL=7000, SPRING=0.03, IDEAL=150, CENTER=0.005, DAMP=0.75;
            for (let iter = 0; iter < 80; iter++) {
                for (let i = 0; i < N; i++) for (let j = i+1; j < N; j++) {
                    const dx=nodes[j].x-nodes[i].x, dy=nodes[j].y-nodes[i].y;
                    const d2=dx*dx+dy*dy||1, d=Math.sqrt(d2), f=REPEL/d2;
                    nodes[i].vx-=f*dx/d; nodes[i].vy-=f*dy/d;
                    nodes[j].vx+=f*dx/d; nodes[j].vy+=f*dy/d;
                }
                edges.forEach(([i,j]) => {
                    const dx=nodes[j].x-nodes[i].x, dy=nodes[j].y-nodes[i].y;
                    const d=Math.sqrt(dx*dx+dy*dy)||1, f=(d-IDEAL)*SPRING;
                    nodes[i].vx+=f*dx/d; nodes[i].vy+=f*dy/d;
                    nodes[j].vx-=f*dx/d; nodes[j].vy-=f*dy/d;
                });
                nodes.forEach(n => {
                    n.vx+=(cx-n.x)*CENTER; n.vy+=(cy-n.y)*CENTER;
                    n.vx*=DAMP; n.vy*=DAMP;
                    n.x=Math.max(n.r+8,Math.min(W-n.r-8, n.x+n.vx));
                    n.y=Math.max(n.r+8,Math.min(H-n.r-8, n.y+n.vy));
                });
            }

            let edgeSvg = '';
            edges.forEach(([i,j]) => {
                const ni=nodes[i], nj=nodes[j];
                const dx=nj.x-ni.x, dy=nj.y-ni.y, d=Math.sqrt(dx*dx+dy*dy)||1;
                const sx=ni.x+dx/d*(ni.r+4), sy=ni.y+dy/d*(ni.r+4);
                const ex=nj.x-dx/d*(nj.r+6), ey=nj.y-dy/d*(nj.r+6);
                edgeSvg += `<line x1="${sx.toFixed(1)}" y1="${sy.toFixed(1)}" x2="${ex.toFixed(1)}" y2="${ey.toFixed(1)}" stroke="#cbd5e1" stroke-width="1.5" marker-end="url(#arr)"/>`;
            });

            let nodeSvg = '';
            nodes.forEach(n => {
                const lbl = n.title.length > 14 ? n.title.substring(0,14)+'…' : n.title;
                nodeSvg += `<g onclick="openPresentation('${n.id}')" style="cursor:pointer">
                    <circle cx="${n.x.toFixed(1)}" cy="${n.y.toFixed(1)}" r="${n.r}" fill="${n.color}" stroke="white" stroke-width="2.5" opacity="0.92"/>
                    <text x="${n.x.toFixed(1)}" y="${(n.y+n.r+13).toFixed(1)}" text-anchor="middle" font-size="10" fill="#334155" font-family="Inter,sans-serif" font-weight="600" style="pointer-events:none">${lbl}</text>
                </g>`;
            });

            const legendEntries = Object.entries(catColors);
            const noLinks = edges.length === 0;
            document.getElementById('network-view').innerHTML = `
                <div class="h-full flex flex-col">
                    <div class="flex items-start justify-between mb-3 shrink-0 flex-wrap gap-3">
                        <div>
                            <h2 class="text-2xl font-black text-slate-900">Network</h2>
                            <p class="text-sm text-slate-400">${N} project${N!==1?'s':''} · ${edges.length} link${edges.length!==1?'s':''}</p>
                            ${noLinks ? '<p class="text-xs text-slate-400 mt-1">No links yet — add <code class="bg-slate-100 px-1 rounded">#proj:project-id</code> in any project.</p>' : ''}
                        </div>
                        ${legendEntries.length ? `<div class="flex flex-wrap gap-3">${legendEntries.map(([cat,col])=>`<span class="flex items-center gap-1.5 text-xs font-bold text-slate-500"><span class="w-2.5 h-2.5 rounded-sm inline-block" style="background:${col}"></span>${cat}</span>`).join('')}<span class="flex items-center gap-1.5 text-xs font-bold text-slate-400"><span class="w-2.5 h-2.5 rounded-sm inline-block bg-slate-300"></span>Uncategorized</span></div>` : ''}
                    </div>
                    <div class="flex-1 bg-white rounded-2xl border border-slate-200 overflow-hidden">
                        <svg width="100%" height="100%" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
                            <defs><marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 Z" fill="#cbd5e1"/></marker></defs>
                            ${edgeSvg}${nodeSvg}
                        </svg>
                    </div>
                </div>`;
        }

        // ── Home / Dashboard view ─────────────────────────────────────────────
        function renderHome() {
            const today = new Date(); today.setHours(0,0,0,0);
            const allEvents = parseDates();

            // Future events: all dates >= today, ascending
            const upcoming = allEvents.filter(e => e.date >= today).slice(0, 20);

            // Recent activity: past dates (non-milestone, or milestone), descending, last 10
            const recent = allEvents.filter(e => e.date < today).reverse().slice(0, 10);

            // Open TODOs from non-done projects
            const todoGroups = parseTodos()
                .map(g => ({ ...g, items: g.items.filter(t => !t.done) }))
                .filter(g => {
                    const tags = [...g.proj.content.matchAll(/#(\\w+)/g)].map(m => m[1]);
                    return g.items.length > 0 && !tags.includes('done');
                });
            const totalPending = todoGroups.reduce((s, g) => s + g.items.length, 0);

            const dateLabel = today.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'});

            let upcomingHtml = '';
            if (!upcoming.length) {
                upcomingHtml = '<p class="text-slate-400 text-sm text-center py-6">No upcoming events.</p>';
            } else {
                upcoming.forEach(e => {
                    const isToday2 = e.date.toDateString() === today.toDateString();
                    const msColor  = e.milestoneDone ? '#10b981' : '#f7b705';
                    const dotEl    = e.isMilestone
                        ? `<div style="width:10px;height:10px;transform:rotate(45deg);background:${msColor};border-radius:2px;flex-shrink:0;margin-top:3px"></div>`
                        : `<div class="tl-dot" style="background:${e.color}"></div>`;
                    const badge    = e.isMilestone
                        ? `<span class="text-[9px] font-black px-1.5 py-0.5 rounded" style="${e.milestoneDone?'background:#d1fae5;color:#059669':'background:#fef9e7;color:#d4991a'}">◆ Milestone</span>`
                        : '';
                    const todayBadge = isToday2 ? '<span class="text-[9px] font-black px-1.5 py-0.5 rounded" style="background:#fef9e7;color:#d4991a">TODAY</span>' : '';
                    upcomingHtml += `<div class="flex items-start gap-3 py-2.5 border-b border-slate-50 last:border-0">
                        ${dotEl}
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xs font-mono font-bold" style="${isToday2?'color:#d4991a':'color:#94a3b8'}">${e.dateStr}</span>
                                ${todayBadge}${badge}
                                <button onclick="openPresentation('${e.projectId}')" class="text-[10px] font-bold px-2 py-0.5 rounded-full text-white hover:opacity-80" style="background:${e.color}">${e.projectTitle}</button>
                            </div>
                            ${e.context ? `<p class="text-sm text-slate-600 truncate mt-0.5">${e.context}</p>` : ''}
                        </div>
                    </div>`;
                });
            }

            let recentHtml = '';
            if (!recent.length) {
                recentHtml = '<p class="text-slate-400 text-sm text-center py-6">No past activity found.</p>';
            } else {
                recent.forEach(e => {
                    const msColor = e.milestoneDone ? '#10b981' : '#f7b705';
                    const dotEl   = e.isMilestone
                        ? `<div style="width:10px;height:10px;transform:rotate(45deg);background:${msColor};border-radius:2px;flex-shrink:0;margin-top:3px;opacity:0.6"></div>`
                        : `<div class="tl-dot" style="background:${e.color};opacity:0.45"></div>`;
                    recentHtml += `<div class="flex items-start gap-3 py-2.5 border-b border-slate-50 last:border-0 opacity-70">
                        ${dotEl}
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xs font-mono text-slate-400">${e.dateStr}</span>
                                <button onclick="openPresentation('${e.projectId}')" class="text-[10px] font-bold px-2 py-0.5 rounded-full text-white hover:opacity-80" style="background:${e.color}">${e.projectTitle}</button>
                            </div>
                            ${e.context ? `<p class="text-sm text-slate-500 truncate mt-0.5">${e.context}</p>` : ''}
                        </div>
                    </div>`;
                });
            }

            let todosHtml = '';
            if (!todoGroups.length) {
                todosHtml = '<p class="text-slate-400 text-sm text-center py-6">No open TODOs.</p>';
            } else {
                todoGroups.forEach(({ proj, pi, items }) => {
                    const col = COLORS[pi % COLORS.length];
                    todosHtml += `<div class="mb-3">
                        <div class="flex items-center gap-2 mb-1.5">
                            <div class="w-2 h-2 rounded-sm shrink-0" style="background:${col}"></div>
                            <button onclick="openModal('${proj.id}')" class="text-xs font-bold text-slate-700 hover:text-amber-600 transition-colors">${proj.title}</button>
                            <span class="text-[10px] text-slate-300">${items.length}</span>
                        </div>`;
                    items.slice(0, 4).forEach(({ lineIndex, task }) => {
                        const cleanTask = task.replace(/\\*\\*\\d{2}-\\d{2}-\\d{4}\\*\\*/g,'').replace(/\\*\\*/g,'').trim();
                        todosHtml += `<label class="flex items-center gap-2 pl-4 py-1 hover:bg-slate-50 rounded cursor-pointer">
                            <input type="checkbox" class="todo-checkbox" onchange="toggleTodo('${proj.id}',${lineIndex})">
                            <span class="text-xs text-slate-600 truncate">${cleanTask}</span>
                        </label>`;
                    });
                    if (items.length > 4) todosHtml += `<p class="pl-4 text-[10px] text-slate-300 italic">…and ${items.length - 4} more</p>`;
                    todosHtml += `</div>`;
                });
            }

            // Deadlines from #due: tags
            const deadlines = projects.map(p => {
                const dueM = p.content.match(/#due:(\\d{2}-\\d{2}-\\d{4})/);
                if (!dueM) return null;
                const [dd,mm,yyyy] = dueM[1].split('-');
                const dueDate = new Date(+yyyy, +mm-1, +dd);
                const diffMs  = dueDate - today;
                const diffD   = Math.round(diffMs / 86400000);
                const tags    = [...p.content.matchAll(/#(\\w+)/g)].map(m => m[1]);
                if (tags.includes('done')) return null;
                return { proj: p, dueDate, diffD, dueStr: dueM[1] };
            }).filter(Boolean).sort((a,b) => a.diffD - b.diffD);

            let deadlinesHtml = '';
            if (!deadlines.length) {
                deadlinesHtml = '<p class="text-slate-400 text-sm text-center py-6">No deadlines set. Add <code class="bg-slate-100 px-1 rounded">#due:dd-mm-yyyy</code> to any project.</p>';
            } else {
                deadlines.forEach(({ proj, diffD, dueStr }) => {
                    const isOverdue  = diffD < 0;
                    const isCritical = diffD >= 0 && diffD < 7;
                    const isWarning  = diffD >= 7 && diffD < 30;
                    const barColor   = isOverdue ? '#e11d48' : isCritical ? '#f97316' : isWarning ? '#f7b705' : '#10b981';
                    const label      = isOverdue ? `${-diffD}d overdue` : diffD === 0 ? 'Due today' : `${diffD}d left`;
                    deadlinesHtml += `<div class="flex items-center gap-3 py-2.5 border-b border-slate-50 last:border-0">
                        <div style="width:8px;height:8px;border-radius:50%;background:${barColor};flex-shrink:0"></div>
                        <div class="flex-1 min-w-0">
                            <button onclick="openPresentation('${proj.id}')" class="text-sm font-semibold text-slate-800 hover:text-amber-600 transition-colors truncate block">${proj.title}</button>
                            <span class="text-[10px] font-mono text-slate-400">${dueStr}</span>
                        </div>
                        <span class="text-[10px] font-black px-2 py-0.5 rounded-full flex-shrink-0" style="background:${barColor}20;color:${barColor}">${label}</span>
                    </div>`;
                });
            }

            document.getElementById('home-view').innerHTML = `
                <div class="max-w-6xl mx-auto">
                    <div class="mb-8 flex items-start justify-between flex-wrap gap-4">
                        <div>
                            <h2 class="text-3xl font-black text-slate-900">Good day</h2>
                            <p class="text-slate-400 mt-1 text-sm">${dateLabel}</p>
                        </div>
                        <button onclick="openQuickCapture()" class="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-amber-50 border border-slate-200 hover:border-amber-300 rounded-xl text-sm font-bold text-slate-600 hover:text-amber-700 transition-all" title="Press Q">
                            <span>⚡</span> Quick Capture <kbd class="ml-1 text-[9px] px-1.5 py-0.5 rounded bg-slate-200 font-mono">Q</kbd>
                        </button>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
                        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                            <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                                <h3 class="text-sm font-black text-slate-800 uppercase tracking-widest">Upcoming</h3>
                                <span class="text-[10px] font-bold text-slate-400">${upcoming.length} event${upcoming.length!==1?'s':''}</span>
                            </div>
                            <div class="px-5 py-2">${upcomingHtml}</div>
                        </div>
                        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                            <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                                <h3 class="text-sm font-black text-slate-800 uppercase tracking-widest">Open TODOs</h3>
                                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" style="background:#fef9e7;color:#d4991a">${totalPending}</span>
                            </div>
                            <div class="px-5 py-2 max-h-96 overflow-y-auto">${todosHtml}</div>
                        </div>
                        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                            <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                                <h3 class="text-sm font-black text-slate-800 uppercase tracking-widest">Recent Activity</h3>
                                <span class="text-[10px] font-bold text-slate-400">${recent.length} entries</span>
                            </div>
                            <div class="px-5 py-2">${recentHtml}</div>
                        </div>
                        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                            <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                                <h3 class="text-sm font-black text-slate-800 uppercase tracking-widest">Deadlines</h3>
                                <button onclick="setViewMode('gantt')" class="text-[10px] font-bold text-amber-500 hover:text-amber-700 transition-colors">Gantt →</button>
                            </div>
                            <div class="px-5 py-2 max-h-96 overflow-y-auto">${deadlinesHtml}</div>
                        </div>
                    </div>
                </div>`;
        }

        // ── Core render ───────────────────────────────────────────────────────
        function renderAll() {
            const svEl = document.getElementById('search-view');
            if (searchQuery.trim()) {
                document.getElementById('filter-bar').classList.add('hidden');
                ['board','list-view','todos-view','timeline-view','map-view','network-view','gantt-view','calendar-view'].forEach(id => { const el = document.getElementById(id); if (el) el.classList.add('hidden'); });
                svEl.classList.remove('hidden');
                renderSearch();
                return;
            }
            svEl.classList.add('hidden');
            const allTags = new Set();
            projects.forEach(p => [...p.content.matchAll(/#(\\w+)/g)].forEach(m => allTags.add(m[1])));

            const isFiltering = activeFilterTags.size > 0;
            document.getElementById('filter-clear-btn').innerHTML = `
                <div onclick="clearTagFilters()" class="filter-pill-clear ${!isFiltering ? 'active' : ''}">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
                        ${isFiltering ? '<path d="M6 18L18 6M6 6l12 12"/>' : ''}
                    </svg>
                </div>`;

            const ftEl = document.getElementById('filter-tags');
            ftEl.innerHTML = '';
            Array.from(allTags).sort().forEach((tag, i, arr) => {
                const isActive = activeFilterTags.has(tag);
                const isHidden = tag.startsWith('_');
                const pill = document.createElement('div');
                pill.className = `filter-pill ${isActive ? 'active' : ''} ${isHidden ? 'filter-pill-hidden' : ''}`;
                const icon = isActive ? '<svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>' : '';
                pill.innerHTML = icon + `<span>#${tag}</span>`;
                pill.onclick = () => toggleTagFilter(tag);
                ftEl.appendChild(pill);
                if (i < arr.length - 1) {
                    const sep = document.createElement('span');
                    sep.className = 'filter-separator';
                    sep.innerText = '|';
                    ftEl.appendChild(sep);
                }
            });

            const filtered = projects.filter(p => {
                const pTags = [...p.content.matchAll(/#(\\w+)/g)].map(m => m[1]);
                if (activeFilterTags.size > 0) return Array.from(activeFilterTags).every(t => pTags.includes(t));
                return !pTags.some(t => t.startsWith('_'));
            });

            if      (viewMode === 'home')     renderHome();
            else if (viewMode === 'board')    renderBoard(filtered);
            else if (viewMode === 'list')     renderList(filtered);
            else if (viewMode === 'todos')    renderTodos();
            else if (viewMode === 'timeline') renderTimeline();
            else if (viewMode === 'map')      renderBossMap();
            else if (viewMode === 'network')  renderNetwork();
            else if (viewMode === 'gantt')    renderGantt();
            else if (viewMode === 'calendar') renderCalendar();
        }

        function renderBoard(items) {
            const container = document.getElementById('board');
            container.innerHTML = '';
            items.forEach(proj => {
                const parts    = proj.content.split('---');
                const descLines = parts[0].split('\\n');
                const desc     = descLines.length > 1 ? descLines.slice(1).join('\\n').trim() : '';
                const body     = parts.slice(1).join('---').trim();
                const tags     = [...proj.content.matchAll(/#(\\w+)/g)].map(m => m[1]);
                const priorityCls = tags.includes('p1') ? ' priority-p1' : tags.includes('p2') ? ' priority-p2' : tags.includes('p3') ? ' priority-p3' : '';
                const col = document.createElement('div');
                col.className = 'project-column flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden shrink-0 transition-all hover:border-amber-400' + priorityCls;
                col.setAttribute('data-id', proj.id);
                col.innerHTML = `
                    <div class="p-6 border-b border-slate-50 relative bg-white">
                        <div class="flex justify-between items-start mb-2">
                            <h2 class="text-lg font-bold pr-12">${proj.title}</h2>
                            <div class="flex gap-1">
                                <button onclick="openPresentation('${proj.id}')" class="p-1 text-slate-300 hover:text-emerald-600" title="Presentation"><svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg></button>
                                <button onclick="openModal('${proj.id}')"        class="p-1 text-slate-300 hover:text-amber-500"  title="Edit"><svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>
                                <div class="p-1 cursor-move text-slate-200 hover:text-slate-400 handle"><svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M7 2a2 2 0 11.001 4.001A2 2 0 017 2zm0 6a2 2 0 11.001 4.001A2 2 0 017 8zm0 6a2 2 0 11.001 4.001A2 2 0 017 14zm6-12a2 2 0 11.001 4.001A2 2 0 0113 2zm0 6a2 2 0 11.001 4.001A2 2 0 0113 8zm0 6a2 2 0 11.001 4.001A2 2 0 0113 14z"/></svg></div>
                            </div>
                        </div>
                        <div class="text-xs text-slate-500 italic mb-3">${marked.parseInline(desc)}</div>
                        <div class="flex flex-wrap">${tags.map(t=>`<span class="${t.startsWith('_')?'bg-slate-100 text-slate-400 border border-slate-200':'bg-amber-50 text-amber-700'}" style="padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;text-transform:uppercase;margin-right:4px;margin-bottom:4px;">#${t}</span>`).join('')}</div>
                    </div>
                    <div class="p-6 overflow-y-auto flex-1 markdown-content bg-slate-50/20">${marked.parse(body)}</div>`;
                container.appendChild(col);
            });
            new Sortable(container, { animation:150, handle:'.handle', onEnd: async () => {
                const newVisibleIds      = Array.from(container.querySelectorAll('.project-column')).map(el => el.getAttribute('data-id'));
                const newVisibleProjects = newVisibleIds.map(id => projects.find(p => p.id === id));
                const visibleSet         = new Set(newVisibleIds);
                let vi = 0;
                projects = projects.map(p => visibleSet.has(p.id) ? newVisibleProjects[vi++] : p);
                fetch('/api/save-order', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(projects.map(p=>p.content)) });
            }});
        }

        function renderList(items) {
            const body = document.getElementById('list-body');
            body.innerHTML = '';
            items.forEach(proj => {
                const descParts = proj.content.split('---')[0].split('\\n');
                const desc  = descParts.length > 1 ? descParts.slice(1).join('\\n').trim() : '';
                const tags  = [...proj.content.matchAll(/#(\\w+)/g)].map(m => m[1]);
                const chars = proj.content.replace(/\\s/g,'').length;
                const loadM = proj.content.match(/#load:(\\d+)/);
                const load  = loadM ? parseInt(loadM[1]) : null;
                const loadHtml = load !== null
                    ? `<span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded" style="background:#fef9e7;color:#d4991a">${load}</span>`
                    : `<span class="text-[10px] font-mono text-slate-300">—</span>`;
                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-slate-50 cursor-pointer';
                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-slate-800">${proj.title}</td>
                    <td class="px-6 py-4 text-sm text-slate-500 italic">${marked.parseInline(desc)}</td>
                    <td class="px-6 py-4"><div class="flex flex-wrap gap-1">${tags.map(t=>`<span class="px-2 py-0.5 ${t.startsWith('_')?'bg-slate-50 text-slate-300':'bg-slate-100 text-slate-500'} rounded text-[10px] font-bold">#${t}</span>`).join('')}</div></td>
                    <td class="px-6 py-4 text-right">${loadHtml}</td>
                    <td class="px-6 py-4 text-right"><span class="text-[10px] font-mono bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded">${chars}ch</span></td>`;
                tr.onclick = () => setViewMode('board');
                body.appendChild(tr);
            });
        }

        // ── Gantt view ─────────────────────────────────────────────────────────
        const MS_PER_DAY = 86400000;

        function parseGanttData(proj) {
            const startM = proj.content.match(/#start:(\\d{2}-\\d{2}-\\d{4})/);
            const dueM   = proj.content.match(/#due:(\\d{2}-\\d{2}-\\d{4})/);
            function pd(s) { const [d,m,y]=s.split('-'); return new Date(+y,+m-1,+d); }

            const allDates = [...proj.content.matchAll(/\\*\\*(\\d{2}-\\d{2}-\\d{4})\\*\\*/g)].map(m=>pd(m[1]));
            let start = startM ? pd(startM[1]) : (allDates.length ? new Date(Math.min(...allDates)) : null);
            let end   = dueM   ? pd(dueM[1])   : (allDates.length ? new Date(Math.max(...allDates)) : null);
            if (start && end && start.getTime() === end.getTime()) end = new Date(end.getTime() + 7*MS_PER_DAY);

            const milestones = [];
            proj.content.split('\\n').forEach((line, li) => {
                const tM = line.match(/TODO:\\s*\\[([ x])\\]/i);
                const dM = line.match(/\\*\\*(\\d{2}-\\d{2}-\\d{4})\\*\\*/);
                if (tM && dM) milestones.push({
                    date: pd(dM[1]),
                    context: line.replace(/TODO:\\s*\\[[ x]\\]\\s*/gi,'').replace(/\\*\\*\\d{2}-\\d{2}-\\d{4}\\*\\*/g,'').replace(/[*#>`_]/g,'').trim(),
                    done: tM[1].toLowerCase()==='x', lineIndex: li
                });
            });

            const todos    = [...proj.content.matchAll(/TODO:\\s*\\[([ x])\\]/gi)];
            const todoDone = todos.filter(m=>m[1].toLowerCase()==='x').length;
            const allTags  = [...proj.content.matchAll(/#([a-zA-Z][\\w:]*)/g)].map(m=>m[1]);
            const cats     = allTags.filter(t=>t.startsWith('cat:')).map(t=>t.slice(4));
            const plainTags = allTags.filter(t=>!t.startsWith('cat:')&&!t.startsWith('proj:')&&!t.startsWith('load:')&&!t.startsWith('_'));
            const rawDesc  = (proj.content.split('---')[0]||'').split('\\n').slice(1).join(' ')
                .replace(/\\*\\*Short Desc:\\*\\*/gi,'').replace(/\\*\\*/g,'').trim();
            return { ...proj, start, end, milestones, cats: cats.length?cats:['—'], plainTags, todoDone, todoTotal: todos.length, desc: rawDesc, status: statusStyle(plainTags) };
        }

        function renderGantt() {
            const ganttData = projects.map(parseGanttData);
            const dated     = ganttData.filter(p => p.start && p.end);
            const undated   = ganttData.filter(p => !p.start || !p.end);
            const today     = new Date(); today.setHours(0,0,0,0);

            let minDate = new Date(today.getTime() - 30*MS_PER_DAY);
            let maxDate = new Date(today.getTime() + 90*MS_PER_DAY);
            dated.forEach(p => {
                if (p.start < minDate) minDate = new Date(p.start);
                if (p.end   > maxDate) maxDate = new Date(p.end);
            });
            minDate = new Date(minDate.getFullYear(), minDate.getMonth()-1, 1);
            maxDate = new Date(maxDate.getFullYear(), maxDate.getMonth()+2, 1);

            const ZOOM_PPD = { week:28, month:10, quarter:4 };
            const ppd      = ZOOM_PPD[ganttZoom] || 10;
            const SVG_W    = Math.max(700, Math.ceil((maxDate - minDate) / MS_PER_DAY * ppd));
            const ROW_H=42, BAR_H=18, AXIS_H=46, LABEL_W=210;
            function xp(d) { return (d - minDate) / MS_PER_DAY * ppd; }

            const palette = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316'];
            const catColors = {}; let gci = 0;
            ganttData.forEach(p => p.cats.forEach(cat => { if (cat!=='—'&&!catColors[cat]) catColors[cat]=palette[gci++%palette.length]; }));
            catColors['—'] = '#94a3b8';

            const rows = [];
            const catMap = {};
            dated.forEach(p => { const cat=p.cats[0]||'—'; if(!catMap[cat])catMap[cat]=[]; catMap[cat].push(p); });
            Object.keys(catMap).sort((a,b)=>a==='—'?1:b==='—'?-1:a.localeCompare(b)).forEach(cat => {
                rows.push({ type:'group', cat, color: catColors[cat]||'#94a3b8' });
                catMap[cat].forEach(p => rows.push({ type:'project', p, color: catColors[p.cats[0]||'—']||'#94a3b8' }));
            });
            if (undated.length) {
                rows.push({ type:'group', cat:'Undated', color:'#e2e8f0' });
                undated.forEach(p => rows.push({ type:'project', p, undated:true }));
            }

            const svgH = AXIS_H + rows.length * ROW_H + 8;

            const months = [];
            let cur = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
            while (cur < maxDate) { months.push(new Date(cur)); cur = new Date(cur.getFullYear(), cur.getMonth()+1, 1); }

            let axisSvg = '';
            months.forEach((m, i) => {
                const x1 = xp(m).toFixed(1);
                const nextM = months[i+1] || maxDate;
                const mx = ((xp(m)+xp(nextM))/2).toFixed(1);
                axisSvg += `<rect x="${x1}" y="0" width="${(xp(nextM)-xp(m)).toFixed(1)}" height="${AXIS_H}" fill="${i%2===0?'#f8fafc':'#f1f5f9'}"/>`;
                axisSvg += `<line x1="${x1}" y1="0" x2="${x1}" y2="${svgH}" stroke="#e2e8f0" stroke-width="0.5"/>`;
                axisSvg += `<text x="${mx}" y="28" text-anchor="middle" font-size="11" font-weight="700" fill="#64748b" font-family="Inter,sans-serif">${m.toLocaleDateString('en-GB',{month:'short',year:'numeric'})}</text>`;
            });
            const todayX = xp(today);
            axisSvg += `<line x1="${todayX.toFixed(1)}" y1="0" x2="${todayX.toFixed(1)}" y2="${svgH}" stroke="#f7b705" stroke-width="2" stroke-dasharray="4,3" opacity="0.85"/>`;
            axisSvg += `<text x="${todayX.toFixed(1)}" y="${AXIS_H-6}" text-anchor="middle" font-size="9" font-weight="900" fill="#f7b705" font-family="Inter,sans-serif">TODAY</text>`;

            let depSvg = '';
            dated.forEach(p => {
                [...p.content.matchAll(/#proj:([\\w-]+)/g)].forEach(m => {
                    const tgt = ganttData.find(gp=>gp.id===m[1]);
                    if (!tgt||!tgt.start||!p.end) return;
                    const fr = rows.findIndex(r=>r.type==='project'&&r.p&&r.p.id===p.id);
                    const to = rows.findIndex(r=>r.type==='project'&&r.p&&r.p.id===tgt.id);
                    if (fr<0||to<0) return;
                    const x1=xp(p.end).toFixed(1), x2=xp(tgt.start).toFixed(1);
                    const y1=(AXIS_H+fr*ROW_H+ROW_H/2).toFixed(1), y2=(AXIS_H+to*ROW_H+ROW_H/2).toFixed(1);
                    const cx1=(parseFloat(x1)+40).toFixed(1), cx2=(parseFloat(x2)-40).toFixed(1);
                    depSvg += `<path d="M ${x1} ${y1} C ${cx1} ${y1} ${cx2} ${y2} ${x2} ${y2}" stroke="#cbd5e1" stroke-width="1.5" fill="none" stroke-dasharray="4,3" marker-end="url(#gantt-arr)"/>`;
                });
            });

            let barSvg = '';
            rows.forEach((row, ri) => {
                const y = AXIS_H + ri * ROW_H;
                barSvg += `<rect x="0" y="${y}" width="${SVG_W}" height="${ROW_H}" fill="${ri%2===0?'rgba(248,250,252,0.5)':'transparent'}"/>`;
                if (row.type==='group') { barSvg += `<line x1="0" y1="${y+ROW_H-0.5}" x2="${SVG_W}" y2="${y+ROW_H-0.5}" stroke="#e2e8f0" stroke-width="1"/>`; return; }
                if (row.undated) return;
                const p=row.p, x1=xp(p.start), x2=xp(p.end), bw=Math.max(x2-x1,6), by=y+(ROW_H-BAR_H)/2;
                const bc = p.status.label==='Done'?'#10b981':p.status.label==='Active'?(row.color||'#f7b705'):p.status.label==='Hold'?'#94a3b8':p.status.label==='Backlog'?'#8b5cf6':(row.color||'#94a3b8');
                const pct = p.todoTotal>0 ? p.todoDone/p.todoTotal : (p.status.label==='Done'?1:0);
                const isHold = p.status.label==='Hold';
                barSvg += `<rect x="${x1.toFixed(1)}" y="${by.toFixed(1)}" width="${bw.toFixed(1)}" height="${BAR_H}" rx="4" fill="${bc}" opacity="${isHold?'0.15':'0.12'}"/>`;
                if (pct>0) barSvg += `<rect x="${x1.toFixed(1)}" y="${by.toFixed(1)}" width="${(bw*pct).toFixed(1)}" height="${BAR_H}" rx="4" fill="${bc}" opacity="${isHold?'0.35':'0.6'}"/>`;
                barSvg += `<rect x="${x1.toFixed(1)}" y="${by.toFixed(1)}" width="${bw.toFixed(1)}" height="${BAR_H}" rx="4" fill="none" stroke="${bc}" stroke-width="1.5" opacity="0.65"${isHold?' stroke-dasharray="5,3"':''}/>`;
                if (bw>50&&p.todoTotal>0) barSvg += `<text x="${(x1+bw/2).toFixed(1)}" y="${(by+BAR_H/2+3.5).toFixed(1)}" text-anchor="middle" font-size="9" font-weight="700" fill="${bc}" font-family="Inter,sans-serif">${Math.round(pct*100)}%</text>`;
                p.milestones.forEach(ms => {
                    const mx=xp(ms.date); if (mx<0||mx>SVG_W) return;
                    const mcy=y+ROW_H/2, mc=ms.done?'#10b981':'#f7b705';
                    barSvg += `<rect x="${(mx-5).toFixed(1)}" y="${(mcy-5).toFixed(1)}" width="10" height="10" transform="rotate(45,${mx.toFixed(1)},${mcy.toFixed(1)})" fill="${mc}" stroke="white" stroke-width="1.5" style="cursor:pointer" onclick="toggleTodo('${p.id}',${ms.lineIndex})"><title>${ms.context||'Milestone'}</title></rect>`;
                });
                barSvg += `<rect x="${x1.toFixed(1)}" y="${by.toFixed(1)}" width="${bw.toFixed(1)}" height="${BAR_H}" rx="4" fill="transparent" style="cursor:pointer" onclick="openPresentation('${p.id}')"/>`;
            });

            const labelHtml = rows.map(row => {
                if (row.type==='group') return `<div class="gantt-group-label" style="height:${ROW_H}px"><div style="width:8px;height:8px;border-radius:2px;background:${row.color};margin-right:8px;flex-shrink:0"></div><span style="font-size:10px;font-weight:900;letter-spacing:0.08em;text-transform:uppercase;color:#475569">${row.cat==='—'?'Uncategorized':row.cat}</span></div>`;
                const p=row.p, pct=p.todoTotal>0?Math.round(p.todoDone/p.todoTotal*100):-1;
                const dot = p.status.label ? `<span style="width:7px;height:7px;border-radius:50%;background:${p.status.color};flex-shrink:0;display:inline-block"></span>` : '';
                if (row.undated) return `<div class="gantt-row-label" style="height:${ROW_H}px;opacity:0.5" onclick="openModal('${p.id}')">${dot}<span style="font-size:12px;font-weight:600;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0">${p.title}</span><span style="font-size:9px;color:#94a3b8;flex-shrink:0">no dates</span></div>`;
                return `<div class="gantt-row-label" style="height:${ROW_H}px" onclick="openPresentation('${p.id}')">${dot}<span style="font-size:12px;font-weight:600;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0">${p.title}</span>${pct>=0?`<span style="font-size:9px;color:#94a3b8;flex-shrink:0;font-family:monospace">${pct}%</span>`:''}</div>`;
            }).join('');

            const zoomBtns = ['week','month','quarter'].map(z =>
                `<button onclick="ganttZoom='${z}';localStorage.setItem('ganttZoom','${z}');renderGantt()" style="padding:4px 14px;border-radius:6px;font-size:11px;font-weight:700;border:none;cursor:pointer;transition:all 0.15s;${ganttZoom===z?'background:#f7b705;color:#1c1917':'background:#f1f5f9;color:#64748b'}">${z.charAt(0).toUpperCase()+z.slice(1)}</button>`
            ).join('');

            document.getElementById('gantt-view').innerHTML = `
                <div style="height:100%;display:flex;flex-direction:column">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-shrink:0;flex-wrap:wrap;gap:8px">
                        <div>
                            <h2 style="font-size:1.5rem;font-weight:900;color:var(--text-primary)">Gantt Chart</h2>
                            <p style="font-size:11px;color:#94a3b8;margin-top:2px">${dated.length} project${dated.length!==1?'s':''} plotted &middot; tags: <code style="background:var(--bg-muted);padding:1px 5px;border-radius:3px">#start:dd-mm-yyyy</code> &middot; <code style="background:var(--bg-muted);padding:1px 5px;border-radius:3px">#due:dd-mm-yyyy</code></p>
                        </div>
                        <div style="display:flex;gap:4px;background:var(--bg-muted);padding:4px;border-radius:8px;border:1px solid var(--border)">${zoomBtns}</div>
                    </div>
                    <div style="flex:1;overflow:auto;border:1px solid var(--border);border-radius:16px;background:var(--bg-surface);display:flex;min-height:0">
                        <div style="width:${LABEL_W}px;flex-shrink:0;border-right:2px solid var(--border);position:sticky;left:0;background:var(--bg-surface);z-index:3">
                            <div style="height:${AXIS_H}px;display:flex;align-items:flex-end;padding:0 12px 8px;border-bottom:1px solid var(--border);font-size:10px;font-weight:900;letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8">Projects</div>
                            ${labelHtml}
                        </div>
                        <div style="flex:1;overflow-x:auto">
                            <svg width="${SVG_W}" height="${svgH}" xmlns="http://www.w3.org/2000/svg" style="display:block">
                                <defs><marker id="gantt-arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 Z" fill="#cbd5e1"/></marker></defs>
                                ${axisSvg}${depSvg}${barSvg}
                            </svg>
                        </div>
                    </div>
                </div>`;
        }

        // ── Calendar view ─────────────────────────────────────────────────────
        function renderCalendar() {
            const allEvents = parseDates();
            const year=calendarYear, month=calendarMonth;
            const firstDay = new Date(year, month, 1);
            const lastDay  = new Date(year, month+1, 0);
            const startDow = (firstDay.getDay() + 6) % 7; // 0=Mon
            const monthName = firstDay.toLocaleDateString('en-GB',{month:'long',year:'numeric'});
            const today = new Date(); today.setHours(0,0,0,0);

            const monthEvts = {};
            allEvents.forEach(e => {
                if (e.date.getFullYear()===year && e.date.getMonth()===month) {
                    const d = e.date.getDate();
                    if (!monthEvts[d]) monthEvts[d] = [];
                    monthEvts[d].push(e);
                }
            });

            const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
            let calHtml = `<div class="max-w-5xl mx-auto">
                <div class="flex items-center gap-4 mb-6">
                    <button onclick="calNavMonth(-1)" class="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-700"><svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg></button>
                    <h2 class="text-2xl font-black text-slate-900 flex-1 text-center">${monthName}</h2>
                    <button onclick="calNavMonth(1)" class="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-700"><svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></button>
                </div>
                <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div class="grid grid-cols-7 border-b border-slate-200">
                        ${DAYS.map(d=>`<div class="py-3 text-center text-xs font-black uppercase tracking-widest text-slate-400">${d}</div>`).join('')}
                    </div>
                    <div class="grid grid-cols-7">`;

            for (let i=0; i<startDow; i++) {
                const pd = new Date(year, month, -startDow+i+1);
                calHtml += `<div class="cal-day other-month"><div class="text-xs font-bold text-slate-300 mb-1">${pd.getDate()}</div></div>`;
            }
            for (let d=1; d<=lastDay.getDate(); d++) {
                const isToday = today.getFullYear()===year && today.getMonth()===month && today.getDate()===d;
                const evts = monthEvts[d] || [];
                calHtml += `<div class="cal-day${isToday?' today':''}">
                    <div class="text-xs font-bold mb-1 ${isToday?'text-amber-600':'text-slate-400'}">${d}${isToday?' ★':''}</div>`;
                evts.forEach(e => {
                    const msIcon = e.isMilestone ? '◆ ' : '';
                    calHtml += `<div class="cal-event" style="background:${e.color}22;color:${e.color};border:1px solid ${e.color}44" onclick="openPresentation('${e.projectId}')" title="${e.context||e.projectTitle}">${msIcon}${(e.context||e.projectTitle).substring(0,20)}</div>`;
                });
                calHtml += `</div>`;
            }
            const totalCells = startDow + lastDay.getDate();
            const trailing = (7 - (totalCells % 7)) % 7;
            for (let i=1; i<=trailing; i++) calHtml += `<div class="cal-day other-month"><div class="text-xs font-bold text-slate-300 mb-1">${i}</div></div>`;

            calHtml += `</div></div>
                <p class="text-center text-xs text-slate-300 mt-4">Click an event to open project · Dates from <code class="bg-slate-100 px-1 rounded">**dd-mm-yyyy**</code> markers · ◆ = milestone</p>
            </div>`;
            document.getElementById('calendar-view').innerHTML = calHtml;
        }

        function calNavMonth(delta) {
            calendarMonth += delta;
            if (calendarMonth > 11) { calendarMonth=0; calendarYear++; }
            if (calendarMonth < 0)  { calendarMonth=11; calendarYear--; }
            renderCalendar();
        }

        // ── Quick Capture ─────────────────────────────────────────────────────
        function openQuickCapture() {
            if (quickCaptureOpen) return;
            quickCaptureOpen = true;
            document.getElementById('quick-capture-panel').classList.add('open');
            setTimeout(() => { const el=document.getElementById('quick-capture-input'); if(el) el.focus(); }, 290);
        }

        function closeQuickCapture() {
            quickCaptureOpen = false;
            document.getElementById('quick-capture-panel').classList.remove('open');
            const el = document.getElementById('quick-capture-input');
            if (el) el.value = '';
        }

        function handleQuickCaptureKey(e) {
            if (e.key === 'Escape') { closeQuickCapture(); return; }
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); saveQuickCapture(); }
        }

        async function saveQuickCapture() {
            const el  = document.getElementById('quick-capture-input');
            const val = el ? el.value.trim() : '';
            if (!val) { closeQuickCapture(); return; }
            const today = new Date().toLocaleDateString('en-GB').replace(/\\//g,'-');
            const note  = '\\n\\n**' + today + '** ' + val;
            let inboxIdx = projects.findIndex(p => [...p.content.matchAll(/#(\\w+)/g)].map(m=>m[1]).includes('inbox'));
            if (inboxIdx < 0) {
                projects.push({ id:'inbox-'+Date.now(), title:'Inbox', content:'## Project: Inbox\\n**Short Desc:** Quick captures and fleeting notes.\\n---\\n#inbox\\n' });
                inboxIdx = projects.length - 1;
            }
            projects[inboxIdx].content += note;
            await fetch('/api/save-order', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(projects.map(p=>p.content)) });
            closeQuickCapture();
            await loadProjects();
        }

        let helpOpen = false;
        function openHelp() {
            helpOpen = true;
            const m = document.getElementById('help-modal');
            m.classList.remove('hidden');
            m.classList.add('flex');
        }
        function closeHelp() {
            helpOpen = false;
            const m = document.getElementById('help-modal');
            m.classList.add('hidden');
            m.classList.remove('flex');
        }

        document.addEventListener('keydown', e => {
            const tag = ((document.activeElement||{}).tagName||'').toUpperCase();
            const editorOpen = !document.getElementById('editor-modal').classList.contains('hidden');
            const presOpen   = !document.getElementById('presentation-modal').classList.contains('hidden');
            const inInput = ['INPUT','TEXTAREA'].includes(tag) || editorOpen || presOpen;
            if (e.key === 'q' && !inInput && !quickCaptureOpen && !helpOpen) { e.preventDefault(); openQuickCapture(); }
            if ((e.key === '?' || e.key === '/') && !inInput && !quickCaptureOpen && !helpOpen) { e.preventDefault(); openHelp(); }
            if (e.key === 'Escape' && quickCaptureOpen) closeQuickCapture();
            if (e.key === 'Escape' && helpOpen) closeHelp();
        });

        applyDarkMode();
        window.onload = loadProjects;
    </script>
</body>
</html>
"""

@app.route("/")
def index(): return render_template_string(HTML_TEMPLATE)

@app.route("/api/projects")
def get_projects(): return jsonify(read_projects())

@app.route("/api/save-order", methods=["POST"])
def save_order():
    save_projects_to_file(request.json)
    return jsonify({"status": "success"})

@app.route("/api/update-tags", methods=["POST"])
def update_tags():
    data = request.json  # {projectId, tagKey, tagValue}
    projects = read_projects()
    proj = next((p for p in projects if p['id'] == data['projectId']), None)
    if not proj:
        return jsonify({"status": "error", "msg": "project not found"}), 404
    tag_key = data['tagKey']   # e.g. "due" or "start"
    tag_val = data['tagValue'] # e.g. "30-07-2026"
    pattern = rf'#({re.escape(tag_key)}:\d{{2}}-\d{{2}}-\d{{4}})'
    replacement = f'#{tag_key}:{tag_val}'
    if re.search(pattern, proj['content']):
        proj['content'] = re.sub(pattern, replacement, proj['content'])
    else:
        # Append after first tag line
        lines = proj['content'].split('\n')
        for i, line in enumerate(lines):
            if re.search(r'#\w', line):
                lines[i] = lines[i] + f' #{tag_key}:{tag_val}'
                break
        proj['content'] = '\n'.join(lines)
    save_projects_to_file([p['content'] for p in projects])
    return jsonify({"status": "success"})

@app.route("/api/toggle-todo", methods=["POST"])
def toggle_todo():
    data = request.json
    projects = read_projects()
    proj = next((p for p in projects if p['id'] == data['projectId']), None)
    if not proj:
        return jsonify({"status": "error"}), 404
    lines = proj['content'].split('\n')
    li = data['lineIndex']
    if li < len(lines):
        line = lines[li]
        if re.search(r'TODO:\s*\[ \]', line, re.IGNORECASE):
            lines[li] = re.sub(r'TODO:\s*\[ \]', 'TODO: [x]', line, flags=re.IGNORECASE)
        elif re.search(r'TODO:\s*\[x\]', line, re.IGNORECASE):
            lines[li] = re.sub(r'TODO:\s*\[x\]', 'TODO: [ ]', line, flags=re.IGNORECASE)
        proj['content'] = '\n'.join(lines)
    save_projects_to_file([p['content'] for p in projects])
    return jsonify({"status": "success"})

@app.route("/raw")
def view_raw():
    if not os.path.exists(DB_FILE): return "File not found"
    with open(DB_FILE, "r", encoding="utf-8") as f: return f.read(), 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    app.run(debug=True)
