# Actual counter1 deadline: independent capture audit

**PASS**, report `9472B613...`. The root-owned run restored the genuine
frame69935 checkpoint and advanced188 neutral frames. The earliest counter1
cycle was observed in core70122; its exported outer boundary is70123.

All36 inventoried files match the completed launch manifest. Wrapper053FD747,
baseC625D710, hostD7D1627B, the280D ROM, source checkpoint files and previous
9F909134 audit remain pinned. All three new genuine States match their complete
IWRAM/EWRAM/VRAM/palette/OAM exports. The two final captures have byte-identical
States and no intervening emulated frame.

The52-row trace contains one start row plus51 target events, all target events
in core70122. It records the successful75C consumption and fresh74D8
initialization before the first IRQ; previous-cycle events are excluded.

| Actual witness | VCOUNT |
|---|---:|
| Counter1 initialization: base0/counter1/index0 | 1 |
| First IRQ and first comparison: programmed line0, target1 | 8 |
| Eight equality matches and subsequent counter/index stores | 9,12,15,19,23,27,32,37 |
| Final callback installed | 37 |
| Final callback actually called | 38 |

All30 comparisons cover programmed lines0..29 without a gap. Their operands
agree with the actual DISPSTAT high byte and source offset table
`0,2,4,7,10,13,17,21`; VCOUNT is checked separately. Each equality is followed
by the expected counter/index stores. The final slot is086FFEBC with counter9
and index8. Four falsified trace variants—late first comparison, cross-frame
final, wrong operand, missing store—are rejected.

The restored Core is **not** byte-identical to the source Core. Its six byte
differences are retained exactly at raw Core180,181,188,189,18C,18D. The pinned
mGBA serialization layout identifies native17C..17D as channel4 LFSR state,
184..185 as its last event, and188..189 as its next event. These are functional
audio fields, not padding. CPU register bank, all five RAM regions, native
extensions and the managed suffix match exactly. No normalization or new
independent loader-cause claim is made.

| Item | SHA-256 |
|---|---|
| `tools/verify_shoot_counter1_capture.py` | `8367ADF1A02600531AB6D6FBD3F4A620EA6B8C970AE46F04D4A8BF08F96C55AA` |
| `build/shoot-counter1-actual-audit-20261110/report.json` | `9472B613513D146C9ECAE52B3598E92EA0D860AF369515B6663DC3B234A65B85` |
| Actual launch manifest | `51A8938C2C692B2791A4A4D7110C8277D877C69F8CC39EABD597AD967F5A2FF3` |
| Genuine source Core | `32A904634D2E9F941853496BE03431EBE276234A1C7E28A9DAD3129387C05583` |
| Actual restored Core | `42252F34F67416229B8A72C9C15CFC0C71C5AD55A72BB68C2F38E081ED6C37E5` |

This establishes the first-counter deadline in this actual restored run. The
probe deliberately stops at the final IRQ: its final snapshot remains
mode7/stage11/sceneCD510. Earlier complete cleanup/mode8 evidence is separate.
The auditor launched no emulator and changed no capture, source, main or Git.
