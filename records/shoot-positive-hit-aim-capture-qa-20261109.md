# Actual aimed Shoot hit: independent capture audit — 2026-11-09

PASS for the completed `build/bizhawk-gba-shoot-positive-hit-aim-20261109-a`
observation. Ordinary input produces an actual FIRST→SECOND positive hit at
core69014: HP37→36, damage1, while FIRST remains HP4. The real nonfatal hook,
resident adapter, palette loader result, eight timer decrements and native
expiry are observed. Final export is core69023, FIRST HP4 / SECOND HP36.
This establishes this bounded positive-hit/expiry path, not terminal Shoot,
historical E5 closure, or cold-entry visual HUD parity.

All42 files match the finalized launch inventory. The exact1477 ROM, copied
source checkpoint, four script pins, frozen00D wrapper/9F12 observer,50A7
host, private configuration and unchanged checkpoint copies pass. Physical
background input, automatic last-state loading and SaveRAM autosave are
disabled. No supplied save, host stop, deadline or guest writes occurred.
This reviewer only read completed files; no emulator or state was loaded.

## Actual input and native route

All96 input/frame pairs are contiguous. Right is held only at cores68927
and68928; its native held bit is0002, the first edge is fresh, and the
second held frame has no repeated edge. No A or Left is pressed. A single
B occurs at69000, relative74, with a fresh native0080 edge and previous B
held clear. Its measured ready callback is0835620C, freeze0, facing4000 set,
upper event0001, dx97 and dy231. All recorded decisions match the frozen
policy's ready/freeze/facing/event/window and prior-held conditions. The
airborne bit is not separately logged each frame; the already-reviewed
frozen policy tests it, no A is pressed, and recorded player Y stays5376.
Inputs are released after the confirmed hit through expiry.

Scalar before-instruction records identify FIRST02011710 as attacker and
SECOND02011828 as victim. The before-HP-store record exposes PC0836E5E8,
old HP37, R0 damage1 and R8 computed36; the next observation exposes
0836E5EC with HP36. Hook0836E634, adapter085CD9A0 and flash-complete085CDA20
are reached in the same core69014 advance. Exposed ARM R15 is instruction
address+4. R13 at damage and flash completion is identical, corroborating
the real palette argument frame was balanced.

## Flash, timer and genuine captures

The first-positive-hit and flash-eight full snapshots are exported after
that advance at69015; they are byte-identical, including genuine State and
all five RAM dumps. Their 15 OBJ palette halfwords05000222..0500023E match
native flash data at ROM5C0B08. Sixteen BG and eight OBJ color-zero entries
are red001F. SECOND's timer is8.

Eight actual before-store records occur at cores69015..69022, with timer
8..1 and computed value7..0; victim R5 remains SECOND. The actual expiry
entry is at69022, R4=SECOND and LR08586C90. Flash-expired outer capture is
69023 with timer0. Its15 P2 palette halfwords match high-HP native data
587108. All16 BG color-zero entries equal the pre-hit snapshot; BG1..15
also match the native restore table586F40. BG0 at the outer frame is0C63,
where that table's immediate entry is0000. The capture therefore does not
claim all16 outer values equal the immediate table. Eight OBJ color-zero
entries remain001F; they are not counted as restored.

00-before68927, first-positive-hit69015, flash-eight69015 and
flash-expired69023 are genuine BizHawk2.11.1 GBA states. ZIP CRC/entry
structure, native frame/ROM identity and all complete IWRAM/EWRAM/VRAM/
palette/OAM regions exactly match their independent same-frame dumps.
All four retain mode7/stage11, typed active FIRST/SECOND/aux pool objects,
actual self/opponent/aux links, SECOND/aux resources, and live input
08374FF4 / battle083735BC controller task owners. SyncSettings are
identical; UserData contains only probe/output/checkpoint arguments.
PNGs are native240×160. No invalid producer, overlap, scratch, dispatch,
P1-death/loss or failure artifact appears in this observation.

## Whole-Core qualification

The restored whole Core equals the previous1477 bounded trial's restored
whole Core byte-for-byte. Original healthy Core SHA is
`6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93`;
actual restored Core SHA is
`4A282CF92BD125BC0C9045CF1546482B2AD6AB72DABF2009E4FE22AB5586F783`.
Against the original healthy checkpoint, changing only comparison bytes
12..15 to the current ROM CRC still leaves nine actual differences at
326,327,330,342,343,384,385,393,397. Both raw and CRC-adjusted comparisons
remain false and are reported without normalization. CPU banks, native
extensions, managed suffix and all five initial RAM regions are equal.
Inherited HUD tiles in that checkpoint do not establish cold-entry HUD
visual behavior.

## Reproduction and pins

Run the read-only auditor:

```powershell
python -u -X utf8 tools/verify_gba_shoot_positive_hit_aim_capture.py --root-completed --output <new-report-path>
```

- Verifier: `tools/verify_gba_shoot_positive_hit_aim_capture.py`
  SHA256 `0F5339FEFFD7DD8B4DF5EF512DCA5EDA52A085AB7A1B88CCDEDA33EEEC132935`.
- Final report: `build/gba-shoot-positive-hit-aim-capture-qa-20261109/final-report.json`
  SHA256 `2A94A3374A5563C3D25E4042745A207CE726AAA30F0EA155B2DE676D8D76C74A`.
- Launch inventory SHA256
  `7DFFB932831C9C63E02EC55046329E5AA5C95A628BF6C7D3243525CB493C3E53`.

The earlier `report.json` is a provisional audit before added typed-link,
native Right-edge and constant-Y assertions; `final-report.json` is the
frozen completed result. No old full suite was rerun and no author,
observer, host, ROM, main or Git state was changed.
