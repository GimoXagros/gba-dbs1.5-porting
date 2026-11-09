# Actual child attack pointer cause

The6D ordinary-input positive-hit trial stops at core69165, before native
36EBA4, with R1=FFFFFFF0 and R9=0A000003. This is an observed invalid branch
target; no FIRST→SECOND positive hit has occurred and HP remains4/37.
Evidence is `build/bizhawk-gba-shoot-positive-hit-20261109-a`:
`positive-hit-first-failure.txt` and `invalid-dispatch-target` RAM/State.

Attack list030048C8 has one record: owner020112B0, type0, metadata085B9178.
Victim list030049B8 names FIRST02011710. The attacker is a live kindB child,
callback085B9C00, event1, P1/P0=085B9000/085B9200. The slot formerly held a
scene presentation, but is now legitimately reused by the enemy child.
The A pointer085B9178 is valid eight-byte attack metadata; it is not the
erroneous rectangle pointer.

The child event1 has eight sixteen-byte payloads at5B9098+n*16. Every
payload+0C incorrectly points to08350438. The original WSC1.5 P1 at3D1E30
has sixth word010C in all eight twelve-byte source payloads. That is a
resource-relative pointer to3D1F3C, whose ten bytes are
`19 00 00 00 00 00 D0 00 D0 00`: attack type19, offsets0/0, half extents208/208.
The native producer353CA4 reads the payload+0C pointer,353D20 reads its
type, and353D24 submits it to the attack list. The separate A pointer is
stored as metadata at list+10.

`shoot_resource_conversion.convert_shoot_payload_item` instead maps every
nonzero sixth word by adding032C and attaching0835. That translation matched
the older retail resource oracle, but was reused for the different WSC1.5
resource. For010C it produces08350438. Those retail bytes are
`00 00 00 00 00 00 00 00 05 FF`, yielding type0 and incorrect extents.
The complete original USA ROM has no existing exact ten-byte source
rectangle to reuse.

Native36E370 copies the actual list type0 to03004D20. The ordinary victim
reaction at36EB58 subtracts8 then doubles it, giving FFFFFFF0. The existing
1A/1B extension6FD000 preserves this unmatched legacy index;36EBA0 reads
the unrelated instruction0A000003 at36EB88 as its branch pointer.
The minimal source correction is a separately owned converted type19
rectangle and all eight payload references. A dispatcher clamp would hide
the malformed producer and preserve the wrong hit geometry. Placement,
independent conversion proof, implementation and runtime remain separate;
this finding changed no ROM, guest memory, script, or emulator.

The shared converter's production caller population is bounded explicitly:
child3D1E30 has20 payloads, of which only the eight event1 items have nonzero
word5; initializer upper3CF410 has34 payloads and rules3BD730 has109, all
with word5 zero. The remaining direct caller is the read-only commercial
oracle. Thus eight pointer words are the complete affected current production
population; initializer event-level B records are a distinct already copied
ten-byte field. A correction should pin this population and reject new
nonzero cases instead of trusting the old resource-specific address rule.

Candidate5B9180..5B918A follows the exact384-byte child P1 and precedes its
P0 at5B9200. The tracked1394 ledger has no interval overlapping those ten
bytes. It lies inside the original resource family's declared envelope
5B851C..5B9328, so using it requires an explicit resource-owner extension,
plus erased bytes and a strict no-inbound scan; this is not a claim that any
erased tail is unowned.
