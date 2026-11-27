# Opening display correction

The v1.0.0 patch displayed unrelated map tiles behind the fighters in the opening. In two cold BizHawk 2.11.1 GBA sessions, we compared the port and the original USA cartridge eight frames into callback 2. Their VRAM differed in only one 2 KiB screen block, at `0600F000`. Of those bytes, 1,271 differed. The port's block began with tiles copied from an added stage map at `0859D4B0`.

The expanded gameplay map table copied native rows 0–20 and assigned new stage data above them. An earlier whole-ROM pointer substitution also redirected ten opening callers that selected native rows 22–31, and the opening's row-32 initialization wrapper. The original rows are still present. The correction binds these eleven callers to the original table. Row 32 is passed by the sole native caller `0808341C` of `080146B0`. Both the bound instruction and original descriptor range are checked before any write.

Four inserted scene transitions also left the screen white. Their WonderSwan handlers set the next fade duration to 5, 30, 30 and 5 source frames, reset elapsed time and reverse the fade. The GBA adapters now restart the existing native fade for 4, 24, 24 and 4 GBA frames. Once the actors became visible, the first added fighter had the wrong form and subsequent actors were drawn offscreen. All five WonderSwan actor calls explicitly pass the table displacement `03C0`. The port now selects its converted row-30 view. The native actor constructor uses r5 for its resource row, so retaining the input X in r5 across the call placed the actor at X=`55C0`. The adapter now saves X, Y and the initial event on the stack across that call.

## Regression check

The opening-only image `8D3F734AC2E23EC4D195E63A45D238C9B663D45082665020E6B4AC5C0CAB5DCD` passed a cold no-input boot to the title on frame 2,886. In another cold run, Start on frame 1,690 reached the title at 1,770. Both preserved the native timing measured before this correction. There were no save loads or guest memory writes.

In all fifteen shared linear callbacks the entire first sampled 240×160 frame matched the USA original. For the four added callbacks, the primary fighter silhouettes sampled against WonderSwan 1.5 at callback age eight had 1,462, 1,539, 1,260 and 1,452 source pixels. Differences were 0, 0, 0 and 1 respectively. A direct check of retail and corrected callbacks 0 and 2 also found all 98,304 VRAM bytes equal. On the released v1.0.0 the same frame comparison fails beginning at callback 0.

Use `tools/run_opening_playback.py` with the exact GBA hash, a fresh output directory and `--limit 3030` to collect the no-input frames. Pass the USA, WonderSwan and candidate capture directories and the candidate hash to `tools/verify_issue4_opening.py`. The verifier reads the actual loaded ROM and checks the frames. Its four silhouette checks cover the primary actors at the sampled times. They do not compare the entire animated background or every frame to the WonderSwan.
