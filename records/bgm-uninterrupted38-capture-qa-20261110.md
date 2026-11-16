# Native38 render-only full-duration check

PASS_RENDER_DURATION. Report `build/bgm-uninterrupted38-capture-qa-20261110/report.json` SHA256 `F86D6ADBD1BDBA36DF429C46FCF6BA557088A419C53981B82EE8B59135DF10FC`.

New host546B4A1F differs from reviewed AD087 only by GBA-only selection, r2CE2D/BCCE fixture bindings, category lookup for the new schema, unique output, explicit render-only scope and final newline. Private desktop,120-second bound, physical audio off, no input and read-only4400-frame observation controls remain intact.

Actual completed GBA38r2 capture has exact inventory and pins, stereo44100Hz PCM16,3248115 frames, zero clipped samples and peak30014. Last nonzero sample ends52.694331seconds, versus predicted3309-update schedule end52.695465seconds (−1.134milliseconds). Request trace equals stopped r1 exactly. PCM first differs at48.257596seconds near the prior stop; the earlier audio prefix is exact.

This establishes removal of the test fixture's stop truncation and PCM reaching expected duration. Native player FINE state was not directly traced. Global-stop suppression remains strictly render-only and establishes neither ordinary evolution lifetime nor audible parity. No emulator or physical listening was performed by this audit.
