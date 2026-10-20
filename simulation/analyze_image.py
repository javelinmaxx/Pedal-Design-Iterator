#!/usr/bin/env python3
"""Extract fixed 1kHz image-suite measurements from saved CSV simulation data."""
import argparse
import bisect
import cmath
import csv
import json
import math
from pathlib import Path


def rows(path):
    with path.open(newline="") as stream:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]


def db(value):
    return 20 * math.log10(abs(value)) if abs(value) > 0 else None


def spectrum(data, node, start=0.290, duration=0.010):
    times = [r["time"] for r in data]
    step = 1e-6
    count = round(duration / step)
    if times[0] > start or times[-1] < start + duration - step:
        raise ValueError("Transient data do not cover the analysis window")
    samples = []
    for i in range(count):
        time = start + i * step
        j = min(max(bisect.bisect_right(times, time), 1), len(times) - 1)
        fraction = (time - times[j-1]) / (times[j] - times[j-1])
        samples.append(data[j-1][node] * (1-fraction) + data[j][node] * fraction)
    dc = sum(samples) / count
    harmonic_rms = []
    for harmonic in range(1, 11):
        phasor = sum((v-dc) * cmath.exp(-2j * math.pi * harmonic * 1000 * i * step)
                     for i, v in enumerate(samples)) * 2 / count
        harmonic_rms.append(abs(phasor) / math.sqrt(2))
    fundamental = harmonic_rms[0]
    return {"dc_V": dc, "total_rms_V": math.sqrt(sum(v*v for v in samples)/count),
            "minimum_V": min(samples), "maximum_V": max(samples),
            "fundamental_rms_V": fundamental,
            "harmonic_rms_V": harmonic_rms,
            "H2_H10_dBc": [db(v/fundamental) for v in harmonic_rms[1:]]
            if fundamental > 1e-12 else None,
            "THD10_percent": 100 * math.sqrt(sum(v*v for v in harmonic_rms[1:])) / fundamental
            if fundamental > 1e-12 else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    root = args.results
    op = rows(root / "op.csv")[0]
    ac = rows(root / "ac.csv")
    transient = rows(root / "transient.csv")
    row = min(ac, key=lambda r: abs(r["frequency_real"] - 1000))

    def phasor(name):
        return complex(row[name + "_real"], row[name + "_imag"])

    spectra = {name: spectrum(transient, name) for name in ("source", "in", "out")}
    output = spectra["out"]["fundamental_rms_V"]
    result = {
        "evidence": "SIMULATED: provisional image wiring and generic device models",
        "op_V": {key: value for key, value in op.items() if key != "vsupply#branch"},
        "op_supply_current_mA": -1000 * op["vsupply#branch"],
        "ac_frequency_Hz": row["frequency_real"],
        "ac_gain_generator_dB": db(phasor("out") / phasor("source")),
        "ac_gain_pedal_input_dB": db(phasor("out") / phasor("in")),
        "ac_phase_generator_deg": math.degrees(cmath.phase(phasor("out") / phasor("source"))),
        "transient_fundamental_gain_generator_dB": db(output / spectra["source"]["fundamental_rms_V"]),
        "transient_fundamental_gain_pedal_input_dB": db(output / spectra["in"]["fundamental_rms_V"]),
        "analysis_window_s": [0.290, 0.300],
        "uniform_resampling_step_s": 1e-6,
        "DFT": "Rectangular, coherent 10-cycle window at 1kHz; linear resampling; H1-H10",
        "spectra": spectra,
        "output_fundamental_prior_5ms_V_rms": spectrum(transient, "out", 0.290, 0.005)["fundamental_rms_V"],
        "output_fundamental_last_5ms_V_rms": spectrum(transient, "out", 0.295, 0.005)["fundamental_rms_V"],
        "target_assessment": "Gain >10dB assessed only conditionally under the stated 1kHz, midpoint-control assumptions; THD has no limit. Final target definition pending.",
    }
    (root / "measurements.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
