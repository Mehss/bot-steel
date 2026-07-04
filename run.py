"""Hot-reload runner — starts main.py and restarts it whenever a .py file changes."""
import subprocess
import sys
import time
from pathlib import Path

WATCH_DIR = Path(__file__).parent
VENV_PYTHON = WATCH_DIR / "venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
DEBOUNCE = 1.0  # seconds to wait after last change before restarting


def collect_mtimes():
    mtimes = {}
    for path in WATCH_DIR.glob("**/*.py"):
        if path.name == "run.py" or "venv" in path.parts:
            continue
        try:
            mtimes[path] = path.stat().st_mtime
        except OSError:
            pass
    return mtimes


def start_bot():
    proc = subprocess.Popen([PYTHON, "main.py"], cwd=str(WATCH_DIR))
    print(f"[reload] started (PID {proc.pid})", flush=True)
    return proc


def main():
    proc = start_bot()
    mtimes = collect_mtimes()
    pending_restart = None  # timestamp when change was first detected

    try:
        while True:
            time.sleep(0.5)

            if proc.poll() is not None:
                print(f"[reload] exited ({proc.returncode}), restarting...", flush=True)
                proc = start_bot()
                mtimes = collect_mtimes()
                pending_restart = None
                continue

            current = collect_mtimes()
            changed = [p for p, t in current.items() if mtimes.get(p) != t]
            if changed and pending_restart is None:
                for p in changed:
                    print(f"[reload] changed: {p.name}", flush=True)
                pending_restart = time.monotonic()

            if pending_restart and time.monotonic() - pending_restart >= DEBOUNCE:
                proc.terminate()
                proc.wait(timeout=10)
                proc = start_bot()
                mtimes = collect_mtimes()
                pending_restart = None

    except KeyboardInterrupt:
        print("[reload] shutting down...", flush=True)
        if proc.poll() is None:
            proc.terminate()
            proc.wait()


if __name__ == "__main__":
    main()
