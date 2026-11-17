# Actual E212 Shoot replay returns to the title

The original r4 checkpoint replay exited successfully. All 166 indexed capture files, the loaded 16 MiB E212 image, private no-supplied-save launch, frozen scripts, and exact copied checkpoint agree. The five restored regions match and the complete restored Core matches the prior restoration after qualifying only the ROM CRC. The 15 original-to-resaved-Core differences remain explicitly recorded.

The ordinary mirrored attack inputs and sole guarded boss HP write match the prior checkpoint replay byte for byte. The real shot reduced stage 11 boss HP from 1 to 0. The checkpoint route and full campaign share the confirmed startup and combat handoff, then the checkpoint replay exposes the complete ending tail.

| Core | Observed native event |
| --- | --- |
| 89469 | Guarded stage 11 HP write at `0201188C`, from 37 to 1 |
| 89483 | Real damage 1 by FIRST `02011710` against SECOND `02011828` |
| 90920 | Mode 7 → 8, Results |
| 90943 | Mode 8 → 12 |
| 92716 | Mode 12 → 13, credits |
| 102010 | Natural mode 13 request with cursor 22, complete flags `003F`, tuple `1,0,0` |
| 102011 | Mode 13 → 11 |
| 102729 | Completed final card waits for ordinary A, with flags `0001` and fade timer 75 |
| 102806 | Native mode 11 card issues the next request |
| 102807 | Mode 11 → 20 |
| 102838 | Native mode 20 art owner active with priority `FFFFF100` |
| 102868 | Native mode 20 emits the title request |
| 102869 | Mode 20 → 3 |
| 102870 | Native title callback observed, frame exported at 102871 |

Both mode 20 memory captures match all 408 source tiles at `06003200..06006500`, including 26112 planar pixel indices, with all 504 map cells at `0600F800`, 96 original palette colors and 32 retained padding colors. Live `BG0CNT=1F02` selects the installed BG0 screen and tile bank. The install snapshot still has a dark interior. The return snapshot and subsequent native title frame visibly show the Battle Spirit Ver. 1.5 source art and border.

The preceding fresh campaign verified all eleven encounters and reached the ending constructor before its observer stopped. The checkpoint replay completes the remaining native path from the exact healthy state. Together the captures cover the path with the stated assisted controls. They are two runs. This E212 replay also retains the native optional staff card that WSC 1.5 bypasses. Mode 23 uses a separate candidate and awaits its own runtime validation.

Checker `tools/verify_shoot_checkpoint_results_v88r4_capture.py` SHA-256 `B4BAE6373E457B7155F62FC007D8E0506BA344B50FF6A241C7E09F29053D5820`. Final report `build/shoot-checkpoint-results-v88r4-independent-20261117/final.json` SHA-256 `B4832A0D31DCA7E4F740D6D7852C4ABED22D46C9D2154EFFEAF72EC9522A6C66`. Exact launch SHA-256 `AB2F14BB32862C7FB9268F0BD63555A7B19F74CC72C0DC85E7883C23E2A28757`.
