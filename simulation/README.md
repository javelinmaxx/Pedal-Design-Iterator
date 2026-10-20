# Repeatable circuit iteration

Status: corrected provisional screenshot transcriptions are now in
`benches/image-v2-shunt` and `benches/image-v2-crossover`, with confirmed S8050
part assignments and approximate Schottky models. Both modes' three analyses
have run using the installed ngspice 44.2 shared library;
see `results/image-v2-summary.md` for results and repeatable commands. There is
no KiCad schematic yet. Wiring, models and control settings remain provisional;
see `schematics/image-v2/TRANSCRIPTION.md` from the repository root.
Partial user-specified conditions and a gain target are recorded in
`conditions.json`. Python 3.12 is available; the ngspice CLI is not on PATH.

## Design record and testbench contract

Keep the KiCad schematic as the design record. Make circuit changes there first,
then export a SPICE netlist using KiCad's simulation model assignments. Inspect
pin order, power connections, ground node 0, and model paths after each export.
Retain the exported baseline and candidate netlists with their schematic revision.
Do not make a change only in an exported netlist and call it a design change.

Create three complete decks in a bench directory, using the same exported circuit,
models, supply, load and control settings. Keep relative includes resolvable from
that directory. Do not put `.control` blocks, `quit`, or extra analyses in these
batch decks; the runner supplies output locations. Each deck needs a title line,
the intended analysis directive, and `.end`.

| Deck | Required analysis and measurements |
| --- | --- |
| `op.cir` | `.op`; transistor/op amp bias, supply current, headroom and output DC |
| `ac.cir` | `.ac`; input source AC magnitude 1 with the stated source impedance; gain `V(out)/V(in)`, phase, and cutoff frequencies over the target band |
| `transient.cir` | `.tran`; stated guitar waveform and amplitude, source impedance, and DC offset; settled output level, clipping/asymmetry, and any target distortion metric |

Choose sweep range, transient step size and duration from the supplied targets.
Check convergence and settling. Distortion requires sufficient steady state cycles
and sample resolution. AC analysis linearizes the circuit at its operating point;
it does not measure clipping or nonlinear distortion.

## Stated conditions and nonlinear measurements

Use a 9 V supply and a 20 kohm resistive output load. The stated supply capacity
is 100 mA; compare simulated supply current with that budget. Do not model the
supply as a forced 100 mA source. Supply impedance and current-limit behavior
remain unspecified.

The input is 100 mV RMS. **Calculated:** for a sine wave, this is
141.421 mV peak or 282.843 mV peak to peak. Use the peak value in a SPICE `SIN`
source when that level refers to the generator. Record whether the specified
level is before the source impedance or at the loaded pedal input; attenuation
can make these different. The guitar/source series resistance is 20 kohm;
the pedal input impedance is not yet specified.

The gain target is **strictly greater than 10 dB**, equivalent to a voltage
amplitude ratio greater than approximately 3.162 (calculated using
`20 * log10(abs(Vout / Vin))`). Before scoring it, define the frequency,
control positions, input reference (generator or loaded pedal input), and whether
the target means small signal AC gain or large signal fundamental gain. For a
distortion or compressor these measurements can differ substantially. Preserve
both references in results where useful. THD has no specified limit: report it
and the individual harmonics without assigning a THD pass/fail result. Remaining
specifications will be supplied when the schematic is made.

Use a 1 kHz sine as a proposed initial harmonic stimulus. Report output DC,
fundamental RMS, H2 through H10 in dBc, and THD through H10:
`THD10 = 100 * sqrt(V2_rms^2 + ... + V10_rms^2) / V1_rms`.
For each harmonic, `dBc = 20 * log10(Vn_rms / V1_rms)`. Handle a negligible
fundamental as undefined, not as a passing result. THD10 omits higher harmonics
and noise; it is not THD+N or a complete measure of sound quality.

Extract harmonics from settled transient output, not small signal AC results.
Use a fixed window containing an integer number of input cycles and uniform
resampling when calculating a DFT from ngspice's adaptive time samples. At 1 kHz,
start with a maximum transient step of 1 us and at least 10 settled cycles for
analysis. Tighten the step and extend settling to verify stability of the results,
especially for sharp clipping. Record the window, sample interval, extraction
method and convergence comparison. Compressor settling can require much longer
than 10 ms; establish it from the envelope behavior before taking a spectrum.

A compressor also needs input level sweeps and an amplitude step/burst test to
measure its transfer curve, gain reduction, attack and release. Define level
points, timing, threshold conventions and control positions before adding those
decks to the fixed comparison suite. The current runner runs only the three core
decks. `analyze_image.py` now extracts H1-H10 from the fixed image-suite 1 kHz
transient test. Compressor-specific tests are not implemented yet.
The gain limit is recorded but its measurement definition is pending.
`conditions.json` deliberately leaves `controls` null, so the runner rejects it
until control settings are supplied. This preflight check does not establish
that all measurement definitions have been completed.

Create a conditions JSON file with nonempty `supply`, `input`, `load`, `controls`
and `targets` fields. Specify units, source amplitude convention (peak/RMS/peak to
peak), source impedance, waveform/frequencies, pot positions and wiring, output
loading, temperature, model versions, and numeric target limits with tolerances.
These fields record the conditions; the decks must actually implement them.
Place required models and includes within the bench directory so the runner hashes
them. Preserve the schematic revision separately; hashes are provenance, not a
restorable copy of a design.

## Run and compare

From `/workspace/Pedal-Design-Iterator`, once the decks and conditions exist:

```sh
python3 simulation/run.py --benches simulation/benches \
  --conditions simulation/conditions.json \
  --output /workspace/pedal-simulation-runs/baseline
```

Install a supported ngspice CLI first, or pass `--ngspice /path/to/ngspice`.
The runner uses the bench directory as its working directory and runs all three
decks, even when one fails. It retains ngspice logs, console output, raw waveform
data, exit codes, simulator version, conditions and bench file hashes. Choose a
new output directory for each run to preserve prior evidence. A successful process
with raw data is not a target pass: inspect the logs for convergence problems,
verify the intended analyses executed, and extract and compare measurements.

For every candidate:

1. Record the proposed schematic change, physical rationale, expected direction
   and approximate size of effect, and possible tradeoffs before simulating.
2. Change the KiCad schematic, export again, and rerun these same three decks with
   the same stimuli, analyses, models, controls and measurement definitions. Only
   the candidate circuit should differ. Use a new output directory.
3. Save a comparison table with metric/unit, target and tolerance, baseline,
   candidate, pass/fail/unresolved, and source log/data reference. Do not treat
   missing measurements as passes. Record extraction formulas and analysis windows.
4. Label evidence as **simulated**, **calculated**, or **bench measurement**.
   Calculated RC corners and bias estimates are predictions until checked.
   Hardware noise, pickup interaction, stability with real wiring, tolerances,
   power supply behavior and subjective sound still need bench testing unless
   supported by actual measurements. Do not infer them from an ideal model.

Outstanding: verify the image transcription and device models, create the KiCad
design record, and finalize input level reference, controls and gain definition.
The shared-library runner works here; a CLI is needed only for `run.py`.
Other specs are deferred until the schematic is made; an unspecified THD limit
does not block reporting harmonic content.
