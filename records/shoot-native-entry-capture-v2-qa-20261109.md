# Corrected native entry capture: independent QA

**Integrity and native case5/scene arrival pass; active Shoot remains unreached.**
The completed hidden run `build/bizhawk-gba-shoot-entry-20261109-b` exhausted its
120000-frame budget at core120001 with `bounded-no-activation`. Exact D0A01 ROM,
driverD40, observer7513 and host019A remained unchanged. The reviewer launched no
emulator, loaded no state and changed no runtime, ROM, main or Git file.

All100 recursively inventoried files and12 complete snapshot sets verify. The first
three ordinary snapshot sets,21 files including PNGs, are byte-identical to run-a.
All26 ordinary scoreWORD999 entries retain their approved addresses/stages and
positive P1HP. Exactly one stage7 SECOND+64 WORD1 write occurs at core64229:
FIRST02011710 HP8, SECOND02011828 HP37→1. There are no stage11 writes.

| Native event | Core | Independently verified facts |
|---|---:|---|
| Authorized boss HP1 | 64229 | Owned active native stage7 pair and kind3 auxiliary; one WORD only |
| Genuine outer checkpoint | 64230 | P1HP8/bossHP1, consumed=true, next input-relative64229 |
| Actual FIRST hit | 66972 | R4=FIRST, R5=SECOND, R0 damage1, R8 computed0; paired hooks retain HP1→0 facts |
| Root5 / case5 | 66972 | P1HP4, difficulty2, progress01C0 eligible; R8 selected085C8000 |
| Native scene / saved HP | 66973 | Real owner02012200, savedHP4 |
| Final bounded state | 120001 | Scene active at085C8400, savedHP4, temporary P1HP1, bossHP0, stage7 |

The pre/post damage memory exports both occur after the frame. Their copied scalar
hook operands and the frozen guards establish the before/after pair; the full RAM
files are not falsely presented as instruction-adjacent HP1 andHP0 snapshots.
Callback R15=hook+4 is retained and checked. No initializer call, saved-health
restore, activation tail or healthy-activation checkpoint was observed.

Final IWRAM/EWRAM/VRAM/palette/OAM sizes, hashes and game fields agree with the
summary. The scene owner header remains active with callback085C8400 and savedHP4.
Native control word03004508 is0002; active Shoot flags0300450A remain0. These are
the captured wait-state facts, not a successful initialization or gameplay claim.

The stage7 checkpoint is genuine and ready for a separately controlled short
continuation. Its ZIP has valid CRCs, unique expected entries and BizHawk2.11.1
metadata. The decompressed Core contains528432 native bytes plus the exact21-byte
managed suffix; its managed frame is64230. Native version01000009, ROM CRC and
title match the exact loaded ROM. Complete IWRAM/EWRAM/VRAM/palette/OAM slices equal
the same-frame05-stage7-checkpoint dumps. Metadata also matches native mode,
stage, difficulty, progress, pointers, HP, fighter/base and service handles.

This parsing follows the [BizHawk2.11.1 state writer](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Emulation.Cores/Consoles/Nintendo/GBA/MGBAHawk.IStatable.cs),
the exact submodule94b1578f [native wrapper](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/platform/bizhawk/bizinterface.c),
[state layout](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/include/mgba/internal/gba/serialize.h)
and [version producer](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gba/serialize.c).
The header's version comment is stale; the actual producer defines version9.
Exact downloaded source hashes are recorded in the machine report and archived
under the QA directory. No frame, register or RAM offset is guessed from a mock.

Eleven mutations of the actual captured checkpoint are rejected in memory: ZIP
CRC, wrong BizVersion, native length, managed frame, ROM CRC, each of five full
memory-region equalities and P1HP metadata. No mutated artifact is written to the
capture directory. No previous campaign, ARM or regression suite is repeated.

| Artifact | SHA-256 |
|---|---|
| Completed launch | B608717EE5C9EE10D99D38B1F198023F96B665615E23237A3AA8F8A07AB8A98E |
| Genuine stage7-hp1.State | 438C859880FBC9D8F6B700641288E6E62FCEF079075EA64D29A83708EFB51204 |
| Decompressed full Core | C6E8036B8E316D0DC83D091B559414C08635FABEA3EE2467880A110B6216CA6F |
| Complete native payload | 3B0155A7275E19B6374857D7BA82ACB23838D2E4C5BB7E39CD97706A8D62453A |
| tools/verify_gba_shoot_entry_capture_v2.py | 4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68 |
| Final independent report | 9EFFC3426CD09E77904661BD58C30185537B2541295BF7D106C8A8625C3A370E |

Report: `build/gba-shoot-entry-capture-v2-qa-20261109/final-report.json`.
Reproduce with a fresh output filename:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/verify_gba_shoot_entry_capture_v2.py build/bizhawk-gba-shoot-entry-20261109-b --output build/gba-shoot-entry-capture-v2-qa-20261109/new-report.json
~~~

`checkpoint_core(blob)` exposes exact decompressed Core bytes for a future full
restore comparison. This audit proves the saved artifact and matching memory; it
does not prove restoration. Native initializer/activation, E5 cause, terminal
continuation and complete port QA remain open.
