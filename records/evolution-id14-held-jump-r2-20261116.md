# ID14 ordinary held-jump refinement

The first new ordinary ID14 capture is preserved at
`build/bizhawk-id14-evolution-20261116-a`. It did not evolve P1; CPU1
claimed Calumon. At core8400, P1 and Calumon were nearly horizontally
aligned, but P1 remained1183 world units below. The capture does not
directly observe P1's short-jump flag, so vertical shortfall is a supported
controller hypothesis rather than a proved native contact defect.

Source Ver.1.5 C415 at768001..768015 tests held A during preparation.
Releasing A sets actor+8C to1 unless the special actor flag is set. Source
768068..76808E selects short-jump parameters at physics+14/+16 if that
flag is1, otherwise full-jump parameters+4/+6. Native356BCC..356BE8 and
356C70..356CA0 preserve this distinction at actor+A2. Native preparation
starts with16 frames at356B9C/356BA0. The old4-frame periodic press can
therefore select the short jump; its first partially overlapping press
can be even shorter. A fresh edge still starts the jump, as established
by the retained helper and controller contract.

The actual ID14-a retained physics pointer is084851A4. Its signed full
velocity/gravity pair is(-1240,50), compared with short(-640,31). These
are native parameters, not a promise of a particular contact height.

The new wrapper `tools/bizhawk_probe_evolution_id14_r2.lua`, SHA
A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA,
keeps DA591 and its failed capture untouched. It changes only the jump
policy: while the selected live P1 is valid, start an ordinary A press
when collectible Calumon is above and the ordinary-kind P1 is grounded;
hold20 consecutive frames, release for at least one frame, then permit
another start only when grounded. The held press continues through its
deadline if Calumon stops being collectible. Existing horizontal contact
movement, inactive preposition, pause schedule, provenance hooks,
terminal conditions and frame bounds remain unchanged. No game state is
written or forced.

`tools/check_evolution_id14_r2.py`, SHA
57363252F3E1D71D4D9224B1EAE675F02E6079E4E9957B5D72C63F84B86A1691,
pins the source, actual native opcodes and ID14 parameter pairs. It reuses
the frozen four-case Lua54 composition/closure check with focused held,
deadline, release, airborne refusal, ordinary-kind refusal, grounded
rearm, collectible-disappearance and valid-P1 tests. Report:
`build/evolution-id14-probe-r2-20261116/author.json`.

Independent review and a new actual capture remain required. This author
did not run an emulator, change main, alter any previous probe, or replay
the historical seed17/no-hit route. No E5 cause or actual ID14 evolution
is claimed by this controller change.
