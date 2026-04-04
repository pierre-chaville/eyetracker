"""
Eye Tracker Station – Launcher
Tkinter GUI to start / stop / update all components of the eye-tracking app.

Components managed:
  • Backend   – Python FastAPI (uvicorn) on port 8080
  • Frontend  – Vue / Vite dev server on port 5173
  • Bridge    – C# .NET Tobii gaze WebSocket bridge on port 8765
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tkinter import messagebox, scrolledtext
import tkinter as tk
from typing import Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

LAUNCHER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = LAUNCHER_DIR.parent

BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BRIDGE_DIR = PROJECT_ROOT / "bridge"

VENV_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
SYSTEM_PYTHON = sys.executable
NPM_CMD = "npm.cmd" if sys.platform == "win32" else "npm"
DOTNET_CMD = "dotnet"
GIT_CMD = "git"

# Fallback: if venv doesn't exist, use the current Python
def _python_exe() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return SYSTEM_PYTHON


def _find_browser() -> Optional[str]:
    """Find Chrome or Edge executable for --app mode."""
    candidates = []
    if sys.platform == "win32":
        for env_var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env_var, "")
            if base:
                candidates += [
                    Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe",
                    Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                ]
    else:
        for name in ("google-chrome", "google-chrome-stable", "chromium", "microsoft-edge"):
            found = shutil.which(name)
            if found:
                return found
    for p in candidates:
        if p.exists():
            return str(p)
    return None


# ---------------------------------------------------------------------------
# Colours / theme
# ---------------------------------------------------------------------------

BG = "#1e1e2e"
BG_LIGHT = "#2a2a3c"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
BLUE = "#89b4fa"
MAUVE = "#cba6f7"
TEAL = "#94e2d5"
PEACH = "#fab387"
SURFACE = "#313244"
OVERLAY = "#45475a"

FONT_FAMILY = "Segoe UI"
FONT = (FONT_FAMILY, 11)
FONT_BOLD = (FONT_FAMILY, 11, "bold")
FONT_LOG = ("Consolas", 10)
FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_STATUS = (FONT_FAMILY, 10)
FONT_BTN = (FONT_FAMILY, 12, "bold")


# ---------------------------------------------------------------------------
# Service definitions
# ---------------------------------------------------------------------------

class ServiceState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


STATE_COLOUR = {
    ServiceState.STOPPED: FG_DIM,
    ServiceState.STARTING: YELLOW,
    ServiceState.RUNNING: GREEN,
    ServiceState.ERROR: RED,
}

STATE_LABEL = {
    ServiceState.STOPPED: "Stopped",
    ServiceState.STARTING: "Starting…",
    ServiceState.RUNNING: "Running",
    ServiceState.ERROR: "Error",
}


@dataclass
class ServiceDef:
    name: str
    short: str
    colour: str
    cmd: list[str]
    cwd: Path
    ready_pattern: Optional[str] = None
    port: Optional[int] = None


SERVICES: Dict[str, ServiceDef] = {
    "backend": ServiceDef(
        name="Backend (FastAPI)",
        short="Backend",
        colour=BLUE,
        cmd=[],  # filled dynamically
        cwd=BACKEND_DIR,
        ready_pattern=r"Uvicorn running on|Application startup complete",
        port=8080,
    ),
    "frontend": ServiceDef(
        name="Frontend (Vite)",
        short="Frontend",
        colour=TEAL,
        cmd=[NPM_CMD, "run", "dev"],
        cwd=FRONTEND_DIR,
        ready_pattern=r"Local:.*http|ready in",
        port=5173,
    ),
    "bridge": ServiceDef(
        name="Bridge (Tobii C#)",
        short="Bridge",
        colour=MAUVE,
        cmd=[DOTNET_CMD, "run"],
        cwd=BRIDGE_DIR,
        ready_pattern=r"WebSocket server|Listening|Started",
        port=8765,
    ),
}


# ---------------------------------------------------------------------------
# Process wrapper
# ---------------------------------------------------------------------------

class ManagedProcess:
    """Wraps a subprocess with state tracking and async log reading."""

    def __init__(self, key: str, svc: ServiceDef, on_log: Callable, on_state: Callable):
        self.key = key
        self.svc = svc
        self._on_log = on_log
        self._on_state = on_state
        self.proc: Optional[subprocess.Popen] = None
        self.state = ServiceState.STOPPED
        self._reader_thread: Optional[threading.Thread] = None

    def start(self):
        if self.proc and self.proc.poll() is None:
            self._log("Already running.")
            return
        cmd = list(self.svc.cmd)
        if self.key == "backend":
            cmd = [_python_exe(), "-m", "uvicorn", "main:app", "--reload", "--port", "8080"]
        self._set_state(ServiceState.STARTING)
        self._log(f"Starting: {' '.join(cmd)}")
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.proc = subprocess.Popen(
                cmd,
                cwd=str(self.svc.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
            )
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()
        except FileNotFoundError as exc:
            self._log(f"ERROR: command not found – {exc}")
            self._set_state(ServiceState.ERROR)
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            self._set_state(ServiceState.ERROR)

    def stop(self):
        if not self.proc:
            self._set_state(ServiceState.STOPPED)
            return
        self._log("Stopping…")
        try:
            if sys.platform == "win32":
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._log("Force-killing process…")
                self.proc.kill()
                self.proc.wait(timeout=3)
        except Exception as exc:
            self._log(f"Error stopping: {exc}")
            try:
                self.proc.kill()
            except Exception:
                pass
        finally:
            self.proc = None
            self._set_state(ServiceState.STOPPED)
            self._log("Stopped.")

    @property
    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def _read_output(self):
        """Background thread: streams stdout and detects ready state."""
        try:
            for line in self.proc.stdout:
                stripped = line.rstrip("\n\r")
                self._log(stripped)
                if (
                    self.state == ServiceState.STARTING
                    and self.svc.ready_pattern
                    and re.search(self.svc.ready_pattern, stripped, re.IGNORECASE)
                ):
                    self._set_state(ServiceState.RUNNING)
        except Exception:
            pass
        finally:
            if self.proc and self.proc.poll() is not None:
                code = self.proc.returncode
                if self.state != ServiceState.STOPPED:
                    if code == 0:
                        self._set_state(ServiceState.STOPPED)
                        self._log("Process exited normally.")
                    else:
                        self._set_state(ServiceState.ERROR)
                        self._log(f"Process exited with code {code}.")

    def _log(self, text: str):
        self._on_log(self.key, text)

    def _set_state(self, state: ServiceState):
        self.state = state
        self._on_state(self.key, state)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class LauncherApp:
    """Tkinter application managing all services."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Eye Tracker Station – Launcher")
        self.root.configure(bg=BG)
        self.root.geometry("900x680")
        self.root.minsize(700, 500)

        self._processes: Dict[str, ManagedProcess] = {}
        self._status_labels: Dict[str, tk.Label] = {}
        self._status_dots: Dict[str, tk.Label] = {}
        self._toggle_btns: Dict[str, tk.Button] = {}
        self._updating = False

        self._build_ui()
        self._init_processes()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- UI construction ----------------------------------------------------

    def _build_ui(self):
        # Title bar
        title_frame = tk.Frame(self.root, bg=BG)
        title_frame.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(
            title_frame, text="Eye Tracker Station", font=FONT_TITLE,
            bg=BG, fg=FG,
        ).pack(side="left")
        tk.Label(
            title_frame, text=f"  {PROJECT_ROOT}", font=FONT_STATUS,
            bg=BG, fg=FG_DIM,
        ).pack(side="left", padx=(8, 0))

        # Status panel
        status_frame = tk.Frame(self.root, bg=BG_LIGHT, highlightbackground=OVERLAY, highlightthickness=1)
        status_frame.pack(fill="x", padx=20, pady=(0, 8))
        for key, svc in SERVICES.items():
            row = tk.Frame(status_frame, bg=BG_LIGHT)
            row.pack(fill="x", padx=12, pady=6)

            dot = tk.Label(row, text="\u25cf", font=(FONT_FAMILY, 14), bg=BG_LIGHT, fg=FG_DIM)
            dot.pack(side="left")
            self._status_dots[key] = dot

            tk.Label(
                row, text=svc.name, font=FONT_BOLD, bg=BG_LIGHT, fg=svc.colour,
                width=22, anchor="w",
            ).pack(side="left", padx=(6, 0))

            state_lbl = tk.Label(
                row, text=STATE_LABEL[ServiceState.STOPPED], font=FONT_STATUS,
                bg=BG_LIGHT, fg=FG_DIM, width=10, anchor="w",
            )
            state_lbl.pack(side="left", padx=(4, 0))
            self._status_labels[key] = state_lbl

            port_text = f":{svc.port}" if svc.port else ""
            tk.Label(
                row, text=port_text, font=FONT_STATUS, bg=BG_LIGHT, fg=FG_DIM,
            ).pack(side="left", padx=(2, 0))

            btn = tk.Button(
                row, text="Start", font=FONT, bg=SURFACE, fg=GREEN,
                activebackground=OVERLAY, activeforeground=GREEN,
                relief="flat", padx=14, pady=2, cursor="hand2",
                command=lambda k=key: self._toggle_service(k),
            )
            btn.pack(side="right", padx=4)
            self._toggle_btns[key] = btn

        # Log area
        log_frame = tk.Frame(self.root, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.log_area = scrolledtext.ScrolledText(
            log_frame, font=FONT_LOG, bg="#11111b", fg=FG,
            insertbackground=FG, relief="flat", borderwidth=0,
            wrap="word", state="disabled",
        )
        self.log_area.pack(fill="both", expand=True)

        # Configure log tag colours per service
        self.log_area.tag_configure("backend", foreground=BLUE)
        self.log_area.tag_configure("frontend", foreground=TEAL)
        self.log_area.tag_configure("bridge", foreground=MAUVE)
        self.log_area.tag_configure("system", foreground=PEACH)
        self.log_area.tag_configure("error", foreground=RED)
        self.log_area.tag_configure("success", foreground=GREEN)

        # Button bar
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        buttons = [
            ("Launch All", GREEN, self._start_all),
            ("Stop All", RED, self._stop_all),
            ("Update", YELLOW, self._update),
            ("Open Browser", BLUE, self._open_browser),
            ("Clear Log", FG_DIM, self._clear_log),
            ("Shutdown", RED, self._shutdown),
        ]
        for text, colour, cmd in buttons:
            b = tk.Button(
                btn_frame, text=text, font=FONT_BTN,
                bg=SURFACE, fg=colour,
                activebackground=OVERLAY, activeforeground=colour,
                relief="flat", padx=20, pady=10, cursor="hand2",
                command=cmd,
            )
            b.pack(side="left", padx=4, expand=True, fill="x")

    # -- Process management -------------------------------------------------

    def _init_processes(self):
        for key, svc in SERVICES.items():
            self._processes[key] = ManagedProcess(
                key, svc,
                on_log=self._append_log,
                on_state=self._update_state_ui,
            )

    def _toggle_service(self, key: str):
        mp = self._processes[key]
        if mp.is_running:
            threading.Thread(target=mp.stop, daemon=True).start()
        else:
            mp.start()

    def _start_all(self):
        def _do():
            for key in ("backend", "frontend", "bridge"):
                mp = self._processes[key]
                if not mp.is_running:
                    mp.start()
                    time.sleep(0.5)
        threading.Thread(target=_do, daemon=True).start()

    def _stop_all(self):
        def _do():
            for key in reversed(list(SERVICES.keys())):
                self._processes[key].stop()
        threading.Thread(target=_do, daemon=True).start()

    # -- Update -------------------------------------------------------------

    def _update(self):
        if self._updating:
            self._system_log("Update already in progress.")
            return

        any_running = any(mp.is_running for mp in self._processes.values())
        if any_running:
            if not messagebox.askyesno(
                "Services running",
                "Some services are still running.\nStop them and proceed with the update?",
            ):
                return
            self._stop_all_sync()

        self._updating = True
        threading.Thread(target=self._do_update, daemon=True).start()

    def _stop_all_sync(self):
        for key in reversed(list(SERVICES.keys())):
            self._processes[key].stop()

    def _do_update(self):
        try:
            self._system_log("=" * 50)
            self._system_log("STARTING UPDATE")
            self._system_log("=" * 50)

            # Git pull
            self._system_log("\n[1/4] Git pull…")
            ok = self._run_sync([GIT_CMD, "pull"], PROJECT_ROOT)
            if not ok:
                self._log_error("Git pull failed. Aborting update.")
                return

            # Python dependencies
            self._system_log("\n[2/4] Installing Python dependencies…")
            self._run_sync(
                [_python_exe(), "-m", "pip", "install", "-r", "requirements.txt"],
                BACKEND_DIR,
            )

            # NPM dependencies
            self._system_log("\n[3/4] Installing NPM dependencies…")
            self._run_sync([NPM_CMD, "install"], FRONTEND_DIR)

            # Bridge build
            if BRIDGE_DIR.exists() and (BRIDGE_DIR / "GazeSpeakerBridge.csproj").exists():
                self._system_log("\n[4/4] Building C# bridge…")
                self._run_sync([DOTNET_CMD, "build"], BRIDGE_DIR)
            else:
                self._system_log("\n[4/4] Bridge not found, skipping.")

            self._system_log("\n" + "=" * 50)
            self._log_success("UPDATE COMPLETE")
            self._system_log("=" * 50)
            self.root.after(0, lambda: messagebox.showinfo("Update", "Update completed successfully."))

        except Exception as exc:
            self._log_error(f"Update error: {exc}")
        finally:
            self._updating = False

    def _run_sync(self, cmd: list[str], cwd: Path) -> bool:
        """Run a command synchronously, streaming output to the log. Returns True on success."""
        self._system_log(f"  $ {' '.join(cmd)}")
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(cwd),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                self._append_log("system", f"  {line.rstrip()}")
            proc.wait()
            if proc.returncode != 0:
                self._log_error(f"  Command exited with code {proc.returncode}")
                return False
            return True
        except FileNotFoundError:
            self._log_error(f"  Command not found: {cmd[0]}")
            return False
        except Exception as exc:
            self._log_error(f"  Error: {exc}")
            return False

    # -- Logging ------------------------------------------------------------

    def _append_log(self, tag: str, text: str):
        """Thread-safe log append."""
        prefix = f"[{SERVICES[tag].short}] " if tag in SERVICES else ""

        def _do():
            self.log_area.configure(state="normal")
            self.log_area.insert("end", f"{prefix}{text}\n", tag)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

        self.root.after(0, _do)

    def _system_log(self, text: str):
        self._append_log("system", text)

    def _log_error(self, text: str):
        self._append_log("error", text)

    def _log_success(self, text: str):
        self._append_log("success", text)

    def _clear_log(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    # -- UI state updates ---------------------------------------------------

    def _update_state_ui(self, key: str, state: ServiceState):
        """Thread-safe status indicator update."""
        def _do():
            colour = STATE_COLOUR[state]
            self._status_dots[key].configure(fg=colour)
            self._status_labels[key].configure(text=STATE_LABEL[state], fg=colour)
            btn = self._toggle_btns[key]
            if state in (ServiceState.RUNNING, ServiceState.STARTING):
                btn.configure(text="Stop", fg=RED)
            else:
                btn.configure(text="Start", fg=GREEN)
        self.root.after(0, _do)

    # -- Misc ---------------------------------------------------------------

    def _shutdown(self):
        if not messagebox.askyesno(
            "Shutdown",
            "This will stop all services and shut down the computer.\nProceed?",
        ):
            return
        self._system_log("Stopping all services before shutdown…")
        self._stop_all_sync()
        self._system_log("Shutting down the system…")
        if sys.platform == "win32":
            subprocess.Popen(["shutdown", "/s", "/t", "5"], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(["shutdown", "-h", "now"])
        self.root.destroy()

    def _open_browser(self):
        url = "http://localhost:5173"
        browser = _find_browser()
        if browser:
            # Use a dedicated profile so Chrome/Edge launches a fresh instance
            # that respects --kiosk (ignored when attaching to an existing window)
            profile_dir = PROJECT_ROOT / ".browser-profile"
            profile_dir.mkdir(exist_ok=True)
            self._system_log(f"Opening {url} in fullscreen app mode")
            subprocess.Popen(
                [browser, f"--app={url}", "--start-fullscreen",
                 f"--user-data-dir={profile_dir}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            self._system_log("Chrome/Edge not found, opening default browser")
            webbrowser.open(url)

    def _on_close(self):
        any_running = any(mp.is_running for mp in self._processes.values())
        if any_running:
            if not messagebox.askyesno(
                "Quit",
                "Some services are still running.\nStop them and quit?",
            ):
                return
            self._stop_all_sync()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = LauncherApp()
    app.run()
