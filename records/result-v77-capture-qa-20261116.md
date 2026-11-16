# Independent v77 ordinary Korean result and music lifetime

The completed private BizHawk run `build/bizhawk-result-v77-20261110-a` passed the independent Korean result audit. BizHawk loaded the exact 16 MiB C344 ROM. The approved arguments selected language 2. The final launch and file hashes verified all 64 manifest entries plus `launch.json`. The v76 baseline had 62 entries plus its launch. The v77 additions were `music-lifetime.txt` and an empty hidden config temp file included in the final launch manifest. The audit checked both inventories again at exit.

All eight PNGs and all complete EWRAM, VRAM, palette, OAM and display-register dumps matched v76 byte for byte. The full 128-line trace matched byte for byte. Each snapshot landed on the same core frame. The audit verified one Korean EEPROM writer entry, seven result initializers, 88 draw calls and 30 WIN label parts with 1,508 matching pixels.

| Snapshot | Core frame | Changed IWRAM bytes |
|---|---:|---:|
| Options staged | 3458 | 3 |
| Options committed | 3559 | 3 |
| Title committed | 3560 | 3 |
| Battle entered | 3999 | 3 |
| Result entered | 11519 | 122 |
| Result plus 120 | 11639 | 122 |
| Result first label | 11776 | 108 |
| Result plus 300 | 11819 | 108 |

The comparison retains each of the 472 differing IWRAM bytes across snapshots, their exact contiguous ranges, every affected word, and both file hashes. The word at `03000D0C` changes from `5A000001` to `5A280AD8` in every snapshot. The four result snapshots also contain player-zero track differences in `03004EA0..03005030` and mixer channel differences in `03005A50..03005B50`. The latter include pointers into v77 sample storage such as `08D33398`, `08D33468` and `08D33400`. At `03007E08`, `00000005` becomes `0801140C`. At `03007E0C`, `00000001` becomes `0801140C`. Both are in the stack address range. These snapshots did not record SP or trace the two writes. The comparison found no corresponding old-to-relocated song-table row pointers in the changed words.

Boot code at `0800022C..08000240` sets up the 0x70-word DMA3 copy sourced by `080003B0` and stores all 448 ROM bytes from `0837B33C..0837B4FC` at `03000BF0..03000DB0`, with exclusive upper bounds. The whole copy in every IWRAM dump matches its own ROM. The copy includes the changed relative branch. If executed from IWRAM, it would branch to `03A03874`. The full ROM scan found four direct ARM callers for the active ROM adapter `0837B44C` and zero aligned literals into the copied adapter or its IWRAM mirrors. Full result-enter IWRAM scanning found zero raw pointer hits into that range and one internal ARM branch `03000D04→03000D2C`. The two external ARM branches entering the larger copy target `03000CCC`, a standalone `BX LR`. The JSON retains the unaligned ROM matches. This is bounded direct-branch and literal evidence. The ordinary run observed actual ROM adapter execution and had no IWRAM execution watches.

The read-only music file closed at core 11819 with all 43 observed event rows emitted. Actor identity 1 matched the selector argument at 9075 and the ROM mapping selected `6E`. The consumer took the queued request at 9076, updated `03004E98` to `6E` and put header `08D75728` in player zero. At 10364, the de-evolution return site had the same header and cached ID with stage music eligible. At 10365, stage request `10` set cache `10` and started `08384BF8` on player zero. There were no intervening tracked player-zero starts. The 1,289-frame interval measures the two starts in this run. It does not establish a universal form duration.

| Artifact | SHA-256 |
|---|---|
| `tools/verify_result_v77_capture.py` | `8F1271729314FBEBF54CE739DE35A2498F76A16BCE1E3E579A621C4B7B9930F2` |
| `build/result-v77-runtime-qa-20261116/final/ko-audit.json` | `19A5D7B9E92E174AD09B65158DE8413127CC627005AA377A8C9F30B4887671D1` |
| `build/result-v77-runtime-qa-20261116/final/v76-comparison.json` | `DBD0CC1A55BBD914E9154D9A6AD399BE8A2340F9ACE3CFD1131B2D0040E7D11C` |
| `build/bizhawk-result-v77-20261110-a/launch.json` | `7DFB96EF420692625422E82B96FCF6F63A0816A0EA22A3C3151F9B688087089B` |
| `build/bizhawk-result-v77-20261110-a/music-lifetime.txt` | `2B7FE19431AE73E0E0DBC5F9F12D8C4B19BC575D506E103751F1A03CA72D750F` |

The first verifier invocation needed Pillow and exited before reading any capture. The bundled runtime supplied it. The initial comparison is retained one level above `final` and marked `REVIEW` because its first classifier covered only potential relocated song-table words. The final comparison identifies the copied branch and audio state, retains both untraced stack words, and repeats the complete independent audit on the same frozen captures.

This ordinary run observed zero pause and resume entries and header comparisons. It had sound disabled and saved audio method 3. Coverage here is Korean Options through WIN, with one naturally selected `6E` evolution and stage return. The other three evolution starts, audible playback, fresh-process persistence and full-game coverage remain outside this run. The auditor read neither supplied saves nor the isolated SaveRAM tree and ran no emulator.

