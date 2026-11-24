# Mode23 turn controller implementation

The new `tools/mode23_rule_controller.py` emits ARM bodies for the ten source
callbacks B1E5, B212, B276, B355, B3BF, B46D, B533, B657, B6C4 and B6EA.
The bounded source interval is raw74BAE5..74C01B, on immutable WSC1.5 C415F227.
The separate scene builder supplies wrappers, placement and typed services.
No ROM, registered mode, title-menu entry or gameplay claim is produced by this
module alone. The shared layout is in `mode23-native-scene-abi-20261117.md`.

## Preserved source behavior

- B1E5/B212 wait75 ticks, advance the participant index, skip the eliminated
  mask, and call BA57 when the index wraps and the halfword turn counter advances.
- B276 highlights the active participant for33 ticks, then selects the player
  aiming callback or the30-tick CPU decision callback from payload byte2.
- B355 changes the eight-bit angle from held masks6/9; pressed40 starts17 ticks
  of delay. B3BF restores the participant's ordinary callback before enabling
  the power-selection phase.
- B46D advances the strength byte by2, wraps values above80 to1, updates the
  source window bottom and accepts pressed40. Source sound requests84/D6/D7
  retain their request types through a required adapter; no equal-ID shortcut.
- B533 and B6EA share the source B55C launch calculation. The latter first calls
  the CPU decision helper BC9C. The unsigned parameter/strength product shifts
  right8; the resulting1.5×value+20 wraps to signed16 before signed sine/cosine
  multiplication. The angle masks toF8 and velocity products shift right4.
- B657 calls the complete BF42 collision helper before testing all participants
  for motion. B6C4 schedules B1E5. B69F's comparison branches to its own
  fallthrough and has no live state effect; body entry flags are not an ABI.

Native context uses flags24, eliminated mask26, turn count28, participant count2B,
turn index2E, strength2F and timer30. The enclosing allocator owns the100h-byte
payload. Bodies preserve R4..R11, SP and LR; they require typed helper preservation
of R4..R11. Controller callback replacements use wrapper symbols, not body symbols.

## Author verification and limits

`tools/check_mode23_rule_controller.py` assembles the real bodies and executes
2,816 cases with the existing ARM walker, adding only a plain ARM7 MUL step.
It compares live context/actor fields, ordered service calls and preserved
registers against source-derived effects. Cases cover all legal eliminated masks
for3..6 participants, direction combinations, all strength bytes, timer boundaries,
CPU/player branches, signed multiplication boundaries and wait-for-motion paths.
A changed source image is rejected. Imported helper calls are explicit fixtures;
this does not validate the actual native adapters or collision implementation.
Only bounded retired stack bytes are excluded from live-memory comparison.

Report: `build/mode23-rules-window-top-20261117/report.json`, status PASS.
Emitted assembly SHA256:
`C541213864702F85CAF0BB87F8BADC788AD92B71A59BA7EEDEDB12C0B1AE88AB`.
Independent source review found no arithmetic/order defect across the ten bodies.
The window helper is named m23_window_top: source OUT09 maps to native shadow
030012BE, not bottom12BF; common frame service adds the native letterbox offset.
Final linked placement, real adapters, complete-scene checks, normal entry/exit
and headless execution remain required before integration claims.
