#!/usr/bin/env python3
"""Plot retained image-v1 baseline and image-v2 switch-mode simulations."""
import argparse
import csv
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/pedal-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/pedal-cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_csv(path):
    with path.open(newline="") as stream:
        return [{key: float(value) for key, value in row.items()}
                for row in csv.DictReader(stream)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path,
                        default=Path(__file__).resolve().parent / "results")
    args = parser.parse_args()
    fig, axes = plt.subplots(3, 1, figsize=(10, 11), layout="constrained")
    cases = [("image-v1-baseline-r2", "Earlier silicon proxy"),
             ("image-v2-shunt", "Schottky shunt"),
             ("image-v2-crossover", "Schottky series/crossover")]
    for index, (directory, label) in enumerate(cases):
        root = args.results / directory
        ac = read_csv(root / "ac.csv")
        time = [r for r in read_csv(root / "transient.csv") if r["time"] >= 0.298]
        measured = json.loads((root / "measurements.json").read_text())
        gains = []
        for row in ac:
            value = complex(row["out_real"], row["out_imag"]) / complex(row["source_real"], row["source_imag"])
            gains.append(20 * math.log10(abs(value)))
        axes[0].semilogx([r["frequency_real"] for r in ac], gains, label=label)
        axes[1].plot([(r["time"]-0.298)*1000 for r in time],
                     [r["out"]*1000 for r in time], label=label)
        harmonics = list(range(2, 11))
        axes[2].bar([n + (index-1)*0.25 for n in harmonics],
                    [value + 100 for value in measured["spectra"]["out"]["H2_H10_dBc"]],
                    bottom=-100, width=0.25, label=label)
    axes[0].axhline(10, color="black", linestyle="--", linewidth=1, label="10 dB threshold")
    axes[0].set(xlabel="Frequency (Hz)", ylabel="Generator-to-output AC gain (dB)")
    axes[1].set(xlabel="Time from 298 ms (ms)", ylabel="Output (mV)")
    axes[2].set(xlabel="Harmonic number", ylabel="Output harmonic / fundamental (dBc)",
                xticks=list(range(2, 11)), ylim=(-80, 0))
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize="small")
    fig.suptitle("SIMULATED: tentative wiring, approximate devices, midpoint controls\n9 V; 100 mV RMS / 1 kHz sine; 20 kohm source and load")
    destination = args.results / "image-v2-comparison.png"
    fig.savefig(destination, dpi=160)
    print(destination)


if __name__ == "__main__":
    main()
