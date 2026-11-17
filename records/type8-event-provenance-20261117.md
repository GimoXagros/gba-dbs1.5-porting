# Type8 event predecessor observation

The failed frozen `933C` campaign ends at core8672 with CPU ID13 actor
`02011828`, presentation `020118D4`, resource `0861CF0C`, event `36`, and
invalid collision type `8070`. The previous frame still reads valid event `0C`.
This document records the narrow predecessor observer; it is not a fix or a
completed campaign claim.

The final actor callback is `0836A744`, the native hitstop continuation, with
saved callback `0836AF64` at actor+84 and duration10 at actor+8C. The saved
callback follows constructor `0836AE94`. Record `0836C32C` selects event36 and
that constructor, and its remaining metadata agrees with the final actor.
These static facts identify a plausible predecessor, not an observed caller.

The native metadata reader `083555D0` receives a 32-byte record in R1. It sets
the actor callback from record+4 and passes record+2 to `08012874`. The setter
stores the event at presentation+0E, multiplies it by16, and reads the selected
P1 row without a row-count check. A clamp here would conceal the bad producer.

## Read-only replay wrapper

`tools/bizhawk_probe_type8_event_provenance.lua` adds eight opcode-pinned hooks:

| Address | Instruction word | Observation before instruction |
|---|---|---|
| 08012874 | E92D403F | SP+0 selected event, SP+8 presentation, LR caller |
| 08012884 | E1C530BE | Actual event store R3/R5, saved LR SP+18, selected P1 row |
| 083555D0 | E92D4008 | Metadata record R1, all32 bytes, R4/R5 owner, LR |
| 083525C4 | E12FFF18 | Actor callback R8 with R4 owner |
| 0836A69C | E92D4013 | Hitstop duration SP+0, continuation SP+8, actor SP+10 |
| 0836EC90 | 159F1B20 | Conditional evolved-air table load, CPSR.Z, scratch |
| 0836F3B8 | E5D50011 | Victim R5, table R1, indexed record and scratch subtype |
| 0836F3CC | E92D0010 | Final record after subtype*32, before actor/presentation swap |

Only actual active Train SECOND ID13/role1 with reciprocal live actor links is
journaled. The callback dispatch does not assume R5 already means presentation:
the common damage path explicitly changes R4 to victim and R5 to victim+AC.
The final256 events and per-hook counts are written once at parent completion.
The wrapper adds no input, game-memory write, register change, or savestate call.

The frozen `F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF`
campaign wrapper is loaded with exactly one string insertion:
`log:close()` becomes `log:close();finish_provenance()`. This closes the journal
before the parent's completion marker. All parent frame-loop, input, failure
and authorized score/HP write behavior remains inherited.

The new wrapper SHA-256 is
`E999477CB5D5A72E64B46DCC6F24838BF4D2447B221A3E018DB88B15BC467523`.
Independent Lua preflight is PASS (`A20FB90505A8032457C1C898AD43AE93924F4C534A57AA11AF03144AF37CEF12`,
`build/type8-event-provenance-qa-20261117/lua.json`). It executes both composed
Lua drivers, verifies identical modeled inputs/writes/output states, all eight
opcode hooks, typed-owner suppression, the277-entry-to256-entry ring boundary,
and close-before-marker order. The actual replay is a separate evidence gate.

## Required dynamic proof

At the actual transition, establish the full ordered chain: evolved-air
selector executes with its condition true, table `0836BED4`, ID13 indexing to
`0836C32C`, metadata-reader caller `0836F3E0`, setter caller `08355620`, event36
store, and hitstop installation. Compare the existing capture files, input
trace prefix and authorized-write ledger against the frozen failed run.

The actual fresh replay now establishes this chain at core8671, seq5368–5373,
with hitstop construction at core8672, seq5375. The journal SHA-256 is
`1B3C05A0A1AA43C0242DD1F5772D21305267579EB57C52DDADAB263DB07AE7AC`.
The event assignment therefore precedes the first bad collision by one frame.
See the [independent repair review](character-type8-tables-independent-20261117.md)
for the source-derived correction and exact consumer checks.

No emulator or ROM was changed by this observer author. Corrected gameplay
and completion remain separate runtime evidence gates.
