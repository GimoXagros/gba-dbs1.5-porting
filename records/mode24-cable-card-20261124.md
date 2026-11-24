# Cable Battle Spirit Ver. 1.5 result and Master promotion

The USA results screen originally returned directly to character select after an exchange. The 1.5 path now waits for the native link command to finish, saves the outcome on each cartridge, shows the card each player gained or lost, and returns both players to character select. The Ver. 1.0 menu choice keeps its original transition.

## Source owners and presentation

* The two native command-82 entry points send and receive a single 16-byte descriptor. The completion hook records the eligible local card only after a successful EEPROM write. The mode dispatcher selects scene 24 using the existing version selection. An absent peer marker, invalid rank or failed write yields no card. In WSC the peer transfer is at raw `741E40/741EAD`; the source streak calculation at `77560B..77562A` increments a winner up to 999 and clears the tied or losing player's streak.
* WSC mode 24 and the solo ending share the far constructor at `73D3:00EE`. The source promotion call at raw `774215` installs the SPECIAL controller via `73D3:052E`. The port reuses the verified WSC card/layout/scene resources. The native register shadows for the display backdrop and BG offsets, IRQ handler, blend mode and brightness are saved before takeover and restored before the two tasks are released. Clearing the previous results-screen darkening allows the card colors to reach the framebuffer.
* Source `D4` opens a card. Standard gain uses `104`, loss uses `108` and Master gain uses `100`. The name screen restores its own graphics, scroll and palette and consumes the four native keyboard actions. Its initialization does not re-trigger the card-opening song.
* The two arena task payloads hold all 30 particles in two 150-byte blocks. The source start positions at `774CA8`, signed movement, offscreen respawn, animation tick and source particle graphics drive the celebration. The selected fighter uses its active costume and native animation records for the approach, jump, landing and change of orientation. Both actor and particles continue through name input. The native post-match save persists the confirmed three-character name.

## Offline builds and checks

| Content | SHA-256 |
| --- | --- |
| Score-audio input ROM | `39D0EEBF4793CAB110DCF51D6C5F29C076039EEC9D78F95BE16096AC5A32D979` |
| Native mode 24 ROM | `249FB4C337964F72005233FD8F68E1A1A19D74171AC35BEA8E4ED932A74B086B` |
| Master keyboard feedback ROM | `505DCE0601EA9ACCB7D27D9AE410132D27933E733580574F4B177541B05DA96D` |
| Master celebration ROM | `2922F5865C962A4AFA148DC80736ADBA96FDFE5786DAFB7F008845C7B529CFE7` |
| Celebration allocation manifest | `74AF7A5614AE9923EF81CC16B2657EE097046C81209766F2331DC2A755BB3F39` |

The installed mode-24 check covered 120 accepted exchanges, 12 transitions, 28 device errors, legacy and missing-marker routes, and all 24 earlier dispatch rows. The keyboard gate exercised 60 action, result and register-state combinations. The portable particle check matched 4,800 positions and 2,444 emitted sprite entries, including offscreen respawns and preservation of the 3,040 bytes used by the separate solo particle system.

## Windowless play

Two mGBA cores ran on a private desktop. The test copied native 512-byte GBA EEPROMs into separate fixtures and initialized the requested rank and previous streak before boot. Both games played to the result through ordinary menu and arena inputs. The recording script read guest memory, graphics and audio requests. The supplied WonderSwan save was not used.

| Play | Observed result | Report SHA-256 |
| --- | --- | --- |
| Standard tag on `249F` | Both players showed the exact 1,510 WSC emblem pixels. The gain overlay matched 1,580 pixels and loss matched 897. Both returned after 400 frames. | `FFB598D507B3B218F49588F7B90F580AA5C035C88C9124D9BDB0D5E887A49C30` |
| Master feedback on `505D` | The winner converted nine champion tags and a genuine won tag into one Master. The display matched 3,268 Master emblem pixels. Three letter selections and confirmation saved AAA. The loser retained eight champion tags. | `968D3B459AA7322BD582531F674DFBC5590A15AE83C87D7293939C8805845B98` |
| Master celebration on `2922` | Player two won using Guilmon's alternate costume. The ground and jump frames matched 14 and 16 fighter tiles against the native fighter bank. Both had 16 visible source particles. All 773 and 848 tested display pixels agreed, including border occlusion. Name input opened after 151 celebration ticks. Both machines returned to character select. | `C3204FB0542DE8A118B326F8D57EE83829E9DDF91C1A10089199E3B9F1D256B7` |
| Cold boot on `2922` | A separate player-one win produced Master rank, eight consecutive wins and AAA. Rebooting a copy of that physical EEPROM matched 1,941 title pixels, all 37 title objects, the three name tiles and 186 name pixels in Collection, and the full 4,096-byte viewer map. The copy remained byte-identical. | `1FDA3EDE704B2B0D025AFC2DE439F08B3A5AE3E7DB7CEACB7B4ED3CAAFF7C2EF` |

The relevant commands are `tools/run_link_tag_capture.py --card-screens --carry-to-special`, `tools/verify_mode24_celebration_capture.py`, `tools/verify_link_reward_cold.py` and `tools/verify_mode24_special_particles.py`. Each command accepts its actual source/ROM paths and writes evidence into a fresh local directory. ROMs, saves, executable hosts and captured frames remain local.
