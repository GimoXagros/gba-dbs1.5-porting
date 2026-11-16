# Invalid evolution event reaches protected BIOS reads

The completed private diagnostic `build/bizhawk-music-three-6f-20261116-b`
ran the isolated8C72 image. Its `evolution-event-queue.txt` SHA is
6583A07BE8551107B020D877FCFF6F730A618D54D60BA0151EC8984B54A086B4;
`launch.json` isD92F27BA21BFE7B288EFB35B0F5A24ED34A83CB5553ACE7015864943E79CA3E5.
The read-only observer `tools/bizhawk_observe_evolution_event_queue.lua`
isC83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D.

At core34954, the post-selection hook at0835A558 observes CPU identity11,
R0=00004000 and tableR8=0835A596. The following accepted-request hook at
080D15D0 records LR08012918, presentation020118D4, P1=0861B4BC,
event4000, command/cursorFFFFFFFF, R1=FFFFFFFF, R0=04000020,
R8=4/R9=1. This directly binds the bad event to the animation initializer's
audio call at08012914, not to the later animation tick call08012BA8.

The pinned native setter08012874 loads P1's event-table pointer0861B4C4,
adds4000*16 and reads row0865B4C4. All four row words areFFFFFFFF.
It installs those words as command and metadata pointers without an event
bound check. The following native reads explain the otherwise unusual
04000020 exactly:

1. At080128C4, `LDRH r0,[r1,#6]` with R1=FFFFFFFF wraps the effective
   32-bit address to00000005.
2. The pinned mGBA source's protected BIOS load path takes the low16 bits
   of `biosPrefetch` for address5, then rotates the 32-bit result right8
   because the address is odd. The observed04000020 implies the protected
   latch's low16 bits were2004: `ROR32(00002004,8)=04000020`.
3. At080128E0 and08012900, `LDRB r8,[r1,#1]` wraps to00000000 and reads
   the same protected latch's low byte04. The native initializer accepts
   this value as sound04/type1, producing the directly observed request.

The complete BIOS latch was not captured; its upper16 bits are not assumed.
This particular read is a protected BIOS-latch read, distinct from the
generic unmapped-memory/open-bus path. It is not a sound byte from a valid
cartridge animation command.

Implementation evidence is the downloaded official
[mGBA memory.c at fa977cc](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/memory.c),
local`build/collision-alignment-20261116/mgba-memory-fa977.c`, SHA
501DBBCA7D5D7CBAA86240DE2D6A4E2E1186B50F74DDE11BCF2F323C4AF8C437.
The relevant source ranges are542–548/646–647 for halfword reads and657–663
for byte reads. Executable-to-source identity has not independently been
proved. The actual register observations and wrapped native addresses are
separate evidence from that source-based behavioral explanation.

## Conditional ID14 discriminator

A read-only calculation on8C72, using the actual ID14 group0/group1 P1
pointers and the retained selector opcodes, gives:

| Selector | Loaded event | Actual P1 | Computed event row | Four row words |
|---|---|---|---|---|
| Entry | unsignedB054 | 086184A0 | 086C89E8 | allFFFFFFFF |
| Air return | signedFFFFE3A0 | 0861DB48 | 08601550 | allFFFFFFFF |
| Ground return | 0019 | 0861DB48 | 0861DCE0 | 00000001,0861E1D0,0861E650,0861E670 |

Thus both bad ID14 selectors would install malformed command and A/B
metadata pointers if those paths ran on these resources. The air lookup
uses signed LDRSH; treatingE3A0 as unsigned would compute the wrong row.
The valid ground command begins`0EFF1000180000000000000000000000`.

No actual historical ID14 path is reconstructed by these arithmetic
calculations. They do not prove that a historical collision B-list read
usedFFFFFFFF, produced typeE5, or supplied the historical timeout's R3.
The newly observed BIOS-latch mechanism shows why the prior unique-ROM
candidate for04000020 was only conditional. Historical E5 first-writer and
pre-dispatch provenance remain unresolved; no old census or emulator
replay was run for this analysis.
