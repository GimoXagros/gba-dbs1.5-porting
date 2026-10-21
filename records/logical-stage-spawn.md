# Logical-stage fighter spawn, 2026-10-16

The ordinary fighter constructor still read the campaign progression byte
directly after the earlier relocated-literal repair. The existing temporary
arena selector already sends characters 11, 13 and 14 to logical stages 10, 8
and 9. This produced a second inconsistency: character 13 could use Train
graphics and collision while receiving stage 1's starting coordinates.

`tools/build_logical_stage_spawn.py` changes one instruction at `08582F00` to
enter a 28-byte adapter at `08627900`. The adapter saves `r0` and LR, calls the
existing selector `080D1C78`, moves its result to `r1`, restores the saved
registers, restores `r8=03002310`, and rejoins at `08582F08`. It leaves the
existing variant selection and all four current/previous coordinate stores
unchanged. SP is balanced. The selector changes flags, but the original CMP at
`08582F10` overwrites them before the first conditional use. No progress byte
or other persistent state is written.

Source `743654..7436A4` selects the same source spawn table and bias: stage*16,
an extra 16 bytes from stage 7, variant&3 only for stage 6 (otherwise variant&1),
and a four-byte second-player offset. The complete source table
`743224..7432E4` equals the installed native table `08583000..085830C0`.
Ordinary stages 0..10 are source-backed. The unchanged last stage-11 placeholder
is only bounded; dedicated Shoot entry remains outside this ordinary-spawn
contract.

The separate verifier imports no generator. It decodes 44 native instructions,
checks 24,576 character/progress/variant/player combinations, including 22,552
source-backed coordinate cases and 24,288 unchanged default-character cases,
and rejects ten semantic mutations. It also verifies exact full-ROM inverse,
blank predecessor bytes, and no existing pointer, ARM branch, or immediate
PC-relative load into the new interval. Only the hook word and `627900..62791C`
are owned by this layer; 32 bytes change in total.

```powershell
py -3 tools/build_logical_stage_spawn.py `
  build/added-stage-collision-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/logical-stage-spawn-20261016/current-candidate.gba `
  --manifest build/logical-stage-spawn-20261016/manifest.json
py -3 tools/verify_logical_stage_spawn.py `
  build/added-stage-collision-20261016/current-candidate.gba `
  build/logical-stage-spawn-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/logical-stage-spawn-20261016/verification.json
```

Candidate SHA-256:
`83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD`.
Manifest SHA-256:
`A642A2579280D72A9E5B97916680DEA7A59E4E5E7DB84F66C71C99BF47FEC44D`.
Independent verifier report SHA-256:
`D8C5A070EDA84A4CAD2ACB8A0D3910BEE7B1E5272990918F60F49F0D64BE5094`.

This makes one more consumer consistent with the already installed temporary
character-to-arena routing. It does not implement the original campaign stage
progression, finish Train's stage behavior, or claim runtime validation of this
new adapter.
