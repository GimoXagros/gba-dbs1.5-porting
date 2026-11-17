# Final ending card accepts a distinct A press

The second E212 checkpoint replay exited with code 1 at its bounded stop on core 105405. It directly recorded the natural credits request at `080CA39C` on core 102010 with cursor 22, complete flags `003F`, and tuple `1,0,0`. The ending constructor ran at 102012 and the original name-entry observation ran at 102030.

Ending task `02010348` initially used callback `080BFEA4`, which contains the hooked name-entry input check `080C0050`. At the final capture the same active task uses callback `080C0F40`. Its payload points at the native predefined name table `080C1100`, index 5, string `KIMJOY`. Text display is complete, its flags are `0001`, and the fade counter is still `004B` (75). The last image is the final name card. The currently loaded callback no longer enters `080C0050`, and so the old observer's A timing gate stops refreshing. The capture records no per-frame ending button journal. The active task and its unarmed fade establish that it never consumed the card's required A edge before the bound.

The card's actual input gate checks flags bit 1 set and bit 2 clear, then samples native rising input `03001306 & 0040`. An ordinary A sets flag bit 2, captures the base fade palette, and counts down 75 ticks. The exit calls native `0808B728` with registers 8/9/10 set to `1,0,0`, which stores the transition words under `03002310`. The mode 11 table maps selector 0 to mode 20.

The read-only hook for the card's input epoch is `080C1018`, opcode `E59F50D0`. The consuming instruction accesses edge input at `080C101C`. A suitable request observation is `080C10CC`, opcode `EBFD43D7`, after the real native tuple stores. The input check can bind the current active `080C0F40` owner, the matching payload pointer in R1 and the exact waiting state before an ordinary press.

Exact installed ARM fixtures show a fresh A on completed text arms the fade. Neutral input, direction, B, incomplete text and a second A while fading leave it unchanged. The sampled countdown cases prove only zero issues the request. Palette operations and common finalization imports in this fixture are modeled. The native request writer itself executes.

Original WSC 1.5 contains the corresponding optional final card code at `77B19A`, with the rising A gate at `77B207..77B226` and request stores at `77B28F`, `77B294`, and `77B299`. Its active selector writes `FF` at `77B34D`, bypassing that card on the ordinary WSC 1.5 path. E212 retains the native card and needs its ordinary A input for this replay. The finding is limited to that retained native behavior.

Checker `tools/verify_mode11_ending_card.py` SHA-256 `44B647C652D5A2B3EFBD7C9EF02FC34FA459F869329D00B6238F1790FAE84375`. Report `build/mode11-ending-card-independent-20261117/report.json` SHA-256 `143E64414DEF6E37E30C1E87D3C66F1336D50189C2F8F09510F278CC000F22A3`. Actual mode 20 entry and title were beyond this capture.
