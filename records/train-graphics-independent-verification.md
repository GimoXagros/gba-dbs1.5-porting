# Independent Train consumer verification, 2026-10-16

`tools/verify_train_graphics_repair.py` independently verifies candidate
`96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530`
against logical-spawn predecessor
`83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD`.
It imports no generator and does not launch an emulator or open save data.

The verifier walks all 100 source/native map descriptors and 50,400 cells
including aliases, all 32,768 retained tile pixels, and 111 retained palette
entries. The 36 unique maps use either tile0 in the common tile bank or a tile
in the 512-tile uploaded bank. Blank tile0 is a common-stage lifecycle
precondition; the separately recorded parent runtime confirms it for the tested
entry, rather than proving every possible lifetime here.

Sixty native and 25 source instruction/data-flow contracts bind the actual BG
constructor, initial fill, scroll, camera, palette owners and queue snapshot.
All 211 installed ARM instructions have explicit boundaries. A restricted
instruction walker checks eight initializer call/stack paths, 12 palette-cycle
states, 8,192 RGB444 projector paths, five disabled paths, and 9,216 routing
cases. Existing native service summaries are bound to their preserved machine
code and argument consumers; this checker is not runtime gameplay execution.

An apparent queue-owner mismatch was resolved through the actual snapshot:
source `1000:02CE..036F` copies to `0300:0044..00E5`, mapping producer
`1000:0330` to display shadow `0300:00A6`. Native `08017768..08017798` copies
400 bytes from `03002478` to `03004578`, mapping `03002568` to `03004668`.
The normal-frame path calls this copy at `080D0BE8` before installing the
display callback at `080D0BFC`. Keeping these two distinct addresses is correct.

The initial map fill's four-byte index stride remains safe because both new BG
objects have selector zero immediately after their clear. Ongoing refills use
the actual eight-byte descriptor stride. Both camera adapters are checked for
their exact load, literal and continuation, with explicit damaging mutations.

Twenty semantic negative cases are rejected. Exact Expected Write spans,
predecessor FF ownership, existing pointer/branch/literal exclusions, and the
full-ROM inverse also pass. Final report:
`build/train-graphics-repair-20261016/verification.json`, SHA-256
`C4DCF5669AB21BB92978EE0ECE6B5EC027BC0CDF42CDE72D1FBDB9AEDFF084EC`.
This supersedes the earlier report beginning `9B486D36`; the ROM is unchanged.

```powershell
py -3 tools/verify_train_graphics_repair.py `
  build/logical-stage-spawn-20261016/current-candidate.gba `
  build/train-graphics-repair-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/train-graphics-repair-20261016/verification.json
```

Train's source-only hazard state machine and the original campaign routing are
separate remaining work. This verification does not convert those omissions
into a completion claim.
