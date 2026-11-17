# Separate mode23: initial task and native resource contracts

Bounded read-only review on frozen574FD261, original WSC1.5 C415F227, WSC1.0 58220B9C and original USA996DE333. The earlier44-root/4052-instruction graph in `shoot-normal-entry-save-copy-20261109.md` is reused. This review decodes only the constructor, three initial callbacks, their first setup, the direct actor-creation dependency and one static-background import. It does not repeat the full graph, expose a menu entry, allocate native RAM, modify a ROM or launch an emulator. Native mode20 completion correspondence and corrected title assets are already established separately.

## The three initial tasks are not a complete scene

Source mode23 initializer74A940 is RETF. Constructor74A941 first disables display, creates the shared OAM-reset service through4FFF:1D68, resets the audio-command owner, and creates three tasks:

| Task role | Source callback chain | Priority | Private handle |
|---|---|---:|---|
| Audio/display service |4090:C999 -> C9B3 -> call C9B9 (raw74D299/2B3/2B9)|F100|0200:0002|
| Scene controller/setup |4090:A56B -> A59F (raw74AE6B/AE9F)|1000|0200:0000|
| Initially idle auxiliary object |4090:BC1C (raw74C51C)|1800|0200:0004|

Constructor74A9C3..9E7 clears word0200:0012 and bytes0018/0019/001A, then copies selected character config1000:0058 into0200:001B. It also clears physicalOBJ-palette colorFF00 and enables the sprite/display state through the existing ports. These are typed source owners; the addresses cannot simply be copied into native RAM.

C999 only replaces its callback with C9B3 on its first visit. C9B3 calls C9B9, which services sound8719:0148 and conditionally calls shared4FFF:4F84 when private state0012 bit1 is set. It is not a second simulation or battle task. A56B likewise only installs A59F for the next visit. BC1C derives current-task payload at header+10 and presentation at payload+22, then returns; it remains idle until another controller installs its active callback. BC36 later runs localB9F1 on that presentation, while BC5A waits on payload+1E and restores BC1C. Merely allocating these three callbacks would not implement the game.

A59F immediately creates a real scene. It calls static-background loader859A:034A with destination1000, halves the16 background palette colors, initializes a fixed presentation at0200:0020, selects event0 and puts it at(112,72) with presentation flag2000. It calls localA30C (raw74AC0C), which reads scene-row table4090:9A4E and allocates participant tasks4090:B71C. Initial scene index0018=0 has participant count3. Their handles are written beginning at0200:0006. Thus the actual first setup already depends on three additional participant tasks, not only the three root tasks.

A30C chooses the selected identity for participant0 and selects the other identities through scene tables, writes participant payload fields and owns their presentations at payload+22. The following A59F body seeds positions/velocities, optionally selects evolved presentation records from4000:03C0 plus identity*20, changes display state, sets timer0200:001E=100 and installs successorA7CF at74B0BF..C7. No blanket fifteen-ID bounds or general actor-lifetime proof follows from this initial-row observation. The remaining source callbacks, input/rules and all rounds still require their existing mapped graph to be implemented and checked.

## Native services that can be reused

The existing service correspondence is positive and already documented: source task allocation4FFF:0980 maps to native08011AC4; source task header/payload10 becomes native18, with100-byte payloads and native118-byte slots. Task unlink4FFF:0A32 maps to08011BE4, and current-task retirement uses08012030. Native allocation accepts the existing stack priority/callback ABI, so source F100 must retain the native sign-extension/insertion convention rather than be treated as an arbitrary unsigned constant. See `shoot-terminal-upload-lifetime-20261106.md` and `shoot-task-capacity-qa-20261106.md`.

Source presentation constructor4FFF:23F4 maps to080127E4; event setter4FFF:24CB maps to08012874; palette loader4FFF:2389 maps to080132EC; the dynamic presentation renderer has the established source2A4B/native08012C28 correspondence. These are reusable primitives, not an existing mode23 controller. Their native presentation is50 bytes and uses full32-bit pointers; source private task handles and payload+22 presentations need an explicit new native layout and lifecycle proof. No free RAM address is proposed here.

