# Native render-only stop-isolation fixtures

Independent PASS_RENDER_ONLY for four r2 fixtures. Verifier `tools/verify_evolution_music_uninterrupted_fixtures.py` SHA256 `29A6A9E377127C318C6D384E4A5FA7DDFEF28D2AD820DC8DCA609104FE6F50D4`; report `build/evolution-music-uninterrupted-fixtures-qa-20261110/report.json` SHA256 `BCCE368043295E0E5420C32B7BF7044AD807086840B4327C53F34561F67E48B6`.

Each complete image differs from its frozen r1 fixture only at37B47C: C00900EB (BL0837DB84) becomes0000A0E1 (MOV R0,R0). The actual stop bridge targets Thumb0837C3B1. Entire-image inverse restores the r1 fixture, and reversing its prior song-row substitution restores exactDD6D component. All four bytes change in each fixture; no source fixture or production ROM is altered.

Thirty-two actual ARM boundary cases cover songs0/1/108/111 before and after for each fixture. Register results, stack and return agree at modeled imported-service boundaries. Only zero-song global-stop invocation disappears; nonzero play remains. The downstream synthesizer is not executed in this check.

This deliberately suppresses every global zero-song stop in these test images, not just the observed boot invocation. It must remain render-only and is not a production music layer. Other song requests can still interrupt playback. No completed audio, normal evolution activation or lifetime parity is claimed. No emulator was run.
