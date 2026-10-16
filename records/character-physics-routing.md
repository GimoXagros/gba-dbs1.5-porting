# Character physics source routing, 2026-10-16

The three added-character payloads were converted from the wrong source
addresses. The converter assumed that every character group followed
`3B847E + character * 0x78`. That works for IDs 0–11, but the source program
looks up all IDs in a pointer table, and IDs 12–14 do not follow that order.
The earlier verifier duplicated the arithmetic assumption. Its successful
v49 report therefore did not establish the correct source identity of these
three payloads.

The native pointer repair introduced in v49 is retained. This new layer
corrects the data reached by those pointers; it does not restore the old
one-record-early pointers.

| ID | Source table word | Actual source group | Previously converted group | Existing native destination |
| --- | --- | --- | --- | --- |
| 12 | `0776` | `3B8BD6` | `3B8A1E` | `084850B4` |
| 13 | `0686` | `3B8AE6` | `3B8A96` | `0848512C` |
| 14 | `06FE` | `3B8B5E` | `3B8B0E` | `084851A4` |

Source constructor `7435EC..743612` sets ES=`2846` and C2=`BB`, doubles
the character ID, loads a word from ES:[ID*2], and stores that offset in
object `+4E`. This resolves to the fifteen-word table at raw `3B8460`.
The constructor reads signed halfwords `+24/+26` from the selected group
into object `+42/+44`. The independent verifier checks the actual
instructions, table values, bank-window calculation, and all fifteen
resolved addresses.

The group size remains **0x78, or 120 decimal bytes**. Source evolution at
`7674B4` adds `50` to the stored pointer, and `7674DB..7674F5` reads the
new group's `+24/+26` bounds. Source de-evolution at `76768F..7676AD`
subtracts `50` and reloads the base bounds. Native `083530BC..083530E4`
stores a full pointer at object `+60`; native `0835A3C4..0835A3D0` and
`0835A6E8..0835A708` make the same `+50/-50` changes. The last evolved
halfword occupies offsets `76..77`. The entire 120-byte group is preserved;
this report does not claim that the middle 40-byte row is independently
reachable.

The numerical conversion is independently checked against all 660
halfwords of retail IDs 0–10. The thirteen known ID-11 commercial
differences, including its evolved height, remain unchanged. This repair
does not claim source-equivalent ID-11 evolution behavior.

`build_character_physics_assets.py` now follows the source table by
default. `--legacy-v48-layout` reproduces the historical pointer and
source-routing errors; `--legacy-v49-layout` reproduces the historical
corrected pointers with the incorrect source data. These explicit modes
exist for the frozen build chain. `build_shoot_other_player_binding.py`
requests the historical conversion explicitly. The old verifier similarly
requires `--legacy-v49-source-routing` to reproduce its historical report;
its default source oracle rejects the old ID-12 payload (`320` instead of
`355` in its first converted halfword).

`build_character_physics_routing.py` applies three Expected Writes over
exact v54, confined to the existing raw range `4850B4..48521B`. It changes
120 bytes across 101 halfwords: 35 for ID 12, 36 for ID 13, and 30 for
ID 14. All fifteen pointers, the reserved gap, retail character groups,
instructions, and all other ROM content are unchanged. No allocation or
new RAM state is introduced.

`verify_character_physics_routing.py` imports no generator. It independently
checks source routing, actual native consumers, all added fields, the
retail oracle, and the complete ROM diff. It rejects mutations of each of
the 180 added halfwords and sixteen additional cases, including old
source routing, earlier pointers, swapped base/evolved rows, narrow
pointer stores, incorrect form offsets, a wrong source bank, and a write
outside the three existing payloads.

Results in `build/character-physics-routing-20261016/`:

| Artifact | SHA-256 |
| --- | --- |
| `current-candidate.gba` | `8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2` |
| `verification.json` | `C6823829AF3EC159BF2FAA85C00CE2D5C1E97603CD40BFA35987221D9B42E88A` |
| `manifest.json` | `EB0948FEC306FD1C39F263ACEAB9D06B73B84DD81DA316BB15081BB1435CC72A` |
| current 540-byte physics asset | `B1DC4C8BC816DE6EF5952403C75A1BF4140A8F6A01A2051A33A3F65809EC29DF` |
| legacy v48 asset | `1F632B750D33E68C2D3265A2AB35676CD22145F716800784D13775A23B214600` |
| legacy v49 asset | `93C735C0A3EE3A9DF09243246BE38129B97AF6A88F5C4546C0229FB7339753C3` |

The regenerated v49 ROM, manifest, and verification report were each
compared byte-for-byte with their frozen counterparts and are unchanged.

From the repository root, the repair and independent verification are:

```powershell
py -3 tools/build_character_physics_routing.py build/repro-v54-20261015-a/current-candidate.gba 'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' 'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' build/character-physics-routing-20261016/current-candidate.gba --manifest build/character-physics-routing-20261016/manifest.json
py -3 tools/verify_character_physics_routing.py build/repro-v54-20261015-a/current-candidate.gba build/character-physics-routing-20261016/current-candidate.gba 'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' 'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' --output build/character-physics-routing-20261016/verification.json
```

This establishes and repairs a static source-routing defect. It does not
establish that this defect caused the reported intro corruption. Runtime
attribution and the rest of the port remain separate work. No emulator,
saved state, or supplied save was used by this investigation.
