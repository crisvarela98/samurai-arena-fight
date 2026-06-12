from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLIENT_DIR = ROOT / "client"
SERVER_DIR = ROOT / "server"


def spawn(command: list[str], cwd: Path) -> subprocess.Popen:
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(command, cwd=str(cwd), creationflags=creationflags)


def resolve_npm() -> str | None:
    if os.name != "nt":
        return shutil.which("npm")
    return shutil.which("npm.cmd") or shutil.which("npm")


def main() -> int:
    server = None
    client = None
    try:
        npm = resolve_npm()
        if not npm:
            print("No se encontro npm. Instala Node.js o agrega npm al PATH.")
            return 1
        server = spawn([npm, "run", "dev"], SERVER_DIR)
        time.sleep(2)
        client = spawn([sys.executable, "main.py"], CLIENT_DIR)
        print("Server and client started. Close this window to stop both.")
        while True:
            if server.poll() is not None:
                print("Server stopped unexpectedly.")
                return server.returncode or 1
            if client.poll() is not None:
                print("Client stopped.")
                return client.returncode or 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping...")
        return 0
    finally:
        for process in (client, server):
            if process and process.poll() is None:
                if os.name == "nt":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
        for process in (client, server):
            if process:
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
