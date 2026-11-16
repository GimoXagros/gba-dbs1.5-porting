# Independent audio render fixture QA

PASS for the eight frozen isolated fixtures. No emulator was run, and no production ROM, existing fixture, host, or Git state was changed.

Verifier: `tools/verify_evolution_music_render_fixtures.py`, SHA256 `BBEE445E04EEAF4EF9C42C429A63DCDAA503239F4F2DBF86A9D1111E20C4A3C2`.
Report: `build/evolution-music-render-fixtures-qa-20261110/report.json`, SHA256 `FB77CBEDAB114B4EEB32A1A930250653D130ECC69A7D9DE30073C1A10FF92B5C`.

The verifier independently reconstructs all eight complete images from frozen original WSC C415 and isolated native audio DD6D. It imports no author fixture helpers. The frozen generator DAB6 and manifest FC88 are pinned. Every before/after span, output hash, changed count and whole-image inverse agrees.

For source groups 38/3C/40/F8, only DC..DF's 24 descriptor bytes at 3F0528 and the final two-byte checksum are substituted. All four hardware voices are present, including F8's reordered channels. Entire-image checksums match. Changed counts are 10, 10, 10, 12.

For native fixtures, only the eight-byte relocated song01 row at D33008 is copied from the corresponding appended 6C..6F row. Each selects player0 with secondary field0, a four-track header, the source PCM voice bank, and bounded track entries. Each changes three bytes. Header, stream, engine and all other image bytes remain identical to independently audited r1.

The frozen source discovery log 47B26B2B binds request DC at frame520 to initialized original descriptor offsets/hardware channels at frame521. Frozen native log 7A08C045 binds song01 request at534 to consumed flags at535. These are ordinary boot observations on the discovery inputs, not executions of the fixtures.

These substitutions qualify isolated render inputs only. They do not prove normal evolution activation, song-title identity, complete playback or audible parity. Later ordinary boot requests can replace the selected score; capture duration alone cannot establish complete rendering. Root owns subsequent hidden runtime captures and read-only request logging.
