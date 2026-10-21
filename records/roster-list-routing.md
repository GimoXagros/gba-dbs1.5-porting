# Expanded roster versus live selection state, 2026-10-16

The natural 12-Down selection attempt did not reach the fighter constructor.
`build/runtime-added-id14-20261016/capture.json` has SHA-256
`AFF048903A7219364538C19D634C6FDD6A7DF78D27FB84F7D71B0C2646186422`.
Its RAM dump shows cursor `0300473C=000C` and maximum `03004740=000C`.
The cursor therefore did not wrap at the old index 11 limit.

The concrete defect is a storage overlap. The original selection list at
`03004710` has twelve halfword slots, ending at `03004726`. The expanded roster
hook wrote ID14 into index12 at `03004728`, and optional IDs11/12 beyond it.
Native `08082410` subsequently stores a full presentation handle into
`[03004710+18]`. In the captured state that handle is `02010360`, so index12
contains `0360` and index13 contains `0201`. The real portrait consumer at
`0808323C` reads the selected halfword from this list; index12 therefore
resolves to a handle fragment rather than ID14. The handle is read again at
`08081DC0`, so moving or corrupting it is not a valid repair.

Three indexed list consumers are positively identified: `08081D04..08081D0C`
for a palette variant, `08081FF4..08081FFC` for the confirmed character, and
`08083238..0808323C` for the portrait. The last already has a doubled index.
Other selection references to the same base use fixed fields, including the
live handle at `+18` and the cached character value at `+1E`; they retain their
original addresses. The independent read-only lifetime analyzer is
`tools/analyze_roster_list_lifetime.py`, with report
`build/roster-list-lifetime-20261016/analysis.json`, SHA-256
`5407FFD87B7C5B5DEBC17BE984B3166D114E5632A740C72AFDA447C51288955A`.
It finds 21 literal words and 23 actual ARM literal loads for this base, with
exactly these three indexed selection-list reads. Four other indexed reads in
the selection range are positively based on ROM animation tables.

## Repair

`tools/build_roster_list_routing.py` stops only the three overflowing halfword
stores at raw `5B002C`, `5B0040`, and `5B0050`. The first twelve native RAM
entries remain `0..10,13`; the established count13..15, unlock tests, cursor
behavior, and selection state are unchanged.

Each of the three indexed consumers gets a small branch adapter that substitutes
an immutable ROM list base for the RAM list base. Four 32-byte views cover the
two existing unlock bits at `03002329`, preserving the established clean-mode
order: `0..10,13,14`, then unlocked11 and/or12. The adapters preserve r0, all
other registers except the intended base output, every condition flag, LR and
SP. Their balanced four-byte stack save makes no calls and creates no new
persistent memory owner. Existing index scaling and halfword loads are retained.

The source producer is `7787DB..778847`: the clean-mode branch writes eleven
ordinary IDs, then13/14, then the two unlock-controlled IDs. Its alternate-mode
branch has a different roster. This repair preserves the already installed
clean-mode policy and does not silently change that separate policy limitation.

New exact spans are `628000..628080`, `628080..6280AC`, `6280C0..6280EC`, and
`628100..62812C`. Each is FF in the fixed predecessor, with no existing whole-ROM
encoded pointer, ARM branch, or immediate PC-relative access into it. Gaps stay
unchanged. The layer changes 268 bytes and passes a complete inverse comparison.

The separate verifier decodes all 27 new instructions and binds 30 native and
11 source contracts. It checks all 256 unlock bytes and 10,752 actual lookup
cases across the three consumer forms, plus twelve damaging mutations. The
original twelve RAM stores stop before the handle for every unlock combination.
No generator is imported by the verifier.

```powershell
py -3 tools/build_roster_list_routing.py `
  build/iraira-floor-launch-v2-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/roster-list-routing-20261016/current-candidate.gba `
  --manifest build/roster-list-routing-20261016/manifest.json
py -3 tools/verify_roster_list_routing.py `
  build/iraira-floor-launch-v2-20261016/current-candidate.gba `
  build/roster-list-routing-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/roster-list-routing-20261016/verification.json
```

Candidate SHA-256:
`7DBFA0B464AB9A0E2DA55049855A0BC08AABAAACDA1AF3E21CC780F2864854E9`.
Verifier report SHA-256:
`1CA72D8AE54AA88E6F7786BAE85B1876169FA8225022DE441BB275C6410FCD96`.
Manifest SHA-256:
`44BE4206C91B6163B31D66461261A8E2D63195BEC10FFC6BBC4212565C1CEA49`.
The fixed predecessor is the class14/effect adapter candidate
`7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470`.

An independent agent reviewed both generator and verifier and found no
actionable instruction or address defect. It also checked the ordinary
selection lifetime for the unlock byte: direct global aliases in
`081600..083278` write only `+1A`, `+4/+6/+8`, or `+A/+B`. The palette helper
`0801F4A4` reaches the resource palette path; `08015D38` clears queue owners;
link preparation `0837A554` operates its separate state blocks; and
`080151AC/080151C0/08015424` operate their documented input/link owners.
The positive `+19` writers are boot/state-load `08015908/08015958`, Options
erase `080C35E8`, and battle award `080BF694 -> 085B1118`, outside this ordinary
selection lifetime. Thus selecting a ROM view from the existing unlock byte
does not change the entry snapshot during this bounded menu flow. This is not
a claim about arbitrary calls to state-load/erase helpers during selection.

Runtime confirmation is recorded separately.
No supplied save file was opened and no emulator was launched by this workstream.