## Complete fixed-presentation asset reuse

A59F's literal resource triples resolve to P0 source3D58F0, P1 source3D87B0 and P2 source3D7E20. These are not part of the first64 common resource-table rows; that table absence alone says nothing about native availability. Direct conversion establishes an existing complete native asset view:

| Source resource | Ready native resource | Bounded evidence |
|---|---|---|
| P0 3D58F0 |080B7348|One layout with31 parts; all124 layout bytes at3D5904 match080B7360. Header constants match. Descriptor3D8E50 resolves992 bytes at3C4F80; all31 converted tiles match080B73E4. Native fullP0 intervalB7348..B77C4 SHA9C2B90865744DFE21AE2251510B04D124346C597E568A7766012D9ABA4782F96.|
| P1 3D87B0 |080B7318|Simple single-event header points to one command and one8-byte A record. Expanding typed pointers/command padding reconstructs all48 native bytes exactly, SHA14E3BC8C0AA32BFF29341EA43F0659015AE27A692E564BEB769770D6DD8533D6.|
| P2 3D7E20 |080B77C4|The complete38-byte source palette converts byte-exact to the40-byte native block.|

The P0 legacy parser reports zero descriptors for this object because its source segment is24F8 rather than2000. That restricted-parser result is not absence of graphics. The actual far descriptor is3D8E50: length03E0, offset0, segment24F8, bankBC, then anFF terminator. The source loader's physical address is3C4F80. The explicit far-descriptor check establishes the real31-tile population.

Native mode6 already uses this complete view: literals080B64A4/A8/AC point to P1/P0/P2 respectively;080B61B4/61C4/61D4 load them for constructor080B6204 ->080127E4. It then selects event0 at080B621C, sets flag2000 and positions(112,72) at080B6230..623C, matching this narrow source setup. This is a particularly useful existing ABI oracle. Reusing the immutable resource pointers is justified; reusing the whole mode6 scene or its global presentation owner is not. Mode23 has different participants, state and lifetime.

## Static background remains a separate entry dependency

Source import859A:034A at785CEA selectsbankC1/DS3F73, copies54 planar tiles from41F830 to physical8000 and15 colors from41FEF2 toFE02. The source caller then halves all16 colors including the separately owned color0. The helper builds the map at the supplied destination1000 through eight explicit rectangular copies of the pattern at41F730, using the generic4FFF:30C9 service. There is no evidence here that the generic map-copy ABI directly accepts these WSC screen entries on GBA.

The packed54-tile block and individually probed tiles0/1/2/53 have no exact match in the frozen574F image. This is a bounded absence of a ready packed resource, not proof that no related/compressed art exists. The minimal native entry work therefore still needs a source-bound background/map/palette converter and precise screen/VRAM ownership or a separately proved native equivalent. It must coexist with the fixed presentation and participant graphics, with source palette dimming converted by channels rather than a blind native halfword shift.

## Smallest real implementation boundary

An honest first entry slice includes private-state/handle ownership, the three root tasks, the initial three participant tasks and their actual setup successor, fixed-presentation reuse, the real54-tile patterned background, typed native display/OAM services, and a demonstrated cleanup path. The root controller's early animation and participant simulation cannot be replaced with a still image or a menu item that immediately exits. This record establishes the reusable services and one complete resource set; it does not establish all44 callbacks or permit exposing mode23 yet.

Before a user-visible entry, the unresolved scope remains: participant callback/rules translation and resource-domain bounds, private native layout and all retirement owners, background-map conversion/lifetime, source menu tree/eligibility/flag0008 producer, character-select transition5, six-column transition ownership and a registered mode23 callback row. Completion should use the already-proved source20/native20 return-to-title chain, whose title resources are now repaired by3CB7. No timing constants are changed or inferred from source/native numeric differences.
