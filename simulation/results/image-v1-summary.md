# Image-v1 provisional simulation report

**Simulated, not bench measured.** These results describe a tentative screenshot
transcription with generic device models. They do not establish the behavior of
the original circuit. Wiring/model uncertainties are listed in
[the transcription notes](../../schematics/image-v1/TRANSCRIPTION.md).
No circuit improvement was made.

## Conditions

ngspice 44.2 shared library, 27 C; 9 V supply through the pictured 100 ohm filter,
100 mV RMS unloaded 1 kHz sine generator through 20 kohm source resistance,
20 kohm output load. Assumed controls: drive rheostat 50 kohm, tone rheostat
50 kohm, volume 50% resistance split; clipping switch enabled. Generic silicon
NPN and diode models are included in the netlist, not manufacturer-qualified.

## Measured simulation results

| Metric | Result | Target interpretation |
| --- | ---: | --- |
| Quiescent supply current | 1.348 mA | Below stated 100 mA budget; not a startup/transient current guarantee |
| Filtered supply | 8.865 V | Descriptive |
| Q1/Q2/Q3 collector DC | 4.300 / 5.024 / 3.866 V | Descriptive |
| Small signal AC gain, generator to output, 1 kHz | 10.542 dB | Above 10 dB under these assumptions |
| Small signal AC gain, loaded pedal input to output, 1 kHz | 18.642 dB | Above 10 dB under these assumptions |
| Large signal fundamental gain, generator to output | 8.983 dB | Below 10 dB under these assumptions |
| Large signal fundamental gain, loaded input to output | 16.404 dB | Above 10 dB under these assumptions |
| Output fundamental | 281.272 mV RMS | Descriptive |
| Output THD through H10 | 6.902% | No THD limit supplied |
| Output H2 / H3 | -32.716 / -24.738 dBc | Descriptive; H2-H10 in measurements JSON |
| Output waveform range | about -369 to +373 mV | Descriptive |

The gain reference and regime matter: loading by the circuit reduces the input,
and nonlinear behavior reduces generator-to-output fundamental gain relative to
small signal gain. Neither reference can be silently substituted for the other.
The user has not finalized which gain definition the target applies to.

## Readiness and numerical checks

- Operating point: 1 solution; AC: 401 points from 10 Hz to 100 kHz;
  transient baseline: 20,001 saved points from about 280 ms through 300 ms.
- No simulation/convergence errors were reported in the successful logs.
  The library warns that `spinit` is absent; these decks explicitly define
  their models and use native ngspice syntax, with no initialization-file dependency.
- Harmonics use linear resampling at 1 us, a rectangular coherent 290–300 ms
  window (10 cycles), and Fourier amplitudes H1-H10. THD excludes noise and H11+.
- Halving maximum transient step from 1 us to 0.5 us changed output fundamental
  RMS from 0.281271873 to 0.281272836 V and THD10 from 6.901854% to 6.902113%.
  This is numerical sensitivity evidence, not physical model validation.
- Baseline adjacent 5 ms windows gave 0.281271291 and 0.281272454 V fundamental
  RMS, consistent with negligible residual amplitude drift for this stimulus.
- The Fourier extractor passed an independent synthetic-signal check with known
  DC offset, fundamental amplitude, H2=-20 dBc and THD10=10%. This is an analysis
  code check, not a circuit or hardware result.
- Initial failed run `image-v1-baseline` retains the shared-library source-path
  quoting failure. It contains no valid circuit results. `image-v1-baseline-r2`
  is the successful baseline; `image-v1-refined` is the timestep check.

Each successful run directory contains copied decks/models, input hashes,
simulator logs, raw data, selected-vector CSVs and `measurements.json`.

## Reproduce

Run from `/workspace/Pedal-Design-Iterator` using a new output directory:

```sh
python3 simulation/run_shared.py --output simulation/results/image-v1-next
python3 simulation/analyze_image.py simulation/results/image-v1-next
```

The default suite is `simulation/benches/image-v1`. With an ngspice CLI installed,
the same decks can instead use `simulation/run.py`, after creating a conditions
file that records the explicit provisional controls and measurement assumptions.

Confirm clipping-pot/switch wiring and device identities, create/reconcile the
KiCad design record, and finalize controls/gain definition before circuit changes.
Hardware bias, real pickup loading, noise, tolerances, stability and sound still
require bench testing. No compressor attack/release behavior has been established.
