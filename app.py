import os
import re
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_DIR = "db"
DB_FILE = os.path.join(DB_DIR, "projects.md")

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
        #modal-textarea { font-family: 'JetBrains Mono', monospace; line-height: 1.6; background-color: #0f172a; color: #f1f5f9; caret-color: #f7b705; }

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
            </nav>
        </div>
        <div>
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
    </main>

    <!-- Editor Modal -->
    <div id="editor-modal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex flex-col h-[85vh] overflow-hidden">
            <div class="px-6 py-4 border-b flex justify-between items-center bg-white">
                <div><h3 class="text-lg font-bold">Edit Project</h3><p class="text-xs text-slate-400">Markdown · <code>#tags</code> · <code>TODO: [ ] task</code> · <code>#cat:name</code></p></div>
                <div class="flex items-center gap-2">
                    <button onclick="insertDateAtCursor()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold border">📅 Date</button>
                    <button onclick="closeModal()" class="p-2 hover:bg-slate-100 rounded-full text-slate-400">
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                </div>
            </div>
            <textarea id="modal-textarea" class="flex-1 p-8 outline-none resize-none"></textarea>
            <div class="p-4 border-t bg-slate-50 flex justify-end gap-3">
                <button onclick="closeModal()" class="px-4 py-2 font-semibold text-slate-600">Cancel</button>
                <button onclick="saveProjectUpdate()" class="px-8 py-2 btn-accent font-bold rounded-lg shadow-md">Save Changes</button>
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
            <button onclick="closePresentation()" class="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
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

        const COLORS = ['#f7b705','#10b981','#e11d48','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#06b6d4','#64748b'];

        async function loadProjects() {
            const r = await fetch('/api/projects');
            projects = await r.json();
            renderAll();
        }

        // ── View mode ─────────────────────────────────────────────────────────
        function setViewMode(mode) {
            viewMode = mode;
            const filterBound = ['board', 'list'];
            document.getElementById('filter-bar').classList.toggle('hidden', !filterBound.includes(mode));
            ['board','list','todos','timeline','map'].forEach(v => {
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
            document.getElementById('modal-textarea').value = projects.find(p => p.id === id).content;
            document.getElementById('editor-modal').classList.remove('hidden');
        }
        function closeModal() { document.getElementById('editor-modal').classList.add('hidden'); currentEditingId = null; }

        function openPresentation(id) {
            const proj = projects.find(p => p.id === id);
            const body = proj.content.split('---').slice(-1)[0].trim();
            document.getElementById('pres-title').innerText = proj.title;
            document.getElementById('presentation-content').innerHTML = marked.parse(body);
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
            const ta = document.getElementById('modal-textarea');
            const ds = `**${new Date().toLocaleDateString('en-GB').replace(/\\//g, '-')}**`;
            const s = ta.selectionStart;
            ta.value = ta.value.substring(0, s) + ds + ta.value.substring(ta.selectionEnd);
            ta.selectionStart = ta.selectionEnd = s + ds.length;
            ta.focus();
        }

        async function saveProjectUpdate() {
            const idx = projects.findIndex(p => p.id === currentEditingId);
            if (idx !== -1) projects[idx].content = document.getElementById('modal-textarea').value;
            await fetch('/api/save-order', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(projects.map(p => p.content)) });
            closeModal();
            loadProjects();
        }

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
                proj.content.split('\\n').forEach(line => {
                    [...line.matchAll(/\\*\\*(\\d{2}-\\d{2}-\\d{4})\\*\\*/g)].forEach(m => {
                        const [dd, mm, yyyy] = m[1].split('-');
                        const date = new Date(+yyyy, +mm - 1, +dd);
                        const ctx  = line.replace(/\\*\\*\\d{2}-\\d{2}-\\d{4}\\*\\*/g, '').replace(/[*#>`_]/g, '').trim();
                        events.push({ date, dateStr: m[1], context: ctx || proj.title, projectId: proj.id, projectTitle: proj.title, color });
                    });
                });
            });
            return events.sort((a, b) => a.date - b.date);
        }

        function setTimelineMode(mode) { timelineMode = mode; renderTimeline(); }

        function renderTimeline() {
            if (timelineMode === 'grid') renderTimelineGrid();
            else renderTimelineList();
        }

        function renderTimelineList() {
            const events = parseDates();
            const today  = new Date(); today.setHours(0,0,0,0);

            if (!events.length) {
                document.getElementById('timeline-view').innerHTML =
                    '<p class="text-slate-400 text-center mt-16 text-sm">No dates found. Use <strong>**dd-mm-yyyy**</strong> in notes, or click 📅 in the editor.</p>';
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
                    <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                        <button class="px-3 py-1.5 text-xs font-bold rounded-md nav-tab-active">List</button>
                        <button onclick="setTimelineMode('grid')" class="px-3 py-1.5 text-xs font-bold rounded-md text-slate-500 hover:text-slate-800">Grid</button>
                    </div>
                </div>`;

            Object.values(months).forEach(month => {
                html += `<div class="tl-month">${month.label}</div>`;
                month.events.forEach((e, idx) => {
                    const isPast  = e.date < today;
                    const isToday = e.date.toDateString() === today.toDateString();
                    const isLast  = idx === month.events.length - 1;
                    html += `<div class="flex gap-4 ${isPast && !isToday ? 'opacity-50' : ''}">
                        <div class="flex flex-col items-center w-4">
                            <div class="tl-dot" style="background:${e.color}"></div>
                            ${!isLast ? '<div class="tl-line"></div>' : ''}
                        </div>
                        <div class="pb-4 flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap mb-0.5">
                                <span class="text-xs font-mono font-bold" style="${isToday ? 'color:#d4991a' : 'color:#94a3b8'}">${e.dateStr}</span>
                                ${isToday ? '<span class="text-[9px] font-black px-1.5 py-0.5 rounded tracking-wide" style="background:#fef9e7;color:#d4991a">TODAY</span>' : ''}
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
            const events = parseDates();
            const today  = new Date(); today.setHours(0,0,0,0);

            if (!events.length) {
                document.getElementById('timeline-view').innerHTML =
                    '<p class="text-slate-400 text-center mt-16 text-sm">No dates found. Use <strong>**dd-mm-yyyy**</strong> in notes, or click 📅 in the editor.</p>';
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
                <div class="flex bg-slate-100 p-1 rounded-lg gap-0.5">
                    <button onclick="setTimelineMode('list')" class="px-3 py-1.5 text-xs font-bold rounded-md text-slate-500 hover:text-slate-800">List</button>
                    <button class="px-3 py-1.5 text-xs font-bold rounded-md nav-tab-active">Grid</button>
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
                    const dotClr = e.isPast && !e.isToday ? '#cbd5e1' : e.color;
                    const txtClr = e.isPast && !e.isToday ? '#94a3b8' : e.color;
                    const short  = e.context.length > 18 ? e.context.substring(0,18)+'…' : e.context;
                    pins += `<div class="absolute flex flex-col items-center" style="left:${e.pct}%;top:${topPx}px;transform:translateX(-50%);z-index:1">
                        <button onclick="openPresentation('${e.projectId}')" class="w-3 h-3 rounded-full border-2 border-white shadow-sm hover:scale-125 transition-transform" style="background:${dotClr}" title="${e.context} (${e.dateStr})"></button>
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
                const plainTags = allTags.filter(t => !t.startsWith('cat:') && !t.startsWith('_'));
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

            const totalPending = enriched.reduce((s,p) => s + p.todoTotal - p.todoDone, 0);
            const totalDone    = enriched.reduce((s,p) => s + p.todoDone, 0);
            const today = new Date().toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'});

            let html = `<div class="max-w-6xl mx-auto">
                <div class="flex items-end justify-between mb-10">
                    <div>
                        <h2 class="text-3xl font-black text-slate-900">Project Map</h2>
                        <p class="text-slate-400 mt-1 text-sm">${today}</p>
                    </div>
                    <div class="flex gap-8">
                        <div class="text-right"><div class="text-2xl font-black text-slate-900">${projects.length}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Projects</div></div>
                        <div class="text-right"><div class="text-2xl font-black text-amber-500">${totalPending}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Open tasks</div></div>
                        <div class="text-right"><div class="text-2xl font-black text-emerald-500">${totalDone}</div><div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">Completed</div></div>
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

        // ── Core render ───────────────────────────────────────────────────────
        function renderAll() {
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
                const ids = Array.from(container.querySelectorAll('.project-column')).map(el => el.getAttribute('data-id'));
                projects = ids.map(id => projects.find(p => p.id === id));
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
