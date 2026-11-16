# Read-only ordinary-play music observations

`tools/bizhawk_probe_result_music_lifetime.lua` is frozen at
`CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430`.
It reads immutable `bizhawk_probe_result_languages_16m.lua` (5D626406), which
reads immutable `bizhawk_probe_result_languages.lua` (928186AE). The full
effective Lua body hash is
`88B8672BC0C87DA27145F4E6012175A0CB8058F5D17908E63A01A94953A616E8`.

The only effective-body additions are a scalar telemetry prefix and one
finish/close call immediately before the unique existing `client.exit()`.
The ordinary KO/result input schedule, frame advances, captures, result trace
and exit policy remain unchanged. The wrapper uses the same userdata arguments.
No new guest writes, saved states, screenshots or memory dumps are introduced.

Ten execution observers cover evolution selector `D14BC`, its queue return
`D14F0`, music request `37B44C`, player-zero M4A start/return `37C298/37C29C`,
the conditional de-evolution return site `35A75C`, pause/resume entries
`37B48C/37B4A8`, and the actual header comparisons `37C364/37C398`.
The de-evolution site reports eligibility rather than claiming that its
conditional call executed. Header comparisons report both equal and unequal
operands. Player-zero address `03006B40` is pinned to table word `37FBB4`.
Reads inside hooks are bounded scalar values; the start-return observer
requires a player-zero start observed in the same core frame.

Output goes only to `music-lifetime.txt`. Each event label emits at most
32 rows, for a maximum 320 event rows, plus a start line, summary and ten
counter lines. Counters retain all qualifying observations beyond the row cap.
Music requests are filtered to original music IDs below `1E` or new IDs
`6C..6F`; actual M4A starts are filtered by the player-zero pointer. The final
summary explicitly counts evolution entries and starts of each appended
score. An absent natural evolution/pause/resume remains absent coverage.

Author checker `tools/check_result_music_lifetime.py` is frozen at
`FFE048155581D20BA90C05F12BB81331D3D403505E1C063FA3CE7B03148D95B8`.
Actual in-process Lua54 checks confirm whole-body composition and syntax,
all ten callbacks, selector identity logging, a player-zero 6E start, both
header outcomes, and a seventy-request case retaining count70 while emitting
32 rows. Author report
`build/result-music-lifetime-author-20261110/report.json` is
`86181A00AEA0E6185EA33A8CD05B80C3F03B1A013989AC13AA77902D978C0F1E`.
Independent composition review and root-owned actual runtime are separate;
this author executed no emulator or gameplay inputs.
