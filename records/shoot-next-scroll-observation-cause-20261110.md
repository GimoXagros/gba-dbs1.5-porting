# Next-scroll failure: source and observation boundary

The completed280D trial remains recorded as `failure:next-scroll-store`.
This narrow review identifies an invalid write-only MMIO readback assertion;
it finds no evidence of a wrong scroll-store width or wrong native value.
It does not turn the existing run into a completed terminal trial.

Frozen capture is `build/bizhawk-gba-shoot-terminal-display-epoch-20261110-a`.
Its launch SHA256 is
C538496FDF8E0B06A29694FFCC7CE6252494B36F1F7317397700D93422B5A6DE.
Full capture integrity is the separate observer review's responsibility.

The source at75FB20 sets DI=003C, sends its first two bytes to ports12/13,
advances DI twice, then sends byte[DI] to port10 at75FB30 and byte[DI+1]
to port11 at75FB35. The native display correspondingly reads the prepared
tuple at0300456C, using byte+2 for horizontal output through08000F2C.

The actual unchanged six-instruction horizontal writer is:

| Address | ARM instruction |
|---|---|
| 08000F2C | LDR r8,[pc,#74] — literal030012B8 |
| 08000F30 | STRB r0,[r8] |
| 08000F34 | MOV r9,#04000000 |
| 08000F38 | SUB r10,r0,#8 |
| 08000F3C | STRH r10,[r9,#14] |
| 08000F40 | BX lr |

At actual69934 the next-display pre-hook has R5=0300456C and tupleB7700C70,
so pending byte+2 is70. At the failure hook085E743C, the captured registers
are R0=70,R10=68,R8=030012B8,R9=04000000,LR=085E743C and reportedPC=085E7440.
The callback convention reports hook address+4. The final outer IWRAM also
contains shadow030012B8=70 and prepared0300456E=70. This supports the expected
native byte shadow and halfword value68; it is not a directly captured
hardware write transaction in the old observer.

The observer reads04000014 through the `System Bus` domain and demands that
its value equal68. BG1HOFS and BG1VOFS are write-only. Official mGBA0.10.5
`GBAIORead` routes both through its write-only cases to `GBALoadBad`, rather
than returning the stored offset. See
[mGBA0.10.5 IO implementation](https://raw.githubusercontent.com/mgba-emu/mgba/0.10.5/src/gba/io.c),
lines850..902. This establishes the readback API limitation; it is not a
byte-for-byte audit of the local packaged core binary.

The actual trace agrees with that limitation: adjacent horizontal/vertical
reads fluctuate together throughC000,000E,4710,5FFF and66BB at unrelated
instruction hooks. These raw readings are retained, but cannot establish
the current scroll latch. The failure line itself records actors/registers,
not the rejected bus value, so that value is not invented here.

A minimal new observer can preserve every existing IRQ condition and add
paired execution hooks around the branch-free STRH:

1. At08000F3C, with a pending next-scroll call, require LR=085E743C,
   R0=pending,R8=030012B8,R9=04000000,low16(R10)=low16(pending−8), and
   shadow030012B8=pending. Record a single pending call witness and actual
   address04000014,width2,value operands.
2. At08000F40, require the matching witness and unchanged call/operand
   identities. Reaching this immediately following instruction establishes
   passage through the intervening STRH. Mark the witness completed.
3. At085E743C, require the completed witness, R5=0300456C and shadow=pending,
   then clear the witness. Do not assert a System Bus readback from04000014.

This proves observed native execution/store operands and RAM shadow, not
render-latch contents or displayed pixels. A memory-write callback is not
required for this adjacent straight-line pair. Fresh evidence remains
necessary; the old failure must remain frozen. No ROM, observer, main,
capture, Git or emulator was changed by this reviewer.
