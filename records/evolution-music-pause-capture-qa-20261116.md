# v77 actual evolution music pause capture

PASS for the completed private Korean capture
build/bizhawk-music-pause-20261116-a. The launch exited with code 0,
produced the target completion marker, and loaded the exact 16 MiB
C344 candidate. The independent audit rehashed all 43 top-level files
and closed the launcher inventory. All five capture sets contain the
six expected memory regions and a PNG.

The input route matches the first 87 trace lines of the ordinary
Korean run. Its original music telemetry also matches through the
natural 6E start at core 9076. The targeted route then sends four
Start frames, 30 neutral frames, and another four Start frames.

| Core frame | Observed player-zero state |
| --- | --- |
| 9076 | The natural 6E start installs header 08D75728 and caches 6E. |
| 9077 | The only pause entry, equal native header comparison, and matching MPlay Stop call occur in the same frame. |
| 9081 and 9110 | The cache and header stay at 6E and 08D75728. The held status is 80000007 at both logged boundaries. |
| 9112 | The only resume entry, equal native header comparison, and matching MPlay Continue call occur in the same frame. |
| 9115 | The cache and header still match. Player status is 00000007 after resume. |
| 10399–10400 | Natural devolution is eligible and stage music 10 starts in the next frame, setting cache 10 and header 08384BF8. |
| 10401 | The capture ends at the next frame boundary in battle mode 7. The IWRAM snapshot confirms the stage cache and header. |

The terminal IWRAM snapshot contains the exact boot copy of the ROM
span. The execution hooks report zero calls at both canonical copied
addresses 03000D00 and 03000D0C during this route. The ordinary Korean
run reached stage music at core 10365. The targeted run reaches it
35 frames later, matching the interval between Stop and Continue.

The verifier rejected five in-memory contradictions covering nonzero
alias count, an uncleared stopped bit after resume, wrong pause-header
operand, stale stage cache, and one extra held Start frame.

| Evidence | SHA-256 |
| --- | --- |
| tools/verify_evolution_music_pause_capture.py | E2AEB4A488CF76B47DE758C7BBF0CDC0B1E3357B9E17A1C2F95B549ED3082F91 |
| build/evolution-music-pause-capture-qa-20261116/audit.json | 68A8960E0BF02746DF28122E8A8137C05AF0DE9911310B11DF034F14732C87E9 |
| build/bizhawk-music-pause-20261116-a/launch.json | 20A9A315822475C1DE8A9340B07779A13C8B5EB33518841AEFE7B551A8F8A50C |
| build/bizhawk-music-pause-20261116-a/trace.txt | E78DA245AF91EEB45442DF6FC2D7CCCF64552F13B4F544FDF1B0712E9C96FE04 |
| build/bizhawk-music-pause-20261116-a/music-lifetime.txt | 4902A6524446EC87EEBDF8AC0043283FF3C99C77AE319E65F576F5301B5C82B6 |

The capture ran with sound disabled and verified runtime player
state for this Korean actor and song 6E. Coverage of the other three
songs in ordinary pause gameplay, audible output during this route,
and execution at other IWRAM mirrors requires separate evidence.
