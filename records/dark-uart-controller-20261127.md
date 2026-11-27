# D-ARK guest controller and two-cartridge checks

The GBA port listens on its native 9600 baud UART. D-Project initiates the battle from its cable menu. The games exchange four little-endian words in each direction. Each game then plays out the agreed attacks on its own screen. The protocol carries combat parameters and five turn decisions. Neither cartridge transmits a portrait or the name of its Digimon.

## Source and ownership

- Battle Spirit WSC `4FFF:1504–1832` reads and writes actual serial data. The reply task runs one scheduler tick after the second incoming byte. Each transmitted byte follows a 26-scanline WSC delay. The GBA receives through SIODATA8, keeps the extra scheduler tick, and spaces its output by 30 GBA scanlines. The cable forwards bytes from the cartridges.
- The retail GBA multiplayer status routine at `0837B1A8` used a word load from SIOCNT. This also read and consumed the first byte in the adjacent UART receive FIFO. Only the low control halfword contributes to the multiplayer routine's output. The patch changes this single instruction to a halfword load. D-ARK restores the previous SIO configuration when the scene exits.
- D-Project installs its receive interrupt and explicitly reads the old data register at `2000:6C02–6C3C`. A response sent during its transmit-to-receive transition can be discarded even with zero wire overruns. A real WSC trace places that register read about 132 scanlines after the second outgoing request byte.
- Battle Spirit WSC `7B62:039D/052F` reads a profile modifier at physical `F990`. It was zero on cold boots of five selected fighters, throughout a reported winning match, and at D-ARK entry with the independently loaded prior WSC save copy. The implemented normal profile is `58`, with the common source stats giving 5 HP and 1 base damage. The WSC also contains a branch for a modifier of five or more. Its gameplay trigger and evolved profile have not been demonstrated.
- D-Project's type-3 validator at `2000:7BEA`, normal transmitter, combat stat table and battle HP adjudication are byte-identical across the supplied Japanese and Korean ROMs. At `7CB6` the original checks an unmasked increment. A computed checksum nibble of zero is compared with 16. The GBA transmits the original four byte pairs and rearms for a retry so both games agree on the rejection.

## Recorded outcomes

Final GBA SHA-256 `FA46FC35A84559C89CFE0D9BD3DF0E5C6657C00A7287C878A69470812EE5B9B5`. Terriermon selected, 5 initial HP on Battle Spirit and 3 on D-Project. Both GBA pairings exchanged eight bytes each way, recorded zero overruns, returned from their result screens, and produced the same HP totals from each cartridge's perspective.

| Cartridges | D-Project output bytes | Battle Spirit output bytes | HP after each round, Battle Spirit / D-Project |
| --- | --- | --- | --- |
| WSC original + D-Project Korean | `0F 02 5F 23 6F 08 0F 00` | `BF C3 8F 05 9F 09 0F 70` | 5/1, 4/1, 3/1, 3/−1 |
| GBA port + D-Project Japanese | `8F 02 5F 23 AF 08 0F 40` | `8F C2 8F 05 5F 09 0F F0` | 5/2, 4/2, 4/1, 2/1, 2/0 |
| GBA port + D-Project Korean | `0F 02 5F 23 CF 08 0F A0` | `8F C2 8F 05 3F 09 0F 10` | 5/2, 5/1, 4/1, 3/1, 3/0 |

`tools/dark_battle_verify.py` runs the unmodified D-Project x86 validator and the installed GBA ARM completion/retry gate in isolated CPU function tests. All 512 combinations of the source strong-attack table and turn mask agreed, with 480 accepted and 32 rejected. The same gate accepted a valid retry after resetting the previous exchange. The CPU tests run separately from the two-game cable. With `--trace-json` the verifier also decodes an actual paired run and checks the result, every reported HP change, byte totals, wire overruns and both returns. The runner accepts private WSC/JP/KR inputs and the built GBA ROM, and uses Unicorn 2.1.4.

In the matched combat captures the active field is the source green grid with the selected Digimon. The opponent's projectiles enter from the right. The GBA retains its 8-pixel ornamental frame. In the 224×144 field, 14,424 sampled pixels in three static regions agreed on lit/unlit geometry. Core RGB palettes differ. The source shows the selected Digimon’s win pose before returning to the title.


## Windows player and build

The packaged Windows player cold-booted each D-Project cartridge with its own registered Botamon save and completed two independent battles through both results and returns. The GBA and WonderSwan keep separate save files keyed by cartridge SHA-256. SDL2 mixes their native stereo samples at 44.1 kHz. [Recorded results and cable bytes](fixtures/d-ark-direct-link-results.json)

Build mGBA with `tools/build_dark_link_mgba.py`. Build the WonderSwan core with `tools/build_wsc_dark_uart.py` using the upstream revisions in the reference record. Place `mgba_libretro.dll`, `ws_uart.dll` and the x64 SDL2 runtime in the same directory. Run `python tools/play_dark_link.py --cores DIRECTORY` with Python and Pillow, then choose both cartridges. [WonderSwan reference and source versions](d-ark-wsc-peer.md) · [Korean player guide](d-ark-direct-play-ko.md)

Two builds on independently reproduced v1.0.3 parents produced identical ROMs and allocation manifests. Applying the BPS to a clean USA cartridge reproduced all 16,777,216 bytes. As a regression check, the final development ROM also completed two matches and returned to selection when paired with the original USA GBA cartridge.

A naturally evolved Greymon registered in the Korean D-Project cartridge also defeated Terriermon. In a cold-booted GBA test, the two games agreed on every turn, ending at Battle Spirit 0 HP and D-Project 5 HP. Both games presented the opposite result from the Botamon captures and returned to their menus. This run used one extra GBA waiting frame and pressed D-Project A on relative frames 1–3. The original WSC Battle Spirit also lost to Greymon in a separate two-core run.
