#!/usr/bin/env python3
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "commands" / "queue"
PROCESSED_DIR = BASE_DIR / "commands" / "processed"
PROBES_DIR = BASE_DIR / "probes" / "outputs"

for d in [QUEUE_DIR, PROCESSED_DIR, PROBES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def process_task(task_file: Path):
    print(f"[*] Processing task: {task_file.name}")
    try:
        with open(task_file, "r") as f:
            task = json.load(f)
    except Exception as e:
        print(f"[!] Error parsing {task_file}: {e}")
        return

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    ts_str = now.strftime("%Y%m%d_%H%M%S")
    task_id = task.get("id", f"task_{ts_str}")
    command = task.get("command", "")
    target = task.get("target", "probe")

    target_dir = PROBES_DIR / date_str
    target_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=task.get("timeout", 300)
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except Exception as e:
        stdout = ""
        stderr = str(e)
        exit_code = -1

    duration = time.time() - start_time

    output_artifact = {
        "task_id": task_id,
        "target": target,
        "timestamp_utc": now.isoformat(),
        "duration_sec": duration,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr
    }

    output_file = target_dir / f"{ts_str}_{task_id}_output.json"
    with open(output_file, "w") as f:
        json.dump(output_artifact, f, indent=2)

    archive_dir = PROCESSED_DIR / date_str
    archive_dir.mkdir(parents=True, exist_ok=True)
    task_file.rename(archive_dir / f"{ts_str}_{task_file.name}")
    print(f"[+] Task {task_id} done. Output: {output_file.relative_to(BASE_DIR)}")

def main():
    print("[*] Vessel Runner active. Polling commands/queue...")
    while True:
        tasks = sorted(list(QUEUE_DIR.glob("*.json")))
        for task in tasks:
            process_task(task)
        time.sleep(5)

if __name__ == "__main__":
    main()
