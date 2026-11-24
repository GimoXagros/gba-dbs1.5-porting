# Tamer Tag result audio and score reel

The WonderSwan ordinary card starts D4 at raw 7740DF and requests 104 on acquisition or 108 on loss at 774177 and 7741A0. The special card starts D4 at 77443E, then selects 100 on acquisition or 108 on loss at 7744DC and 774505. D4 is a one-channel effect at priority 1. The other requests use priority 4 and select four descriptors each. The fourth descriptor in each group immediately ends. In the final group, 10B is the last of 268 entries in the source table, with a four-byte zero header and the FFFF end command. The source score reel starts B6 at 775340 and clears its own audio lane with 06 at 7753C3.

| Source | Native row | Native player | Source duration in driver updates |
| --- | --- | --- | --- |
| D4, card slide | 7B | 4 | 40 |
| 104, ordinary gain | 7C | 0 | 235 |
| 108, loss | 7D | 0 | 281 |
| 100, special gain | 7E | 0 | 1330 intro, 4096 repeating |
| B6, score reel | 7F | 3 | 5 intro, 16 repeating |

The WSC speed accumulator and vibrato phase determine the native loop lengths. The converter reconstructs the original four-channel music group, applies each physical waveform, volume envelope, stereo ceiling and vibrato, and emits timed native note starts, releases and FINE or backward GOTO. The native clock and its finite bend precision still differ from a WonderSwan APU. For the six voice samples it reuses five exact native payloads and installs the original type-8 waveform as a separate sample. 

The original 123 native rows, including the four evolution tracks, are copied exactly to a 128-row table. All five M4A readers point to it. The prior table and existing song data remain in place. The installer only enables the presentation's award sound dispatch after checking its authenticated code, table readers and assigned rows. No mode-24 controller or menu difference is inferred from a standalone bank. Native source 14 uses retail 03 on player 0. The retained retail music has matching complete upper and middle note sequences and an octave difference on the final four bass notes. The original 06 makes the B6 hardware lane silent. Its native counterpart asks m4aSongNumStop(7F) on player 3 and compares the exact playing header before issuing MPlayStop. The presentation and link controllers own the timing of those requests.

On parent D71E0896, `tools/build_tag_result_audio.py` produces `9A8D51B08310376C093013D952FC7A02973134F3FE338C1718AF009B4B692B2D`. The typed ownership manifest `build/tag-result-audio-score-integrated-20261124/manifest.json` has SHA-256 `8B483AEFD27C4F87438B60155417A306E84602209C7035F0AC4EEC21D25B6DA3`. The builder takes `--source`, `--input`, `--owner`, both SHA-256 arguments and `--output`. The integrated run uses `--presentation-owner build/v92-end-to-end-serial-20261124/presentation/manifest.json`.

The independent `tools/verify_tag_result_audio.py` reads the installed M4A commands and original source control streams, verifies all 14 track descriptors, checks the quantized stereo envelopes and each held-note pitch, and inverts all production writes. It covers 1040 note starts, including measured full-period unrolling, with maximum error below 0.781 cents. `build/tag-result-audio-score-integrated-20261124/verified.json` has SHA-256 `45D857295D8B4939303FE6E1E4973DBC7EA5D85D329709CAC453336374E39508`.

`tools/run_tag_result_audio_renders.py` records five private BizHawk/mGBA stereo WAVs. Its isolated fixtures substitute one eight-byte boot song row to select each production header. All five players began at frame 539. The three finite cues released their players at 572, 726 and 762. Both looping cues continued through the recording. `build/tag-result-audio-native-render-20261124/report.json` has SHA-256 `0C999A04AB303725EA0D14C8F65A41CA2200F44A91C7466304C8A206FCB7B7A3`. Natural ending and cable dispatch require their own actual-scene observations.

A separate negative fixture kept retail sound 55 active on shared player 3. The native conditional stop for 7F compared its requested header against 55 on 502 updates and left the other sound playing. Across 287958 stereo frames the recordings had 99.315% identical samples and 0.997937 normalized correlation. The physical WAVs differ slightly between the instrumented paths. The report `build/tag-reel-stop-negative-20261124/report.json` has SHA-256 `299446891E213CED923C80A18EC3FC90431A88C5A302F93417118B8FAE471955`.
