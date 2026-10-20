# Image-v2: device and switch clarification

This revision supersedes the device/switch assumptions in image-v1. User confirmed
that Q1, Q2 and Q3 are S8050 and the diodes are Schottky. The switch selects either
diodes to ground (shunt clipping) or diodes in the signal path (crossover distortion).
The screenshot and user clarification remain the reference; a KiCad schematic has
not yet been created. These netlists do not replace the KiCad design record.

## Connections implemented

The two diodes remain antiparallel in both modes; only their return connection and
the following-stage input connection move. Inserting that antiparallel pair as a
two-terminal element in series with the signal produces the crossover mechanism.
Two diodes in anti-series would block ordinary conduction in both directions and
are not the interpretation used here.

- `simulation/benches/image-v2-shunt/pedal.cir`: `drive -> Rdrive -> clip`,
  diodes between `clip` and ground, and `drive -> selected -> Ccouple2 -> b2`.
- `simulation/benches/image-v2-crossover/pedal.cir`: `drive -> Rdrive -> clip`,
  diodes between `clip` and `diode_return`, and
  `diode_return -> selected -> Ccouple2 -> b2`.
- Closed switch contacts are represented by 1 milliohm resistors. Each mode is
  a static topology, not a simulation of switch bounce or switching transients.

The ambiguous 100 kohm drive control is still approximated as a 50 kohm rheostat
in series with the diode pair; the visible 5 kohm remains a shunt from `drive`
to ground. Tone is 50 kohm and volume a 50% resistance split. Those pot and 5 kohm
connections still need confirmation. Other component values are unchanged from
image-v1.

## Model accuracy

`S8050_APPROX` assigns the confirmed part identity while retaining the earlier
generic NPN proxy parameters. **It is not a manufacturer S8050 model**, nor a
claim that measured S8050 gain, capacitance or saturation behavior is reproduced.
`SCHOTTKY_APPROX` uses illustrative parameters: IS=200 nA, N=1.05, RS=2 ohm,
CJO=10 pF, BV=30 V, and default zero transit time. It is not a particular part.
These assumptions can materially affect both crossover leakage and clipping.
Use the actual manufacturer models once the manufacturer/diode type is known.
All diodes, including the supply protection diode, use this Schottky approximation.

Expected effects before the rerun: compared with the image-v1 silicon diode
approximation, the Schottky pair should conduct at lower voltage. Shunt mode can
limit excursions earlier; crossover mode should attenuate around zero crossings
and change harmonic content. Leakage makes the crossover transition soft and can
produce nonzero linear AC gain at zero signal. Small signal AC alone therefore
does not characterize this nonlinear effect. This revision corrects transcription
assumptions; it is not a proposed improvement to the user's circuit.

Both modes use the same operating point, AC, and 100 mV RMS/1 kHz transient tests
as image-v1, with the same source resistance, load, supply and assumed controls.
Results, mode comparison and numerical checks are in
`simulation/results/image-v2-summary.md`.
