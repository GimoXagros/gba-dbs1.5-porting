# Source-relative child attack rectangle correction

Frozen NEW builder `tools/build_shoot_child_attack_rectangle.py` SHA256
`185072F560F82D5A8AD63E416E3E8C9A5A2503B353A5AEA9597C9F44CF20A3E1`
accepts exact6D, USA GBA and WSC1.5, with fresh `output --manifest PATH`.
Isolated output `build/shoot-child-attack-rectangle-20261109/component.gba`
is `1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC`.
Manifest SHA256 is
`FF0B5FFF3B43E692128A0A6B857AFC97F9FE714657439ACFD2CE05D078B2FF73`.

Eight command+0C words at5B90A4+n*16 now point to085B9180. Ten source bytes
from3D1F3C are copied there: type19, X/Y offsets0/0, half extents208/208.
Nine ExpectedWrites declare42 bytes and invert the complete ROM to6D.
The new record explicitly extends this child P1's384-byte allocation within
the original resource-family envelope5B851C..5B9328, before P0 at5B9200.
The full ten-byte extension is erased, has no tracked ownership overlap,
and passes strict mirrored/unaligned-pointer and ARM/Thumb no-inbound scans
with zero exemptions. Unused resource gaps are not treated as anonymous caves.

The source consumer74250E loads the current command;742511..517 selects
the P1 segment/bank.74258A checks its sixth word and742594 loads that
ES-relative pointer, then7425B2..5E0 copies offsets, extents and type.
The generator's P1 far resourceBD:21E3:0000 resolves to3D1E30. Therefore
word010C means3D1F3C. The old converter's hardcoded commercial032C mapping
cannot prove this WSC1.5 command pointer. This final source-relative patch
is authoritative; the old shared converter and its historical oracle are
unchanged and are used only to verify exact predecessor bytes.

All163 production payloads using that converter are checked: child20 has
exactly eight nonzero010C pointers in event1, upper34 and rules109 have zero.
Unknown nonzero pointers are rejected. All155 null pointers, event-level B
records, A metadata, timing, callbacks and existing dispatcher code remain
byte-identical by full inverse. No source type clamp or handler change exists.

Author checks execute128 actual ARM cases (all eight pointers times16 NZCV):
complete producer353C88, including the one explicitly implemented native
MUL353CB8; overlap metadata transfer36E348; and36EB54/6FD000 dispatch.
They produce type19 and208/208 extents and select existing handler0836F37C
at index22hex. The same fragment on6D reproduces type0, indexFFFFFFF0,
and target0A000003. No service or BIOS is modeled; collision geometry and
reaction handler bodies are outside these author fragments. Fourteen inverse
mutations reject. Independent QA and actual gameplay remain separate.

No existing converter/builder, main, Git, emulator, save or guest memory was
changed. Production promotion and positive-hit/ending acceptance remain held.
