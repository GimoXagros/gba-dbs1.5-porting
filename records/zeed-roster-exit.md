# ZeedMillenniummon defeat and the player roster

In v1.0.2, the stage 11 exit display tests the real player ID against zero at `086FFAC0..086FFAC8`. It then tests two presentation pointers against Guilmon’s fixed addresses at `086FFB64..086FFB80`. A stationary Gabumon (ID 9) has different resources and cannot pass either condition. The original WonderSwan display at file offsets `75FADA..75FBFC` operates on display/IRQ state, without an ID-zero selection there. The earlier original capture and its limits are recorded in [the terminal observer report](shoot-actual-terminal-di-owner-20261109.md).

The GBA loader at `08353304` resolves the selected normal player’s 32-byte row in `084A80F8`. Its first two pointers reach actor offsets F4 and F0 through `080127E4`. The corrected exit accepts the fifteen normal player IDs and matches **both** of these pointers to the selected row. It still requires a stationary, idle player, the linked boss and auxiliary tasks, the proper draw queue, hardware state, and map/tile conditions. The existing caller restores its saved registers after the guard.

The only ROM changes in this layer are offsets `6FFAC4..6FFACC`, `6FFB64..6FFB94`, and `6FFDA4..6FFDA8` (exclusive ends). `python tools/verify_zeed_roster_exit.py <candidate.gba>` executes the emitted machine code. All fifteen legitimate player rows pass. All 331 bad-owner/invalid-ID cases reject. This is a guard-level test. A separate real-game checkpoint replay checks that the battle actually ends.

## Gabumon campaign and matched replay

A private-desktop run of the published `F32BEFB1…EFE0090` ROM started from title with an earned all-roster save, selected Gabumon on difficulty 2, and played the ten ordinary stages. The approved test assists fixed D-Spirit at 999 and set a live boss to 1 HP once per fight. After an initial loss at the first boss, a controller retry from its game-earned entry defeated it at frame 87507; stage 11 opened at 88165 and Gabumon landed the final hit at 91144. Both replays used the same checkpoint at frame 91145 (SHA-256 `6EA323B679F497F21C0B0A6F9C7A5FC71AC6E66992A1E51138ADFE0E7CDF0C80`). No guest writes or battle inputs were issued after restore. Ordinary confirm inputs were issued after results.

| Event | v1.0.2 | Corrected exit layer |
|---|---:|---:|
| First guard check with Gabumon resources 081FEE44 / 081FC568 | 92128 | 92128 |
| Guard rejects ID 9 | 2,017 times in the observation window | 0 |
| Native battle result | Still in battle at 94145 | 92639 |
| Native ending entry | — | 94920 |
| Return to title | — | 96148 |

The corrected layer in this comparison was `084750406ACAB6AD1071FECA1778F2789C4233CF906E688F5AFF6810BE8955DE`. The read-only replay is [bizhawk_zeed_ending_replay.lua](../tools/bizhawk_zeed_ending_replay.lua). Local evidence is in `build/zeed-gabumon-cold-a`, `build/zeed-gabumon-cold-retry-a`, `build/zeed-gabumon-baseline`, and `build/zeed-gabumon-beta`.

## First boss HP for the expanded roster

The USA stage 7 constructor loads a single byte from `08370044 + playerID`. There are only 12 entries. The next word is pointer `03004D42`, so its first three bytes became base HP for IDs 12, 13 and 14. The original WonderSwan stage 7 constructor at file offsets `7455DD..74562D` uses fifteen halfwords at `7457F8`. Its fifteen entries are identical to the already resident stage 11 table at GBA `085C1400`. Original difficulty 3 adds two truncated quarters of base HP.

The repair uses the commercial stage 7 constructor and its own real actor, HP and phase thresholds. It retargets the retired lookup to the resident table and reproduces the original difficulty adjustment in place. In v1.0.2 the only aligned ARM immediate reference to the retired table is the constructor at `0836FD20`. No absolute pointer or ARM PC-relative word load refers into the original 12-byte row. The first use of condition flags after setup is preceded by `TST` at `085B3608`.

| Player ID, difficulty 2 | v1.0.2 HP | Source / corrected HP |
|---|---:|---:|
| 12 | 82 | 37 |
| 13 | 96 | 25 |
| 14 (Gatomon) | 0 | 37 |

