#!/usr/bin/env python3
"""TechAranya launcher - works on Windows, Mac and Linux.

Run it with:   python start.py      (Windows)
               python3 start.py     (Mac / Linux)
On Windows you can also just double-click this file.
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
PORT = os.environ.get("PORT", "8000")
VENV_DIR = ROOT / ".venv"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if WINDOWS else "bin/python")
ENV_FILE = ROOT / ".env"
PLACEHOLDER = "sk-ant-..."


def pause():
    # Keep the window open when the file was double-clicked on Windows.
    if WINDOWS:
        try:
            input("\nPress Enter to close this window...")
        except EOFError:
            pass


def open_in_editor(path: Path):
    try:
        if WINDOWS:
            subprocess.Popen(["notepad", str(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-e", str(path)])
        else:
            print(f"   Edit this file: {path}")
    except OSError:
        print(f"   Edit this file: {path}")


def open_browser_when_ready(url: str):
    for _ in range(60):
        try:
            urllib.request.urlopen(url + "/api/health", timeout=1)
            webbrowser.open(url)
            return
        except Exception:
            time.sleep(1)


def main() -> int:
    os.chdir(ROOT)

    if sys.version_info < (3, 10):
        print(f"[X] Python 3.10 or newer is needed (you have {sys.version.split()[0]}).")
        print("    Download it from https://www.python.org/downloads/")
        return 1

    # 1. Virtual environment + packages
    if not VENV_PY.exists():
        print("Creating virtual environment (first run only)...")
        venv.create(VENV_DIR, with_pip=True)
    print("Installing / checking packages (first run takes 1-2 minutes)...")
    result = subprocess.call(
        [str(VENV_PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", "requirements.txt"]
    )
    if result != 0:
        print("[X] Package install failed. Check your internet connection and try again.")
        return 1

    # 2. API key
    if not ENV_FILE.exists():
        shutil.copy(ROOT / ".env.example", ENV_FILE)
    if PLACEHOLDER in ENV_FILE.read_text(encoding="utf-8", errors="ignore"):
        print()
        print("[KEY] Add your Anthropic API key:")
        print(f"      In the file that just opened ({ENV_FILE.name}), replace  {PLACEHOLDER}  with your key,")
        print("      save it, close the editor, then run start.py again.")
        open_in_editor(ENV_FILE)
        return 0

    # 3. Start server (and open the browser once it is ready)
    url = f"http://localhost:{PORT}"
    print()
    print(f"TechAranya is starting at {url}")
    print("Press Ctrl+C (or close this window) to stop.")
    print()
    if not os.environ.get("NO_BROWSER"):
        threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    try:
        return subprocess.call(
            [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", PORT]
        )
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:  # show the error instead of a window that vanishes
        print(f"\n[X] Unexpected error: {e}")
        code = 1
    if code != 0:
        pause()
    elif WINDOWS and not (ENV_FILE.exists() and PLACEHOLDER not in ENV_FILE.read_text(encoding="utf-8", errors="ignore")):
        pause()
    sys.exit(code)
