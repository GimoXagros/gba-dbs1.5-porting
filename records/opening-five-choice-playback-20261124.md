# Cold opening, all five choices, and Start skip

On the frozen WonderSwan 1.5 source `C415F227` and GBA candidate `D432DBE9`, two isolated non-displaying BizHawk sessions cold-booted with empty save directories. Each ran without input until all five opening endings cycled naturally and returned to the title. Two separate cold sessions used one ordinary four-frame Start press during added callback 8. No BIOS, RAM, registers or save slots were changed by the observer. The full loaded ROM dumps matched both inputs byte for byte.

The owner was consistently WSC RAM `C234` and GBA EWRAM `10118`. Both traversed all 19 linear callbacks in the same order on each of five cycles. The final choice sequence was 0, 1, 2, 3, 4 with the original five selector pairs, followed by wrap to 0. Source callback 4 was recognized at its existing six-byte entry stub. The check distinguishes execution of a graph path from equivalence of the assets it displays.

| Choice | WSC entry → title frame | GBA entry → title frame |
| --- | --- | --- |
| 0 | 518 → 3513 | 537 → 2886 |
| 1 | 8918 → 11913 | 7266 → 9615 |
| 2 | 18098 → 21093 | 14895 → 17244 |
| 3 | 26498 → 29493 | 21565 → 23902 |
| 4 | 35678 → 38673 | 29182 → 31519 |

Pressing Start 15 frames after entry into callback 8 reached title on both systems. The source took 101 source frames, from 1972 to 2073. The GBA took 42 native frames, from 1690 to 1732. Both selected the terminal callback on the following frame. The source held it for 50 frames before convergence and the GBA held it for one. Platform refresh rates differ, so these native-frame measurements should not be interpreted as the same unit of elapsed time.

The two physical pictures eight native frames into choice 3 show a visible discrepancy. WSC shows a gold-and-blue fighter on the left and a green-and-gold fighter on the right. GBA shows a gray-and-yellow fighter on the left and a purple fighter on the right. At choice 0, the sampled left fighter is a dark silhouette on GBA while the WSC image shows colored details. No particular pointer, palette owner or animation error is inferred from these captures. The pictures were sampled by callback and native frame count, without an assertion of exact visual phase alignment. No PCM was recorded.

`tools/run_opening_playback.py`, `tools/bizhawk_opening_playback.lua` and `tools/verify_opening_playback.py` produce the record. The four input directories to the verifier were `build/opening-playback-wsc-full-20261124-b`, `build/opening-playback-wsc-skip-20261124-b`, `build/opening-playback-gba-full-20261124-b` and `build/opening-playback-gba-skip-20261124`. The source full run used a 42,000-frame limit, the native full run 43,000, and both skip runs 5,200. Each exited on its own title condition.

The local report `build/opening-playback-comparison-20261124/verified.json` has SHA-256 `581F3597F1A86A3CC730E18FE21FAA1AC759D8F4EC95110376BD00B2117D777D`. The comparison image `opening-choices.png` in the same directory has SHA-256 `D3D97A6A9E53ED8FC07AC6244208E2816F195C9B17B0A90F0DA6FC77C418147F`.
