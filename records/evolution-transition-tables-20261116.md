# Source evolution transition tables

The isolated Impmon contact change exposed three retained retail presentation
tables that still contain only eleven identities. Source Ver.1.5 contains
fifteen. No audio request is suppressed by this correction.

`tools/build_evolution_transition_tables.py` is frozen at
`7DC002920D38E12F49743DB1D51E644037FFA5E487A69632445ACB616D05600D`.
Its input is the isolated 16 MiB `8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8`.
Output `build/evolution-transition-tables-20261116/component.gba` is
`C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`;
the accompanying `component.json` is
`4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6`.

## Exact source and defect

Source SHA is C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7.
The actual source selectors at 7673C1 and 7675C2/7675CE index the following
tables by twice the fighter identity:

| Purpose | Source | Retained native | Fifteen source entries |
|---|---|---|---|
| Evolution entry | 7679C2 | 35A210 | 109,119,94,109,126,98,111,98,119,98,98,105,109,109,115 |
| Ground return | 7679E0 | 35A580 | 24 for identities 0–13; 25 for 14 |
| Air return | 7679FE | 35A596 | 25 for identities 0–14 |

The first eleven entries are byte-identical. Native ID11 air lookup reads
35A5AC, the next ARM instruction E92D4000, as signed halfword 4000.
The completed 6F-a final RAM dump independently contains CPU11 presentation
event4000 and command base/cursorFFFFFFFF; its P1 remains the correct0861B4BC.
That event indexes erased bytes beyond the actual39-event P1 resource.
Source41 event1 itself contains only FF sound bytes. The call at35A670
advances animation by one tick; its argument1 is not an event selector.
Root's separate completed diagnostic reports the direct chain from
35A558 event4000 through initializer08012914 to accepted080D15D0 sound04/type1.
The independent capture reviewer owns the final runtime provenance verdict.

ID14's retained entry/ground/air reads are B054/0019/E3A0. These are recorded
without claiming a cause for any historical E5 failure.

## Allocation and exact change

The frozen production music manifest
`build/repro-v77-20261110-c/evolution-music.json`, SHA
AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91,
owns D33000..D40000 and records the final occupied byte before D3EA01.
The builder checks each earlier allocation's payload hash, the complete
unused tail, and the frozen conservative scanner's zero incoming
pointer/ARM/Thumb encodings. This layer explicitly suballocates
D3F000..D3F05A for three15-entry halfword tables; it does not infer ownership
merely from erased bytes.

The three ADR instructions35A1E4/35A54C/35A550 become same-condition literal
loads. Their aligned pointer words are35A210/35A580/35A598. The air literal
deliberately uses598 rather than halfword-aligned596, respecting ARM7 word
load alignment. New tables areD3F000/D3F01E/D3F03C. Nine disjoint writes
declare114 bytes and change109; complete inverse restores exact8C72.

## Author verification and limits

720 modeled actual ARM lookup cases cover identities0..14, all three paths,
and all sixteen incoming NZCV combinations. The imported interpreter runs
the real prefix; a strict local decoder executes the final pinned
register-offset LDRH/LDRSH, which that interpreter does not support.
For identities0..10, output registers, flags, RAM and writes match the old
lookup, except for the deliberately relocated R8 table base. Sixteen
actual clean-mode Calumon gate cases reject boss15 before table selection.
All45 selected events fit their actual P1 tables and bounded command
extents. Two harmful mutations reject the old air selector and a4000 entry.

This author did not launch an emulator, edit main, or perform Git actions.
Independent verification and a new actual CPU11 evolution/pause/resume/
natural stage return remain required. No historical E5 closure or full
gameplay parity is claimed.
