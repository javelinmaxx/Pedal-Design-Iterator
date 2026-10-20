#!/usr/bin/env python3
"""Run the same three user-supplied ngspice benches and retain evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benches", type=Path, required=True)
    parser.add_argument("--conditions", type=Path, required=True,
                        help="JSON record of supply, input, load, controls and targets")
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory for this baseline or candidate run")
    parser.add_argument("--ngspice", default="ngspice")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    benches = args.benches.resolve()
    paths = [benches / name for name in ("op.cir", "ac.cir", "transient.cir")]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        parser.error("Missing circuit testbenches: " + ", ".join(missing))
    try:
        conditions = json.loads(args.conditions.read_text())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if not isinstance(conditions, dict):
        parser.error("Conditions must be a JSON object")
    for field in ("supply", "input", "load", "controls", "targets"):
        if not conditions.get(field):
            parser.error("Conditions must document: " + field)
    executable = shutil.which(args.ngspice)
    if not executable:
        parser.error("ngspice executable unavailable; install it or pass --ngspice PATH")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        version = subprocess.run([executable, "--version"], capture_output=True,
                                 text=True, timeout=args.timeout)
        version_text = version.stdout + version.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        version_text = str(exc)
    manifest = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "ngspice_version": version_text,
        "conditions": conditions,
        "runs": [],
    }
    # Record all files in the bench directory, including local model dependencies.
    manifest["bench_files_sha256"] = {
        str(path.relative_to(benches)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(benches.rglob("*"))
        if path.is_file() and not path.is_relative_to(output)
    }
    failed = False
    for path in paths:
        name = path.stem
        raw = output / (name + ".raw")
        command = [executable, "-b", "-r", str(raw),
                   "-o", str(output / (name + ".log")), str(path)]
        entry = {"bench": path.name, "command": command}
        try:
            result = subprocess.run(command, cwd=benches, capture_output=True,
                                    timeout=args.timeout)
            console = result.stdout + result.stderr
            entry["returncode"] = result.returncode
            entry["raw_data_present"] = raw.is_file() and raw.stat().st_size > 0
            entry["process_completed_with_data"] = (
                result.returncode == 0 and entry["raw_data_present"])
        except subprocess.TimeoutExpired as exc:
            console = (exc.stdout or b"") + (exc.stderr or b"")
            entry.update(error="timeout", process_completed_with_data=False)
        except OSError as exc:
            console = str(exc).encode()
            entry.update(error=str(exc), process_completed_with_data=False)
        (output / (name + ".console.log")).write_bytes(console)
        failed |= not entry["process_completed_with_data"]
        manifest["runs"].append(entry)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(name + ": " + ("completed; inspect measurements" if
              entry["process_completed_with_data"] else "FAILED"))
    print("Evidence saved to", output)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
