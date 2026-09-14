#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROBES_DIR = BASE_DIR / "probes" / "outputs"
REPORTS_DIR = BASE_DIR / "reports" / "runs"
HANDOFFS_DIR = BASE_DIR / "context" / "agent_handoffs"

for d in [REPORTS_DIR, HANDOFFS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def generate_report(output_file: Path):
    with open(output_file, "r") as f:
        data = json.load(f)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    ts_str = now.strftime("%Y%m%d_%H%M%S")

    target_reports_dir = REPORTS_DIR / date_str
    target_reports_dir.mkdir(parents=True, exist_ok=True)

    task_id = data.get("task_id", "unknown")
    report_file = target_reports_dir / f"{ts_str}_{task_id}_report.md"

    md = f"""# Vessel Execution Report: {task_id}
- **Generated (UTC):** {now.isoformat()}
- **Execution Timestamp:** {data.get('timestamp_utc')}
- **Target:** {data.get('target')}
- **Duration:** {data.get('duration_sec', 0):.2f}s
- **Exit Code:** {data.get('exit_code')} ({'SUCCESS' if data.get('exit_code') == 0 else 'FAILURE'})

## Output Summary
```text
{data.get('stdout')[:4000] if data.get('stdout') else 'No stdout.'}
```

## Diagnostics & Errors
```text
{data.get('stderr')[:2000] if data.get('stderr') else 'None.'}
```

## Agent Handoff Context
- Artifact location: `{output_file.relative_to(BASE_DIR)}`
- Status: Stored in persistent date-bucketed repository tree.
"""
    with open(report_file, "w") as f:
        f.write(md)

    print(f"[+] Report generated: {report_file.relative_to(BASE_DIR)}")

def main():
    for json_file in PROBES_DIR.glob("**/*_output.json"):
        generate_report(json_file)

if __name__ == "__main__":
    main()
