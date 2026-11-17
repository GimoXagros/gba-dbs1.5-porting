# Shoot replay through the active credits

The original private run on the E212 candidate exited with code 1 at core 97405. Both completion files report `failure:bounded-no-terminal`. The run advanced exactly 8000 frames from its restored healthy Shoot checkpoint. It performed the guarded two-byte boss HP write and an ordinary shot, entered Results, completed mode 12, and reached the active mode 13 credits. The replay retained the credits scene when the frame budget expired.

## Capture identity

- Candidate SHA-256 `E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C`. The launched and actually loaded 16 MiB ROM both match the frozen component.
- Final private launch SHA-256 `D977B2A441075153D7B8F6567CF5DEE671583FFB08016CF1E98545A807080FCE`. All 113 indexed files, all six Lua pins, private configuration, and exact launcher and pin files verified.
- Copied checkpoint Core SHA-256 `BCA24A090D8AA084D25A4B6F7F31820DD8636054FD84898D201081D3C01793F8` at core 89405. Its seven copied artifacts match their original v87 run. The complete restored Core matches the prior restored Core after updating only the ROM CRC. The 15 original-to-resave byte deltas are retained separately. Five restored RAM/display-region dumps match byte for byte.
- Independent verifier `tools/verify_shoot_checkpoint_results_v88_capture.py` SHA-256 `DF8912BA917D79A6A253A8F7E51FA25A977549FA2D4955FA732AB7C3C2434FAF`. Its report, `build/shoot-checkpoint-results-v88-capture-independent-20261117/report.json`, has SHA-256 `7A3AFF15C317AC3C6DD1CE907FBA81518E86C8A02CBD7C5D4603433D69341603`.

## Actual combat and results route

The replay repeats the prior measured aim inputs and the first eight framebuffer and memory snapshots byte for byte. At core 89469 the sole authorized script write sets SECOND's HP at `0201188C` from 37 to 1. Read-back checks preserve the neighbors and FIRST's HP and score. The game processes the qualified ordinary B and records a one-point hit by FIRST `02011710` against SECOND `02011828` at core 89483. The resulting HP is zero. The terminal scene and native cleanup request at core 90919 match the earlier run.

| Core | Native event |
| --- | --- |
| 90920 | Physical mode word `03002310` changes 7 → 8 |
| 90942 | Stage 11 Results constructor at `080897B0` |
| 90943 | Physical mode changes 8 → 12 |
| 90944 | Mode 12 constructor |
| 92715 | Mode 12 issues its native `1,0,0` request with timer zero |
| 92716 | Physical mode changes 12 → 13 |
| 92717 | Mode 13 credits constructor |
| 97405 | Frame budget expires during mode 13 |

Held and edge input words are zero at the captured mode 12 constructor/request and mode 13 constructor/boundary. The mode 13 exit request and modes 11, 20, and 3 remain unobserved in this run.

## Credits at the boundary

The first and last mode 13 snapshots share four valid active native tasks, with callbacks `08015AB4`, `080CAFAC`, `080CAD44`, and `080CA7F0`. Over 4688 frames the credit next-page index at `0300428E` advances from 1 to 8, the selected text pointer from `080CF598` to `080CFB18`, and the controller word from `0800` to `0822`. The current overlay has 50 hold frames left at `03003DB2`. Native code at `080CB600` decrements this counter, then schedules the fade and the inter-overlay delay. The captured ARM PC `0000001C` and CPSR `60000092` place the frame on the BIOS IRQ path. The final state agrees with all five memory dumps.

The final framebuffer at `build/bizhawk-shoot-checkpoint-results-v88-20261117-a/13-bounded-no-terminal.png` visibly reads SPECIAL THANKS and shows DIMPS and HIROYUKI KAWANO. Native page loader `080CC764` advances the index and resolves 12-byte credit descriptors at `080CF4F0`. The visible descriptor range has fourteen valid rows, indices 0 through 13. Row 7 is currently displayed, with six later valid rows in that range. This proves substantial credits progression and supports retaining the existing 120000-frame budget for the full replay. The exact end-to-end credits duration remains unmeasured.
