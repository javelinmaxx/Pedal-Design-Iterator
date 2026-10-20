#!/usr/bin/env python3
"""Run a three-deck suite with installed libngspice; no CLI required."""
import argparse
import csv
import ctypes as C
import ctypes.util
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import os


class Complex(C.Structure):
    _fields_ = [("real", C.c_double), ("imag", C.c_double)]


class Vector(C.Structure):
    _fields_ = [("name", C.c_char_p), ("type", C.c_int),
                ("flags", C.c_short), ("real", C.POINTER(C.c_double)),
                ("complex", C.POINTER(Complex)), ("length", C.c_int)]


def run_one(deck, output):
    library = ctypes.util.find_library("ngspice")
    if not library:
        raise RuntimeError("libngspice unavailable")
    lib = C.CDLL(library)
    log = []
    callback_type = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)

    @callback_type
    def receive(message, ident, user):
        log.append(message.decode(errors="replace"))
        return 0

    exit_type = C.CFUNCTYPE(C.c_int, C.c_int, C.c_bool, C.c_bool,
                           C.c_int, C.c_void_p)
    exits = []

    @exit_type
    def on_exit(status, immediate, requested, ident, user):
        exits.append(status)
        return 0

    lib.ngSpice_Init.argtypes = [callback_type, C.c_void_p, exit_type,
                                C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p]
    lib.ngSpice_Command.argtypes = [C.c_char_p]
    lib.ngGet_Vec_Info.argtypes = [C.c_char_p]
    lib.ngGet_Vec_Info.restype = C.POINTER(Vector)
    lib.ngSpice_Init(receive, None, on_exit, None, None, None, None)

    def command(value):
        if lib.ngSpice_Command(value.encode()) != 0:
            raise RuntimeError("ngspice command failed: " + value)

    def vector(name):
        pointer = lib.ngGet_Vec_Info(name.encode())
        if not pointer or pointer.contents.length < 1:
            raise RuntimeError("Missing vector: " + name)
        value = pointer.contents
        if value.complex:
            return [complex(value.complex[i].real, value.complex[i].imag)
                    for i in range(value.length)]
        return [value.real[i] for i in range(value.length)]

    try:
        command("version")
        os.chdir(deck.parent)
        command('source ' + deck.name)
        command("run")
        if exits:
            raise RuntimeError("ngspice requested exit: " + str(exits))
        command("set filetype=ascii")
        command('write ' + str(output / (deck.stem + ".raw")) + ' all')
        nodes = ["source", "in", "b1", "c1", "e1", "drive", "clip", "b2",
                 "c2", "e2", "b3", "c3", "e3", "vcc", "out", "vsupply#branch"]
        axis = [] if deck.stem == "op" else ["frequency" if deck.stem == "ac" else "time"]
        vectors = {name: vector(name) for name in axis + nodes}
        count = len(vectors["out"])
        if any(len(v) != count for v in vectors.values()):
            raise RuntimeError("Inconsistent vector lengths")
        with (output / (deck.stem + ".csv")).open("w", newline="") as stream:
            writer = csv.writer(stream)
            headers = []
            for name, values in vectors.items():
                headers.extend([name + "_real", name + "_imag"]
                               if isinstance(values[0], complex) else [name])
            writer.writerow(headers)
            for index in range(count):
                row = []
                for values in vectors.values():
                    value = values[index]
                    row.extend([value.real, value.imag] if isinstance(value, complex) else [value])
                writer.writerow(row)
        (output / (deck.stem + ".status.json")).write_text(
            json.dumps({"samples": count, "completed": True}, indent=2) + "\n")
    finally:
        (output / (deck.stem + ".log")).write_text("\n".join(log) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benches", type=Path,
                        default=Path(__file__).resolve().parent / "benches/image-v2-shunt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--one", choices=["op", "ac", "transient"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    benches, output = args.benches.resolve(), args.output.resolve()
    if any(c.isspace() for c in str(output)):
        parser.error("Use an output path without whitespace for ngspice commands")
    if args.one:
        run_one(benches / (args.one + ".cir"), output)
        return 0
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "backend": "libngspice, isolated subprocess per analysis",
        "bench_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(benches.iterdir()) if p.is_file()},
        "runs": [],
    }
    # Keep the actual decks and local model definitions with the results.
    import shutil
    shutil.copytree(benches, output / "benches")
    failed = False
    for name in ("op", "ac", "transient"):
        command = [sys.executable, str(Path(__file__).resolve()),
                   "--benches", str(output / "benches"), "--output", str(output), "--one", name]
        try:
            result = subprocess.run(command, capture_output=True, timeout=120)
            (output / (name + ".console.log")).write_bytes(result.stdout + result.stderr)
            code = result.returncode
        except subprocess.TimeoutExpired as exc:
            (output / (name + ".console.log")).write_bytes(
                (exc.stdout or b"") + (exc.stderr or b"") + b"\nTIMEOUT\n")
            code = 124
        failed |= code != 0
        manifest["runs"].append({"analysis": name, "returncode": code})
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(name, "completed" if code == 0 else "FAILED")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
