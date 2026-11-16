# Impmon Calumon gate: isolated Ver.1.5 default-mode repair

The current port retained the retail Impmon denial even though its installed
roster and resource policy follows the default Ver.1.5 mode. This prevented
the native normal Calumon contact branch from assigning Impmon's evolution
callback. The isolated component changes one conditional branch to an
unconditional branch to the existing normal/boss identity gate.

| Item | SHA256 |
|---|---|
| `tools/build_impmon_evolution_gate.py` | `C7D88E9E07E683DF73D56F5097EA422DF484D111D4EDCF70CAF76119274EBF73` |
| C344 input | `C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278` |
| `build/impmon-evolution-clean15-20261116/component.gba` | `8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8` |
| `build/impmon-evolution-clean15-20261116/manifest.json` | `32AD301794BEE771211F53E75C1CDC7DE8BE8E7A030C32356A11519564CD48D9` |

CLI: `python tools/build_impmon_evolution_gate.py --before C344.gba --gba retail.gba --wsc10 original.wsc --wsc15 version15.wsc --output fresh.gba --manifest fresh.json`.
All four inputs are fully hash-pinned; outputs must be fresh and nonaliasing.

Original WSC1.0 at3927ED..392835 compares kind8, then unconditionally tests
fighter identity11 and takes the non-evolving special Calumon animation.
WSC1.5 at742ACD..742B1D adds `test byte es:[0073],1` first. When clear,
identity11 takes the same normal callback assignment as other fighters:
source668E:0A33, corresponding to native0835A0F8. The existing current
native3546F0..354738 is byte-identical to the retail denial block.

The source flag is also game state004E+25, gating the extra default roster
members13/14 and unlocked12 at7787F3/778808/778826. Existing native roster
production already specializes the flag-clear Ver.1.5 policy, with count13
and the immutable extended roster views. This repair has that same scope.
It does not invent a corresponding native RAM flag or claim alternate-mode
support. A numerically guessed native2335 address is not used.

The only declared four-byte span is raw354700:
`1A00000C` (BNE354738) becomes `EA00000C` (B354738). Exactly one byte changes.
No cave, new memory owner, asset, timing, sound table or runtime input changes
are introduced. Restoring that word reconstructs all16MiB of C344 exactly.
The existing native35473C boss comparison remains15; actor12 was already
admitted and remains unchanged.

Author verification executes519 bounded actual-ARM cases: all16 identities
with every initial NZCV pattern before/after, three non-Calumon branches,
and the actual subsequent group1 loader caller. Every non11 identity retains
the complete modeled register/memory/write/call state. Identity11 now installs
0835A0F8 and the collector link, then calls the existing normal36D718
continuation. Boss15 remains excluded. The actual35A424..35A440 caller
passes `(group=1,id=11,side=1)` to353304. Effect creation and the group loader
remain explicit service boundaries, not simulated gameplay.

Only the newly reachable source record41 was rechecked: the actual group1
table owner at0860B000 selects ID11 row60B160, whose P0/P1/palettes/P4 are
084B0000/0861B4BC/084A1390/084A1390/08568000. Existing validators walk all39
source events and164 commands, their P0 layouts and tile bounds, both palettes,
and the typed P4 graph. No resource bytes change. This is a narrow validity
check, not a renewed full content or attack-quality approval.

Two harmful mutations reject restoring the old denial and bypassing the
boss identity comparison. Independent verification and actual CPU11
evolution/6F pause/return are required before integration. The original C344
and all prior probes remain unchanged. No main, host, emulator or Git action
was performed by this author.
