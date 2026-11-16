# v77 ordinary 6C retry capture

PASS on the exact 16 MiB C344 candidate. The successful retry kept
the game and original actor selection intact. It used ordinary Left
input before Calumon became collectible, only in a validated live
fight and while player X exceeded 0x600. The normal collectible
chase and the pause sequence then used their existing rules.

An independent Lua 5.4 preflight reconstructed the full effective
body EB7296BD3D518EB460F839D4AEA5B3D02AB07E380EF78B76DB522D3DB5A612B7
from the frozen sources. It checked the threshold and battle/pair
guards, the existing active collectible branch, and rejection of
other song targets.

The actual Korean run shares the original 54-line trace prefix
through fighter selection. The input-selected P1 actor 5 triggers
category 0 at core 8276. Player zero begins song 6C at 8277 with
header 08D43CAC and cache 6C.

| Core | Native observation |
| --- | --- |
| 8278 | Matching header comparison and one MPlay Stop call. |
| 8282 and 8311 | Same cached song and header at both stopped boundaries. |
| 8313 | Matching header comparison and one MPlay Continue call. |
| 8316 | Same cached song and header with stopped bit cleared. |
| 9600 | The same actor naturally de-evolves. The native stage selector queues the prior stage song 10. |
| 9601–9602 | The actual player start returns with stage cache 10 and header 08384BF8. The next battle frame confirms them in IWRAM. |

All 42 top-level artifacts and five complete frame-boundary capture
sets independently verify. Both canonical IWRAM execution counters
are zero. The capture's saved configuration shows sound disabled.
This records the player's runtime state for 6C rather than audible
output.

| Evidence | SHA-256 |
| --- | --- |
| tools/verify_evolution_music_6c_approach_capture.py | 98D81055830D19927037DCE8009BD5FA17956CD2D129633F873C3C374A3468D3 |
| build/evolution-music-three-capture-qa-20261116/audit-6c-b.json | 76742352091B9941CB17C9CF21C64E784CBCFFB029F1FD9FFB8358C32D72394C |
| Retry launch manifest | E49CB6CCC6177C09367BEABC5C4076080A41B977945E198B7E2C9FABDA9A06AB |
| Retry music telemetry | 6EBAFDE75697F80DCF90FD6A28AF0FCBC38B8A52B47F12CF9F9108DC2FE4E80C |
