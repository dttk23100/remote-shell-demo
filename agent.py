#!/usr/bin/env python3
"""Allowlisted, read-only remote-shell demo agent.

Polls a public GitHub Gist for commands and writes output back to the same Gist.
Runs only a small allowlist of commands. No writes, no sudo, no network commands.
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request

OWNER = os.environ.get("GIST_OWNER", "dttk23100")
GIST_ID = os.environ["GIST_ID"]
TOKEN = os.environ["GH_TOKEN"]
INTERVAL = float(os.environ.get("INTERVAL", "1.5"))
HEARTBEAT = 10.0

ALLOWED = [
    re.compile(r"^whoami$"),
    re.compile(r"^id$"),
    re.compile(r"^hostname$"),
    re.compile(r"^pwd$"),
    re.compile(r"^date$"),
    re.compile(r"^uptime$"),
    re.compile(r"^uname -a$"),
    re.compile(r"^sw_vers$"),
    re.compile(r"^df -h$"),
    re.compile(r"^ls( -la)?$"),
    re.compile(r"^ps aux( \| head( -n)? [0-9]{1,3})?$"),
    re.compile(r"^echo [A-Za-z0-9 .,!?_'\"-]{1,120}$"),
    re.compile(r"^say [A-Za-z0-9 .,!?_'\"-]{1,120}$"),
]

def allowed(cmd: str) -> bool:
    return any(p.match(cmd) for p in ALLOWED)

def fetch_raw(file: str) -> str:
    url = f"https://gist.githubusercontent.com/{OWNER}/{GIST_ID}/raw/{file}?t={time.time_ns()}"
    return subprocess.check_output(
        ["/usr/bin/curl", "-sS", "--max-time", "15", "-A", "remote-shell-demo-agent", url],
        text=True,
    )

def patch(files: dict) -> None:
    body = json.dumps({"files": files})
    p = subprocess.run(
        [
            "/usr/bin/curl", "-sS", "--max-time", "15", "-X", "PATCH",
            "-H", f"Authorization: Bearer {TOKEN}",
            "-H", "Accept: application/vnd.github+json",
            "-H", "Content-Type: application/json",
            "-A", "remote-shell-demo-agent",
            "--data-binary", "@-",
            f"https://api.github.com/gists/{GIST_ID}",
        ],
        input=body,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"curl exit {p.returncode}")

def status(online: bool, last_id: int) -> dict:
    return {
        "online": online,
        "last_seen": int(time.time()),
        "host": socket.gethostname(),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "last_id": last_id,
    }

def write_status(online: bool, last_id: int) -> None:
    patch({"status.json": {"content": json.dumps(status(online, last_id))}})

def run(cmd: str) -> str:
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            executable="/bin/zsh",
        )
        text = (p.stdout or "") + (p.stderr or "")
        if not text:
            text = f"[exit {p.returncode}]\n"
        return text[-12000:]
    except subprocess.TimeoutExpired:
        return "[timeout after 15s]\n"
    except Exception as e:
        return f"[error] {e}\n"

def main() -> int:
    last_id = 0
    last_status = 0.0
    print(f"agent online: {socket.gethostname()} user={os.environ.get('USER')}", flush=True)
    write_status(True, last_id)
    while True:
        try:
            raw = fetch_raw("command.json")
            try:
                cmd = json.loads(raw)
            except Exception:
                cmd = {}
            cid = int(cmd.get("id") or 0)
            text = str(cmd.get("cmd") or "").strip()
            if cid and cid != last_id and text:
                if text == "__quit__":
                    write_status(False, last_id)
                    print("quit command received", flush=True)
                    return 0
                if allowed(text):
                    out = f"$ {text}\n\n" + run(text)
                else:
                    out = f"$ {text}\n\n[blocked] command is not in the read-only allowlist\n"
                print(out, flush=True)
                patch({
                    "output.txt": {"content": out},
                    "status.json": {"content": json.dumps(status(True, cid))},
                })
                last_id = cid
                last_status = time.time()
            if time.time() - last_status >= HEARTBEAT:
                write_status(True, last_id)
                last_status = time.time()
        except KeyboardInterrupt:
            write_status(False, last_id)
            return 0
        except Exception as e:
            print(f"[agent] {e}", file=sys.stderr, flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    raise SystemExit(main())
