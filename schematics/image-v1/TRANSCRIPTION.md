# Provisional image transcription

The uploaded iCircuit screenshot is the reference for this first transcription.
The original image is in the conversation; it is not stored in this directory.
There is no KiCad schematic yet. These SPICE decks are a provisional simulation
artifact, not a replacement for the KiCad design record. Verify the wiring and
create/reconcile a KiCad schematic before treating this as the approved design.

## Read directly from the image

- 9 V supply; 100 ohm series supply resistor, 220 uF decoupling and reverse diode.
- 20 kohm source resistance, 50 nF input coupling capacitor.
- Stage 1: 20 kohm collector, 100 ohm emitter, 100 kohm base-to-ground,
  470 kohm collector-to-base feedback in parallel with 200 pF. Q1 is labeled S8050.
- 100 nF coupling after stage 1 and another 100 nF before stage 2.
- Stage 2: 220 kohm/100 kohm bias divider, 6.8 kohm collector and 3.3 kohm emitter.
- Tone path: 220 nF, 100 kohm control, 1.5 kohm series resistor, 2.2 nF shunt.
- Stage 3: 250 kohm/100 kohm bias divider, 10 kohm collector, 3.3 kohm emitter.
- 1 uF output coupling, 100 kohm volume control, 20 kohm output load.

## Assumptions requiring confirmation

1. The lower rail is ground. The supply protection diode is reverse biased
   normally (anode ground, cathode filtered supply).
2. The unclear 100 kohm drive pot is represented as a 50 kohm rheostat between
   the stage-1 coupled output and an antiparallel diode pair. The visible 5 kohm
   is modeled from the coupled output to ground. **Check this network first:**
   the wiper/5 kohm wiring may instead form a different divider or series path.
3. The DPDT is simplified to clipping enabled: diode return grounded and the
   stage-1 coupled output feeding the second coupling capacitor. Alternate
   switch positions and contacts are not modeled. Confirm this interpretation.
4. Tone is a rheostat at 50 kohm. Volume is an unloaded 50% resistance split
   (not a claim about knob angle or audio taper). Drive is also at 50 kohm.
5. All three transistors use an explicitly generic silicon NPN model, BF=150.
   Q2/Q3 types are unreadable/unspecified; this is not a validated S8050 model.
   All diodes use an illustrative generic silicon model. Polarity, part numbers,
   real pinouts and manufacturer models must be checked before hardware claims.
6. 100 mV RMS is the unloaded generator level before the 20 kohm source resistor.
   Initial harmonic stimulus is a zero-offset 1 kHz sine. These are explicit
   provisional choices; there is no modeled pickup inductance or capacitance.

## Evidence limits

The gain target is >10 dB, but its frequency, input reference and control settings
are not finalized. Report both generator-to-output and pedal-input-to-output
gain at 1 kHz, separately for linear AC and large signal fundamental gain.
THD10 is descriptive, without a pass/fail threshold. This topology contains no
explicit compressor envelope detector; do not infer compressor ratio/attack/release
from the screenshot or from a steady state sine simulation.

No circuit improvement is proposed in this revision. The generic models and
uncertain clipping network can materially change bias, gain and harmonic results.
