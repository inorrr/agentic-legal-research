#!/usr/bin/env python3
"""Start the UI and API on one loopback origin; keep this terminal open.

Uses existing installed dependencies, builds the UI locally, and never creates
credentials or calls a model. Ctrl+C stops the server without deleting data.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def open_when_ready(process, url):
    for _ in range(100):
        if process.poll() is not None:
            return
        try:
            with urlopen(url + '/api/health', timeout=1) as response:
                if json.load(response).get('stage') == 'local_workspace':
                    webbrowser.open(url)
                    return
        except (OSError, ValueError):
            pass
        time.sleep(.15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--open', action='store_true', help='Open the browser after startup')
    parser.add_argument('--port', type=int, help='Explicit local UI/API port; otherwise choose a free port from 5173–5183')
    args = parser.parse_args()
    if args.port is not None and not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        raise SystemExit('Install the backend first using the README setup instructions.')
    ports = [args.port] if args.port is not None else range(5173, 5184)
    selected = None
    for candidate in ports:
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', candidate))
            except OSError:
                continue
            selected = candidate
            break
    if selected is None:
        raise SystemExit('No requested port is free. Stop an older app or choose another with --port.')
    args.port = selected
    url = f'http://127.0.0.1:{args.port}'
    npm = shutil.which('npm')
    if not npm or not (ROOT / 'frontend/node_modules').is_dir():
        raise SystemExit('Install Node.js and run npm ci --prefix frontend before starting.')
    built = subprocess.run([npm, 'run', 'build'], cwd=ROOT / 'frontend')
    if built.returncode:
        return built.returncode
    env = {**os.environ, 'LEGAL_RESEARCH_SERVE_UI': '1'}
    print(f'\nOpen {url}\nKeep this terminal open while using the app. Press Ctrl+C to stop.\n', flush=True)
    process = subprocess.Popen([str(python), '-m', 'legal_research.serve', '--port', str(args.port)], cwd=ROOT, env=env)
    if args.open:
        threading.Thread(target=open_when_ready, args=(process,url), daemon=True).start()
    try:
        return process.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    sys.exit(main())
