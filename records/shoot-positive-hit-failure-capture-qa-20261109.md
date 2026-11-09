# Positive-hit trial failure: independent capture integrity — 2026-11-09

PASS for integrity of the preserved failed observation in
`build/bizhawk-gba-shoot-positive-hit-20261109-a`. The trial did **not** observe
a successful positive hit or flash expiry. Its observer rejected a dispatch
target at callback core69165; the outer frame completed and full snapshots
were exported at69166. This audit does not classify the target's execution
semantics, infer an E5 producer cause or claim that the emulator crashed.
Source/rectangle/dispatcher causality belongs to the separate source audit.

All29 files exactly match the finalized launch inventory. The three frozen
script pins, host036C, reviewed pin file, exact copied/loaded6D ROM and seven
original/checkpoint copies remain unchanged. The launch reports completed
without host stop or deadline, on a private desktop with physical background
input, SaveRAM autosave and automatic state loading disabled. This reviewer
started no emulator, loaded no state and changed no evidence or guest data.

The actual input stream contains239 contiguous advances, ending at69166.
Every input's A/B phase and measured direction matches the frozen policy:
four A pulses and twenty B pulses. The initial A1/release5 and later native
A40/B80 held bits agree with the corresponding frame records. FIRST remains
HP4 and SECOND HP37 throughout those239 records. No paired positive-damage,
nonfatal adapter, flash8, timer-update or expiry observation is present.

The immediate scalar failure file is exactly the prefix of the later trace
through the failure's copied registers. It predates the next frame and the
full snapshot. The retained before-instruction facts are:

| Field | Captured value |
| --- | --- |
| Observed callback/core | `0836EBA4` / `69165` |
| Exposed R15 | `0836EBA8` |
| R0 / R1 | `00000000` / `FFFFFFF0` |
| R8 / R9 | `0836EBA8` / `0A000003` |
| R4 / R5 | `020112B0` / `02011710` |
| LR | `08353FF0` |

The later full snapshot is an outer-frame observation at69166, not memory
from that instruction. R9's mirror/odd-address interpretation and whether
this is a real unsupported route require the source audit. No first-E5
producer record is supplied by this failure; R0=0 is retained as a raw
register fact and is not casually relabeled a collision producer type.

Both00-before and invalid-dispatch-target states are genuine BizHawk2.11.1
GBA ZIP states with valid CRCs/unique entries, correct ROM identity and managed
frames. Their entire decompressed IWRAM/EWRAM/VRAM/palette/OAM equal their
separate same-frame dumps. SyncSettings remain identical and only the new
output/checkpoint/probe arguments survive in UserData; old authorization and
frame-budget fields are absent. Both states retain live input08374FF4 and
battle083735BC owners. The later state has flags0046, compared with0006
initially; that post-frame flag value is not projected backward to the hook.

The restored state and00-before state are byte-identical. All five initial
game-RAM regions exactly equal the healthy source checkpoint. Strict full-Core
identity is nevertheless **false**, and remains false even after the explicit
current-ROM CRC expectation. The exact differences are preserved:

- Versus the unmodified original Core: offsets12,13,14,15,326,327,330,342,343,
  384,385,393,397.
- Versus only CRC-adjusted source expectation: offsets326,327,330,342,343,384,
  385,393,397, with every expected/actual byte stored in the report.

The source Core hashes to6A81B95E…; the actual restored Core hashes to924A0DCF….
The complete CPU bank slab, native extension data and managed suffix remain
equal. These are qualified loaded-state observations, not a silent rewrite
of the full-Core equality criterion. No older loader-difference pattern is
used to exempt or normalize this run's actual differences.

Both PNGs are valid240×160 images. Restored VRAM initially contains the source
checkpoint's existing HUD tiles. A still-visible000 cannot prove or disprove
the new HUD guard's cold-entry rendering. This audit makes no HUD visual
parity claim and performs no RAM erase; a later cold/new6D entry would be a
separate visual gate.

| Frozen artifact | SHA-256 |
| --- | --- |
| `tools/verify_gba_shoot_positive_hit_capture.py` | `C49AEB9B5A528E714D86E12396A046897259E63C2EA561C1EE8CA681D31A6A2A` |
| `build/gba-shoot-positive-hit-capture-qa-20261109/final-report.json` | `D240D22DB04A801DB70753C7B0B64D1B413C16F430F7FCF2B37CB75F3103EA2C` |
| Immediate scalar failure | `D3404F52ABF8FF9D81575D79C0BDBE62BEF20BE37A026499EB64E3591EE16C01` |
| Failure genuine state | `FF4B0B3E8545FE128074FF7FE10BE3E4FEDBE84DB1788FE58C57F7A7135E87A4` |

Reproduce to a fresh output report:

~~~powershell
python -u -X utf8 tools/verify_gba_shoot_positive_hit_capture.py --output build/gba-shoot-positive-hit-capture-qa-20261109/new-report.json
~~~

The actual failure evidence and frozen9F12 observer are preserved without a
rerun, clamp or behavioral change by this reviewer. Positive-hit gameplay,
expiry, full Shoot lifetime and E5 causal closure remain open.
