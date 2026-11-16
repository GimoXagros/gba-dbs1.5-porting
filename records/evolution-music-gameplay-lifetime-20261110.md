# Ordinary evolution music: caller and return lifetime

This narrow source review uses original WSC1.5 C415 and the C508 composition.
It does not repeat the previously checked sixteen-ID selector cases or claim
an ordinary evolution playback capture.

The ordinary native caller `0835A448..0835A450` reads the actor's character
byte at `r4+11`, pushes it, and invokes `080D14BC`. Its preceding `0835A43C`
call loads evolution group one through `08353304`. Original source
`7674F9..767517` performs the same group-one load and passes the actor's
`+11` character byte to the source selector `78727F`. Thus the selector's
input is the live actor identity, rather than a category or evolved form ID.
The source-derived sixteen-entry table maps that identity to the four scores;
whether every identity reaches this caller in ordinary gameplay is not newly
established here.

The values previously called request "cooldown" (`6EA` native, `8AC` source)
do not establish a thirty-second playback deadline. Native consumer
`080D1500` tests pending bit `100`, clears it, clears request field `+6` at
`D152C`, and dispatches the selected song at `D1534`. The main loop invokes
it at `0002BC`. Source `7872E8..7872FD` similarly clears bit `100` and field
`+6` before dispatch. The occupied-request gate prevents replacement until
consumption; these inspected consumers do not count the value down.
Consequently no native tempo change or longer gameplay timer is justified
from the apparent 30-second interpretation.

Music return follows de-evolution. Native `35A748` loads group-zero assets;
`35A750..35A75C` then tests `03004500+6 & 80`, calling stage selector `D13EC`
when clear. Original `7676D1` loads group zero and `7676DE..7676E7` tests
physical `103D4 & 80` before source stage selector `7871A8`. Native `D13EC`
selects a stage/boss track and enqueues it through `D15C0`; consumption then
replaces the player-zero evolution song. Ending evolution or leaving the
battle can therefore replace a finite score before its final note by retained
gameplay design. This review does not assert a universal elapsed form duration
or that all original and native de-evolution timing is identical.

The review also found the appended-song pause-cache defect, corrected only
in the new C344 isolated layer documented in
`evolution-music-pause-cache-20261110.md`. Prior C508 outputs and the four
complete source/native audio-render comparisons remain immutable.

A minimal ordinary-playback probe can add read-only execution observers to
the existing result/KO controller: log entry `080D14BC` with entry-SP identity,
actor `r4` and its `+11` byte; actual play adapter `0837B44C` with R8; actual
song-table consumer `0837C28C`; de-evolution call site `0835A75C`; pause and
resume entries `0837B48C/0837B4A8`; cached ID `03004E98` and player-zero active
header. Record the original input schedule unchanged. A neutral KO run may
not encounter Calumon/evolution, so absence must remain explicit. The old
mGBA position-sweep probe writes actor coordinates and is unsuitable as
evidence of an ordinary input-only route. No new emulator run, observer,
guest-state change or save loading was performed for this source review.
