# Selection list lifetime and actual consumers

This read-only analysis independently checks the list-storage conflict behind
the natural ID14 selection failure. It does not alter the roster or read a
save. `tools/analyze_roster_list_lifetime.py` consumes the frozen class14
candidate `7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470`
and both original code sources needed for this check. The report is
`build/roster-list-lifetime-20261016/analysis.json`, SHA-256
`5407FFD87B7C5B5DEBC17BE984B3166D114E5632A740C72AFDA447C51288955A`.

## Positive source order

Source producer raw `7787DB..778847` has SHA-256
`9BABC5510A2FADE32E501D968E337747C7BCD67168D79453132DC1556187D263`.
DS is `0300`; the list begins at offset `00EA`, physical RAM `30EA`.
It writes IDs `0..10`, then appends `13,14` when source state
`1000:004E+25` bit 0 is clear. It reads `1000:004E+19` bits 4 and 5 to
append `11` and `12`, and writes count minus one to the selection object's
`+8` field at raw `778844`.

The source also has an alternate-mode condition: when state `+25` bit 0 is
set, it omits `13,14` and considers only the ID11 unlock bit. The existing
GBA expansion always uses the ordinary-mode policy. Four ROM lists indexed
by the two unlock bits reproduce that existing ordinary policy; they do not
by themselves implement the source alternate mode. All eight source
mode/unlock combinations are recorded in the report.

## Existing native memory is not a longer list

Native list base is `03004710`. Twelve halfword entries fit before offset
`18`. The original native presentation initializer loads the active task
through slot `0300133C` at `08082328`, adds `18` to obtain its presentation,
and retains that pointer in r0. At `0808240C..08082410` it loads `03004710`
and stores the pointer at offset `18`. Input code `08081DBC..08081DC0`
later reads that same pointer.

Therefore extending the list in place makes indices 12 and 13 occupy the
two halves of a live presentation pointer at `03004728..0300472B`. The
root-owned runtime observation of `0360,0201` is consistent with pointer
`02010360`; this analysis independently proves the writer and subsequent
consumer. It does not depend on interpreting those two halfwords as IDs.

Offset `1E` is another positively proved state field: the portrait loader
at `084A5C6C..084A5C74` stores selected ID plus one, and input routines use
that cache. No claim of free space or a live owner is made for offset
`1C..1D` based only on adjacency.

## List read population

The pre-repair candidate contains 21 exact encoded pointers to `03004710`,
including unaligned scans of the full 8 MiB ROM. There are no encoded
pointers to interior addresses `03004711..0300472F`. A complete aligned
ARM PC-relative word-load scan finds 23 load encodings that resolve to the
21 pointer words. Their raw locations are included in the report.

Only three positively identified selection paths use this base as an
indexed ID list:

| Native range | Operation | Consumer |
| --- | --- | --- |
| `08081D04..08081D0C` | Base plus cursor × 2, then halfword | Palette variant selection |
| `08081FF4..08081FFC` | Base plus cursor × 2, then halfword | Confirmed battle character ID |
| `08083230..0808323C` | Mask cursor low byte, double it, then indexed halfword | Portrait selection |

Other selection loads use fixed fields: `08081B68` and `08081DA0` read
cached ID plus one, `08081DBC` reads the presentation pointer, and
`0808240C` writes it. The old portrait tail at `080832D0` and the current
expanded tail at `084A5C6C` write the cached ID, not the list.

Four nearby indexed halfword loads might otherwise look like omitted list
consumers. Their actual address producers identify ROM tables:

| Load | Positive ROM base producer | Table raw offset |
| --- | --- | --- |
| `080825B8` | ADR at `080825B4` | `0825DA` |
| `08082658` | ADR at `08082654` | `0825D8` |
| `0808269C` | ADR at `08082698` | `0825D4` |
| `080826B8` | ADR at `080826B4` | `0825D6` |

The shared address is also used by other modes and the Shoot terminal
transition; those are separate owner lifetimes and must not be redirected
as roster pointers. The finite encoded-pointer inventory and the positive
selection contracts support replacing the three list reads with immutable
ROM views while keeping the native object/cache fields in place. They do
not justify a global replacement of every `03004710` literal.

## Independent review of the resulting adapters

The separate `tools/build_roster_list_routing.py` and
`tools/verify_roster_list_routing.py` were reviewed without editing them.
Their three adapters resolve their owner literal at bridge `+36` and the
ROM-table literal at `+40`. `(unlock & 30) << 1` selects one of four
32-byte rows. The adapters balance their r0 save, preserve LR and condition
flags, and change only the original destination base register. Suppressing
the three overflowing halfword stores leaves the count updates, unlock
tests, and saved-r4 restoration unchanged. No actionable instruction or
addressing defect was found in that review.

The repeated lookups read native unlock byte `03002329`. The selection
callbacks' five direct `03002310` aliases are at raw `81670`, `816DC`,
`81C74`, `81FBC`, and `81FE4`. Their writes affect `+1A`, `+4/+6/+8`, and
`+A/+B`; none covers `+19`. Palette helper `0801F4A4` only invokes the
resource palette consumer. Reset helper `08015D38` clears `03002478` and
`0300456C`, while the link-preparation helpers use `030022C4`,
`03002168/2178`, `03001F00`, `03001302`, and the separate `03004E08`
family. These are distinct from the unlock owner.

The positive native `+19` writers are state reset/load at `08015908` and
`08015958`, Options erase at `080C35E8`, and the battle-award path at
`080BF694` / its existing expansion hook `085B1118`. These are outside
the reviewed selection callback lifetime. The ordinary selection path
therefore retains the same unlock choice between its entry count and its
three consumers. This does not expand the source alternate-mode policy
or authorize arbitrary writes by external debugging tools.
