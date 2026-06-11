"""ProjectHub launcher — start server then choose TUI or browser."""
import atexit
import os
import socket
import subprocess
import sys
import time
import webbrowser

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

HUB_URL = os.environ.get("HUB_URL", "http://127.0.0.1:5000").rstrip("/")
_PORT = int(HUB_URL.rsplit(":", 1)[-1]) if ":" in HUB_URL.rsplit("/", 1)[-1] else 5000
_HERE = os.path.dirname(os.path.abspath(__file__))

console = Console()

_server_proc: subprocess.Popen | None = None
_server_owned = False  # True only if this launcher started the server


def _port_open() -> bool:
    host = "127.0.0.1"
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex((host, _PORT)) == 0


def _server_ready() -> bool:
    try:
        r = httpx.get(f"{HUB_URL}/api/projects", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def _start_server() -> bool:
    global _server_proc, _server_owned
    env = {**os.environ, "FLASK_DEBUG": "0"}
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    _server_proc = subprocess.Popen(
        [sys.executable, os.path.join(_HERE, "app.py")],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    _server_owned = True
    with console.status("[cyan]Starting server…[/cyan]"):
        for _ in range(27):  # up to ~8s
            time.sleep(0.3)
            if _server_proc.poll() is not None:
                return False  # process died
            if _server_ready():
                return True
    return False


def _stop_server() -> None:
    if _server_owned and _server_proc and _server_proc.poll() is None:
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _server_proc.kill()


atexit.register(_stop_server)


def _menu_panel(external: bool) -> Panel:
    origin = "[dim]external[/dim]" if external else "[green]managed[/green]"
    body = Text.assemble(
        ("  [1] ", "bold cyan"), ("TUI", "bold white"), ("  — terminal UI\n", "dim"),
        ("  [2] ", "bold cyan"), ("GUI", "bold white"), ("  — open browser\n", "dim"),
        ("  [q] ", "bold cyan"), ("Quit\n", "dim"),
    )
    title = Text.assemble(
        ("ProjectHub  ", "bold white"),
        (f"{HUB_URL}  ", "dim"),
        (f"({origin})", ""),
    )
    return Panel(body, title=title, border_style="bright_blue", padding=(0, 2))


def main() -> None:
    external = False

    if _port_open() and _server_ready():
        console.print("[yellow]Server already running[/yellow] — using existing instance.")
        external = True
    else:
        console.print("[cyan]Starting ProjectHub server…[/cyan]")
        if not _start_server():
            console.print("[red]Server failed to start.[/red] Check app.py for errors.")
            sys.exit(1)
        console.print("[green]Server ready.[/green]")

    while True:
        console.print()
        console.print(_menu_panel(external))
        try:
            choice = console.input("[bold cyan]>[/bold cyan] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye.[/dim]")
            break

        if choice == "1":
            console.print("[cyan]Launching TUI…[/cyan]")
            subprocess.run([sys.executable, os.path.join(_HERE, "tui.py")])
        elif choice == "2":
            webbrowser.open(HUB_URL)
            console.print(f"[green]Browser opened:[/green] {HUB_URL}")
        elif choice in ("q", "quit", "exit"):
            console.print("[dim]Shutting down.[/dim]")
            break
        else:
            console.print("[dim]Unknown choice — use 1, 2, or q.[/dim]")


if __name__ == "__main__":
    main()
