# WonderSwan D-Project cable reference

Battle Spirit Ver. 1.5 uses the D-ARK menu for D-Project battles. D-Project uses the second item in its communication menu, `VS SWAN (CABLE)`. Select a registered Digimon, confirm OK, then press A on D-Project to start transmitting. The cartridge pair and the resulting battle can be observed without either a physical D-ARK or prerecorded packets.

## Native core and setup

The test frontend loads a separate native core instance, working RAM and cartridge save for each game. It advances each WS CPU by one scanline and transfers only bytes emitted by the other machine's UART. Each game handles its own receive interrupts, protocol validation, attacks and adjudication.

Build sources are [Beetle WonderSwan at 4b01295](https://github.com/libretro/beetle-wswan-libretro/tree/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd) and the [dual-core UART patches at db00c5f](https://github.com/Squirbie/handheld-link-cores/tree/db00c5fd2c863563da4ae84c4fe2d78364f7e3dc/cores/wswan-mednafen-dual/patches). Build with Python, a Git checkout of both revisions and the Visual Studio x64 C compiler.

```powershell
python tools/build_wsc_dark_uart.py <beetle-checkout> <uart-patch-checkout> <core-output>
python tools/prepare_dproject_link_save.py <core-output>/ws_uart.dll <d-project.wsc> <peer-output>
python tools/wsc_dark_setup.py <core-output>/ws_uart.dll <battle-spirit.wsc> <waiting-output> --fighter 1
python tools/verify_wsc_dark_pair.py <core-output>/ws_uart.dll <battle-spirit.wsc> <d-project.wsc> <peer-output>/ready.State <report-output> --battle-state <waiting-output>/ready.state --peer-input 5:A:2
```

## Headless two-cartridge results

The reference ROM SHA-256 is `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`. D-Project files are the two user-supplied 4 MiB dumps. Separate saves on each edition started with a Botamon hatched through gameplay. On private QA copies only, the registration PC was enabled with story flag 1. The game saved the two copies of that single bit and its own checksum bytes. An operator then used the game's PC menu to register Botamon and cold-booted the resulting cartridge save. The Japanese run also needed normal pet care to clear Botamon's droppings before registration.

Both runs selected Terriermon on Battle Spirit. With both machines at their game-native waiting screens, D-Project received an A press on relative frame 5. Each cartridge sent eight bytes and received eight bytes. Both cores reported zero overruns and zero dropped bytes.

| D-Project | D-Project → Battle Spirit (hex) | Battle Spirit → D-Project (hex) | Battle Spirit | D-Project |
|---|---|---|---|---|
| Japanese | `8F 02 5F 23 4F 08 0F A0` | `BF C3 8F 05 BF 09 0F 50` | Initial HP 5–3, won 5 to −1 on frame 976, returned to title on 1405 | Displayed LOSE on frame 940. A returned to NETWORK BATTLE |
| Korean 1.1 | `0F 02 5F 23 6F 08 0F 00` | `BF C3 8F 05 9F 09 0F 70` | Initial HP 5–3, won 3 to −1 on frame 1636, returned to title on 2065 | Displayed LOSE on frame 1604. A returned to NETWORK BATTLE |

D-Project SHA-256 values are `A88C0E50C75547FE79F98D56A793B95D6B9D52E44D4C21448C0C6DBD1BBF0A8C` for Japanese and `1732F1DDD8A5017FE2B4D861054C972AFEAE08478483189C76A7C53CA5A43FD1` for Korean. Extra runs using four other starting fighters (IDs 0, 2, 3, 4) also completed against Korean Botamon. Across these genuine matches the Battle Spirit profile word at `F990` was zero from waiting to return.

In the disconnected control, the native Battle Spirit waiting screen and the Japanese D-Project field map were linked for 180 frames. Both recorded zero bytes in either direction and Battle Spirit remained in mode 18. The opposite win/loss direction was not demonstrated live with this starter. Local traces, screenshots and result reports from the two principal runs are in `build/wsc-dark-pair/{jp-1,kr-1}`.

## Serial timing

In the Korean run, D-Project transmitted each request at scanlines 38 and 51 (frames 6, 9, 12 and 15). Its RX vector remained `2000:6C84` while transmitting. At scanlines 23–24 of the following 159-line frame, D-Project switched to `2000:6CE2`, read port B1 to discard a pending byte (`2000:6C2F`) and enabled its receive IRQ. A response arriving less than about 132 lines after the second request byte would reach the receiver before this reset. The original Battle Spirit returned the two bytes at scanlines 49–50 and 75–76 two frames later, about 316 and 342 lines after the request. Both message order and turnaround time matter.

## Observation points

| Machine | Observation |
|---|---|
| Battle Spirit | SRAM `004E=18` is D-ARK. The waiting actor in segment `7B62` checks the driver's ready flag at `0618`, copies both negotiated health values and enters callback `07BB`. At `0A91` a signed local HP value of zero or lower takes the loss branch. At `0ADB` depleted opponent HP selects the win branch. Both routes eventually return to the game menu. |
| D-Project | RAM `1F44=6F21` is the cable wait callback. A starts transmission. `1F44=7078` is reached after the exchange. The game copies local/peer health to `1EF4–1EF5`. The battle routine `C000:D0AD` checks local HP first, then peer HP at `D0CF`. The result coroutine waits at `C000:D2D4` for A to return to the communication menu. |
| Registration | The house event at `6000:00D5` skips the registration PC object when persistent flag 1 is clear. The object's definition at `6000:00DA` points to script `6000:0596` and opens `8000:0000`. In a QA save copy, RAM `239F` bit 1 enables this PC. Its menu transfers a game-earned field Digimon (records starting at `1FCC`) into the communication roster at `20E0`. The cable selector tests the actual species in the roster. An empty slot has value `FF`. |

The Korean starter also evolved into Greymon through in-game training and roaming. After menu registration and a cartridge restart, native WSC Battle Spirit lost and D-Project displayed WIN. The same registered save also produced a GBA loss against Greymon. Use the save preparation tool’s `--greymon` option to reproduce this opponent. [Results](fixtures/d-ark-direct-link-results.json)
