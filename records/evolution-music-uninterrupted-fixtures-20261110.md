# Native full-score render-only fixtures

The first native38 capture was cut by the ordinary boot request00 before the
score ended. Source request00 instead targets the four foreground/SFX slots;
it does not itself end the four BGM slots. This is a fixture-lifetime problem,
not evidence requiring a production music change.

Changing native song-table row00 would not avoid the stop: native37B44C
special-cases zero before the song-table lookup. It branches to37B478, calls
37DB84, and enters the Thumb37C3B0 all-player stop loop.

The four NEW r2 native fixtures therefore replace only the four-byte BL at
37B47C (`C00900EB`) with ARM `MOV r0,r0` (`0000A0E1`) over the respective
r1 render fixtures. The existing saved-LR prologue and unwind remain exact.
This deliberately suppresses every global song-zero stop in these test ROMs.
They are explicitly unsuitable as normal gameplay builds.

The builder pins the actual BL target, complete unwind, ARM→Thumb bridge and
all-player loop. Ten bounded actual-ARM zero/nonzero cases verify the selected
service call and stack/return behavior; downstream M4A is an explicit imported
service boundary. Every full inverse restores its exact r1 fixture, then the
DD6D73B5 component. Original source fixtures, r1 files, and main remain intact.

| Item | SHA-256 |
|---|---|
| `tools/build_evolution_music_uninterrupted_fixtures.py` | `E8FB33FC6C0857E8DEC4AD1D8D15695632305F24ADD0E3B260054D9A24A94C82` |
| `build/evolution-music-render-fixtures-20261110-r2/manifest.json` | `CE2DC41BB52843B7022027A724115F30D9A5D9695302F7633655590A46028AD9` |

Files are `gba-source-{38,3C,40,F8}-uninterrupted-fixture.gba` in that
directory. Independent verification and actual full-score capture remain
pending at this record's creation. Other normal boot song replacements may
still interrupt a score and must be observed, not assumed absent.
