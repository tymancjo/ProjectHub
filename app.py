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

        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #1e293b; }
        .project-column { min-width: 380px; max-width: 380px; height: calc(100vh - 200px); }

        .markdown-content h1 { font-size: 2em; font-weight: 800; margin-bottom: 0.8em; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.4em; }
        .markdown-content h2 { font-size: 1.5em; font-weight: 700; margin-top: 1.2em; margin-bottom: 0.6em; color: #1e293b; border-bottom: 1px solid #f1f5f9; padding-bottom: 0.2em; }
        .markdown-content h3 { font-size: 1.2em; font-weight: 700; margin-top: 1em; margin-bottom: 0.4em; color: #334155; display: block; }
        .markdown-content p { margin-bottom: 1em; font-size: 1em; line-height: 1.6; color: #475569; }
        .markdown-content ul { list-style-type: disc !important; padding-left: 1.5em !important; margin-bottom: 1em !important; display: block !important; }
        .markdown-content ol { list-style-type: decimal !important; padding-left: 1.5em !important; margin-bottom: 1em !important; display: block !important; }
        .markdown-content li { font-size: 1em; color: #475569; margin-bottom: 0.4em; display: list-item !important; list-style: inherit !important; }
        .markdown-content code { background-color: #f1f5f9; padding: 0.2em 0.4em; border-radius: 4px; color: #be185d; font-family: monospace; font-size: 0.9em; }
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
                <button id="view-board"    onclick="setViewMode('board')"    class="px-4 py-1.5 rounded-md text-sm font-bold transition-all nav-tab-active">Board</button>
                <button id="view-list"     onclick="setViewMode('list')"     class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Overview</button>
                <button id="view-todos"    onclick="setViewMode('todos')"    class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">TODOs</button>
                <button id="view-timeline" onclick="setViewMode('timeline')" class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Timeline</button>
                <button id="view-map"      onclick="setViewMode('map')"      class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Map</button>
                <button id="view-network"  onclick="setViewMode('network')"  class="px-4 py-1.5 rounded-md text-sm font-bold transition-all text-slate-500 hover:text-slate-800">Network</button>
            </nav>
        </div>
        <div class="flex items-center gap-3">
            <div class="relative">
                <input id="search-input" type="text" placeholder="Search projects…"
                    oninput="onSearchInput(event)" onkeydown="onSearchKey(event)"
                    class="pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-amber-400 focus:bg-white w-48 transition-all" autocomplete="off">
                <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
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
        <div id="board"         class="flex-1 overflow-x-auto flex gap-6 p-8 items-start"></div>
        <div id="list-view"     class="hidden flex-1 overflow-y-auto p-8 max-w-6xl mx-auto w-full">
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Project</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Description</th>
                            <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tags</th>
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
        <div id="network-view" class="hidden flex-1 overflow-hidden p-6"></div>
    </main>

    <!-- Editor Modal -->
    <div id="editor-modal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex flex-col h-[85vh] overflow-hidden">
            <div class="px-6 py-4 border-b flex justify-between items-center bg-white">
                <div><h3 class="text-lg font-bold">Edit Project</h3><p class="text-xs text-slate-400">Markdown · <code>#tags</code> · <code>TODO: [ ] task</code> · <code>TODO: [ ] **date** = milestone</code> · <code>#cat:name</code> · <code>#proj:id</code> · <code>#load:N</code></p></div>
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

    <script>
        let projects = [];
        let currentEditingId = null;
        let viewMode = 'board';
        let activeFilterTags = new Set();
        let presentationFontSize = 18;
        let timelineMode = 'list';
        let timelineFilter = 'all';
        let searchQuery = '';
        let mapLoadMode = 'project';
        let cmEditor = null;
        let vimEnabled = localStorage.getItem('vimMode') === 'true';

        const COLORS = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#06b6d4','#64748b'];

        async function loadProjects() {
            const r = await fetch('/api/projects');
            projects = await r.json();
            renderAll();
        }

        // ── View mode ─────────────────────────────────────────────────────────
        function setViewMode(mode) {
            viewMode = mode;
            searchQuery = '';
            document.getElementById('search-input').value = '';
            const filterBound = ['board', 'list'];
            document.getElementById('filter-bar').classList.toggle('hidden', !filterBound.includes(mode));
            ['board','list','todos','timeline','map','network'].forEach(v => {
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

            // Load chart data — exclude #done projects
            const activeEnriched = enriched.filter(p => !p.plainTags.includes('done'));
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
                    html += `<div class="map-card bg-white rounded-xl border border-slate-200 p-4 cursor-pointer" onclick="openPresentation('${p.id}')">
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

        // ── Core render ───────────────────────────────────────────────────────
        function renderAll() {
            const svEl = document.getElementById('search-view');
            if (searchQuery.trim()) {
                document.getElementById('filter-bar').classList.add('hidden');
                ['board','list-view','todos-view','timeline-view','map-view','network-view'].forEach(id => { const el = document.getElementById(id); if (el) el.classList.add('hidden'); });
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

            if      (viewMode === 'board')    renderBoard(filtered);
            else if (viewMode === 'list')     renderList(filtered);
            else if (viewMode === 'todos')    renderTodos();
            else if (viewMode === 'timeline') renderTimeline();
            else if (viewMode === 'map')      renderBossMap();
            else if (viewMode === 'network')  renderNetwork();
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
                const col = document.createElement('div');
                col.className = 'project-column flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden shrink-0 transition-all hover:border-amber-400';
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
                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-slate-50 cursor-pointer';
                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-slate-800">${proj.title}</td>
                    <td class="px-6 py-4 text-sm text-slate-500 italic">${marked.parseInline(desc)}</td>
                    <td class="px-6 py-4"><div class="flex flex-wrap gap-1">${tags.map(t=>`<span class="px-2 py-0.5 ${t.startsWith('_')?'bg-slate-50 text-slate-300':'bg-slate-100 text-slate-500'} rounded text-[10px] font-bold">#${t}</span>`).join('')}</div></td>
                    <td class="px-6 py-4 text-right"><span class="text-[10px] font-mono bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded">${chars}ch</span></td>`;
                tr.onclick = () => setViewMode('board');
                body.appendChild(tr);
            });
        }

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
