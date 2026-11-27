# Waterfall hides both fighters in v1.0.0

The v1.0.0 foreground map and sprite priorities correctly occlude the fighters **on the water-visible frame**. The prior [single-frame audit](waterfall-foreground-source-parity-20261117.md) checked that frame. It did not exercise the next interrupt.

In a non-visible BizHawk 2.11.1 run of the original Ver. 1.5 WSC, the Waterfall IRQ at 5EEA:0B4E read display port 0 as 1 before both writes. The output alternated between 5 and 7 as the retained halfword at 1000:0382 alternated between 0 and 2. The alternating layer reveals the fighters and rocks behind the water. In an identical stage setup on v1.0.0, the retained state alternated but DISPCNT stayed at 3F40. The GBA kept BG0 enabled across both interrupts.

The correction is confined to the Waterfall display helper at 08628380. The original conditional enable now has a matching conditional clear for the off phase. The existing scroll, palette, sprite priority and unrelated hardware bits are preserved.

## Private emulator comparison

Each run cold-booted, entered a solo match through ordinary controls and selected Waterfall by changing the stage selector from 8 to 9 during the VS screen before the normal initializer. This is a diagnostic stage setup. No foreground register, actor, IRQ or phase value was forced. The captures cover battle ticks 195–205 and 595–605. For example, at the horizontal center / y=32 in two successive frames:

| Image | Display behavior | RGB samples at ticks 600 and 601 |
| --- | --- | --- |
| Original WSC | Port 0 alternates 7 and 5 | (170,238,255) water; (85,34,0) rock |
| USA port v1.0.0 | DISPCNT 3F40 both phases | (74,156,255) water in both |
| Corrected isolated GBA | DISPCNT alternates 3E40 and 3F40 | (189,107,58) rock; (74,156,255) water |

The two captures are compared by foreground phase, since they start on different phase parities. Both fighters are visible in the corrected off-phase image at battle tick 200. The emulator event logs are local under `build/issue4-waterfall-{ws1,ga1,ga2}` with SHA-256 `18D06C106DF8BAAC2237446BB0CF6BA3FBFD2C80135FBB27C723C6AF1545BAC0`, `BC0EE9E0A6C647F0841F413DAA8C3230C54E66EA2B69C23E1385A57C04549E0E` and `429CD693FA685E36C6938B117D01B725B3BCC189845587887B6E1B130979CD58`.

Run `python tools/verify_issue4_waterfall.py <port.gba>` to exercise the installed ARM for four consecutive interrupts for each combination of seven incoming display configurations and two initial phases. v1.0.0 fails the stale-BG0 regression. The corrected IRQ passes all 56 transitions.

## Combined build and stage dimensions

Integrated test image `2EA3B19CD4A83E06B2E0BA050F12C71EDB8043BC258C054EA355C6CD8B5ED966` passed the same 56 checks. Executing the actual GBA stage setup at 0803EE70 through the 03004568 store produced the WSC width/height word at 77CCF0 for every stage 0–11.

In Waterfall, both the source game and integrated GBA initialized the stage to 224×432 pixels and cached its world limits as 3584×6912 at sixteen units per pixel. v1.0.0 initialized 672×288 and 10752×4608. We used ordinary movement inputs from battle tick 611 onwards. During the 2,600-tick GBA comparison both background layers scrolled together vertically with zero horizontal scroll. The integrated game and v1.0.0 had different vertical scroll positions from ticks 1306 to 2004 under the same input. The stage selector was the only diagnostic guest edit. This test checks the size producer and a moving camera; input and gameplay timing between WSC and GBA are not frame-identical.

The integrated GBA and v1.0.0 camera logs have SHA-256 `DBC5C021D5E271F57633666C34C0832BB081E484A16E013358CB7ED77EE72236` and `F420B57A3F27F2537460D0E384B0CB6A1E38A9234812F0B28C402766D22CFF40`. They read the two packed scroll words from the callback's actual 0300456C source.
