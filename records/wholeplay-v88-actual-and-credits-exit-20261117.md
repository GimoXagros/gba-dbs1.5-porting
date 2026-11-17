# Fresh v88 campaign and normal credits exit

The fresh E212 campaign ran on the private emulator desktop from core 1 with no supplied save. The original process exited with code 1 because the observer expected a different credits exit hook. The game itself reached the native ending constructor.

## Actual campaign

The finalized launch `2BFD40718A37D23E528F705082165939ED70E006C2949EFDEA86FFFEF5F6C5DB` indexes 395 verified files. The actually loaded ROM was identical to both E212 build outputs. The first 287 captured image and memory files through healthy Shoot matched the v87 replay byte for byte. Campaign row 2 produced and activated all eleven encounters in this order.

`8 → 1 → 9 → 6 → 10 → 3 → 2 → 4 → 5 → 0 → 7`

The progress 9 and 10 HUD tilemaps matched their native words. Iraira's sampled physical backdrop is black and its 38 palette projection words match the captured counters. All eleven active encounter snapshots had valid owners and nonblank frames.

The requested assistance comprises 31 score writes across the ten ordinary encounters and exactly one two-byte HP write in each of stages 7 and 11. Stage 11 HP went from 37 to 1 at core 89469 after the live actor checks. The game's ordinary shot recorded lethal damage at core 89483. Native terminal cleanup requested the Results transition at core 90919.

| Core | Observed native transition |
| --- | --- |
| 90920 | 7 → 8, Results |
| 90943 | 8 → 12 |
| 92716 | 12 → 13, credits |
| 102011 | 13 → 11, ending |
| 102012 | Ending constructor `080BF1D0` entered and the old observer stopped |

The hardware mode-word writer was observed at `08015B64` with retained caller `08015AE4` on each transition. The first failure capture is explicitly an observer guard stop before the ending instruction, with a frame-boundary export at 102013. Mode 20 and the eventual title were beyond this run's observations.

## Credits exit producer

The original mode 13 slot schedules source callback `75AA1A`, which guards its natural end on cursor `ES:[2] >= 22` and exact complete flags `ES:[040A] == 003F`. It retires two tasks, then stores transition request `1,0,0` at source `75AADA`, `75AADF`, and `75AAE4`.

The matched E212 callback is `080CA2C0`. Its guard uses `03003DA2` at `080CA310` and `03004270` at `080CA324`. It calls the two corresponding retirement services and writes the tuple at `080CA388`, `080CA390`, and `080CA398`. The natural exit hook is the immediately following `080CA39C` with instruction `E8BD0020`. A separate fade callback issues the same tuple and remains observable at `080CBCC0`. Mode 13 selector 0 maps to 11 in both native and source mode tables.

The ending capture confirms cursor 22, exact complete flags `003F`, and last credit page pointer `080D0038` with next index 14. Held and edge inputs are zero. One old credit task slot is inactive and the other contains a newly created ending callback. The old replay observed the real mode change and compatible final state. The new hook is needed to directly log the natural exit producer.

Exact ARM fixtures using this capture's owner values reject cursor 21, flags `003E` and flags `013F`. Cursors 22 and 23 with flags `003F` reach both retirement calls and the ordered stores. Native retirement and audio service internals are modeled at their entry points in this fixture.

## Follow-up replay preflight

The reviewed follow-up keeps the same 16 MiB E212 image, copied bootstrapped checkpoint at core 89405, five-region restore guard, guarded stage 11 write, and 15-frame ordinary shot lead. The two unique Lua changes add the typed natural-request observation and extend the replay cap from 8000 to 16000 advances. The host inverse changes only its output version token, pins file, and both occurrences of the selected probe name. Its private descriptor, 360-second deadline, and approved HP write scope remain intact. All 30 opcodes match E212 and the frozen author fixture reports nine passes.

| Artifact | SHA-256 |
| --- | --- |
| Fresh capture checker | `8E348B0980CBF7669BF6220B1DAE49DFC2B3895AE2B58D9B9C16E73720A879B8` |
| Fresh capture report | `F03C8BE3DB14AE58CD40D9C35EA7384E7EF831AE2AC4241B3CD12241914D9094` |
| Natural credits checker | `A58EE358EC7526AFC96CE83AB866E65DE7B359FBC6C027911AD9293DCA4ADBCC` |
| Natural credits report | `F3DEA4B824943A163BFB8CDB349D6E5C6F2AA4790DDF2BAF0D0208CBF8C853B9` |
| Revised checkpoint observer | `F92720EE9EA08A48FC2AE188AE972BD7D0B2B0864014DA868FD24635EBFCBB24` |
| Revised private launcher | `99D34A9E252ACC7CDC95A26DB1247998ACDEE06E7561220DDCC209783C18CB1F` |
| Revised six-input pins | `F5BDA2FF469B0257FD517F135ACB249205DE2D15186AD412EAFD3674AB7D3803` |
| Revised Lua author fixture report | `29EC244AB79A9EFBAF8B47B99CC07BDCEECD03A6523A0991DDEC07296040F94D` |