In v1.0.2, a native write trace for Gatomon saw actor creation and initialization in frame 3881. The stage 7 HP write left zero before play began. A Gabumon control saw 37. The comparative CPU test [verify_zeed_boss_hp.py](../tools/verify_zeed_boss_hp.py) runs the extracted WSC code and the candidate ARM code with Unicorn 2.1.4, then reads back actual HP and both phase thresholds. The ROM with both boss fixes (`673507D2484CA9A8670B3250B8433905377E0598112AB023FDA93951AB196BAD`) matches the source on all 3,840 inputs, including every one of the 60 valid fighter/difficulty combinations. v1.0.2 differed on 24 of those 60. Run `python tools/verify_zeed_boss_hp.py <candidate.gba> <original.wsc>` with Unicorn installed.

## Integrated build

The earlier integrated candidate `59A50F9039B215DEFB29E2A01D675D5B48C4A304E04B6B394DB9D6B5FB8C9B79` passed the same 3,840 HP/threshold comparisons and the 15 valid / 331 invalid terminal ownership cases. The same game-earned Gabumon checkpoint produced identical event logs and six byte-identical screenshots to the corrected exit layer, including the result, victory podium and return to title. Local run: `build/zeed-gabumon-integrated-59`. The actual visual comparison is `frame-2999.png` from the baseline and integrated runs; `result.png` is the earlier transition frame.

## What changes with the winner

The winner’s podium is personalized within the shared ending sequence. WonderSwan `76DA37..76DA96` reads the winning player’s selected fighter and palette from the character slot, indexes the fighter’s 32-byte art row and selects victory animation 36 hex. The GBA counterpart at `080BB314..080BB3CC` selects the corresponding 32-byte row at `084A80F8`, passes the character graphics and palette to the renderer and selects the same animation. Some roster slots share art and use a different palette, notably the Agumon variants. The credits use the common mode 13 sequence. Name entry and eligible unlocks run after it; unlock slots and their conditions are documented in [the ending award record](mode11-source-roster-awards-20261124.md). These stages do not establish fifteen separate scripted stories.

## Gatomon’s clear mark on restart

The original Ver. 1.5 winning routine `7784AA..7784B2` sets bit 14 for a Gatomon clear. Its next two saves at `7784BC` and `7784C8` run selectors 1 and 2. Before each selector, source `785FF3` masks record offset 10 hex to `3FFF`. Selector 1 recopies the live clear mask at `78611C..786120`. Selector 2 saves other flags and retains the masked clear field. With a previous Guilmon clear, the original first writes `4001`, then writes `0001`. The GBA serializer copies the live field before sanitizing, so both writes already contain `0001`. The Gatomon bit is visible during that play session; the final stored clear mask agrees with the original after restart.

[The save comparison](../tools/verify_zeed_clear_marks.py) executes the original WSC winning routine, verification, sorter, and record copies, then the two GBA serializer/writer calls with an eight-byte device fixture. The final records match for all 15 fighters. On final `8ABA49B14FFB4A1BABD3B99CD438846EA1D0CE7C0680F52D0B6F1A328A7CD508` the independent CPU checks also matched all 3,840 HP/threshold cases and all 15 accepted / 331 rejected exit-guard cases.

## All fifteen podiums and endings on the release candidate

The final `8ABA49B1…8A7CD508` ROM was loaded and independently dumped inside each private emulator. All fifteen default-palette fighter slots resumed from checkpoints produced one frame after an actual lethal stage 11 hit. Gabumon’s checkpoint came from the full campaign described above. The other fourteen used native character selection and replayed the earned final-round index to play the two boss encounters. No battle inputs or guest writes were issued after the lethal-hit checkpoint. Each run entered the native result, selected its own podium row and palette, entered credits and name/ending, then returned to title. The battle result appeared 1,412–1,554 frames after the respective checkpoints.

[All fifteen winners on the podium](../docs/screenshots/zeed-winners.png) shows unscaled 240×160 emulator frames, captured exactly 400 frames after podium entry. The fifteen centers were visually reviewed. In particular, Gatomon is clearly visible standing on first place at this point; later the scene changes the viewpoint. The gallery SHA-256 is `E235729137427280AF812834A5085827314E3F68230E9157584F84220C0AE29B`. Per-fighter verification, the selected 32-byte resource rows and screenshot hashes are in the local `build/zeed-podium-final-report.json`, with native trace logs in `build/zeed-podium-final-00` through `-14` and gallery samples in `build/zeed-podium-standing-00` through `-14`.
