# Four original-score render pairs

PASS for capture provenance and complete native PCM duration. Verifier `tools/verify_bgm_all_four_captures.py` SHA256 `53D8C042BD31EC6CB58ACD1CD4691963EEEF1E14E1BAAFD1D9227024DEDAC65C`; report `build/bgm-all-four-capture-qa-20261110/report.json` SHA256 `E9864FFB4D4B48595C2E0BE8699A31C6962152649D082FB527F89114BE8D0E06`.

All eight completed captures have exact inventories, frozen host/observer/fixture-gate bindings and copied-ROM hashes. All source groups initialize their four expected descriptor offsets and hardware channels, including F8's reordered channels. All native captures show the expected01 request and consumption. Saved configuration retains physical audio off and save/input isolation. WAVs are stereo44100Hz PCM16, with4400-frame durations appropriate to each platform. Every capture has zero clipped samples.

| Source group | Source driver updates | Native end minus predicted | Same-frequency spectral cosine | Half/double alternatives |
|---|---:|---:|---:|---:|
|38|3309|−1.134ms|0.9122|0.1641 /0.1849|
|3C|2753|−2.035ms|0.9220|0.2029 /0.1848|
|40|2972|−0.253ms|0.9526|0.2115 /0.2063|
|F8|2089|+1.516ms|0.9345|0.1725 /0.1944|

Spectral comparisons use aligned8192-sample stereo power windows, independent gain normalization and100..5000Hz frequency bins. They support broad pitch correspondence and provide no evidence of a wholesale octave error. They are not listening tests or exact note/envelope/stereo/timbre parity proofs.

Source final PCM exceeds the simple outer-frame prediction by0.2094/0.1886/0.2519/0.1712seconds. Schedules are expressed in actual driver updates. The separate38 diagnostic proves exactly3309 updates across3320 frames, explaining eleven missed passes; other groups have no equivalent per-pass diagnostic and their end differences remain qualified. No tempo retune follows.

Native rendering uses test-only global-stop suppression. Reaching expected PCM duration does not directly trace player FINE state or establish ordinary evolution activation/lifetime. Titles and full audible parity remain unverified. No emulator, capture modification, production-ROM change or physical listening was performed by this auditor.
