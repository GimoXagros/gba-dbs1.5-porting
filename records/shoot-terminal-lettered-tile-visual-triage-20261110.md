# Read-only terminal lettered-tile visual triage

The repeating lettered/MONSTER-like boss texture is **not newly introduced
by280D or the corrected scroll observer**. It is already visible in the
original WSC capture during active Shoot and during boss disappearance,
and in the earliest available native healthy checkpoint before this
terminal attempt. This narrow triage does not declare the texture correct,
approve overall visual parity or reopen the closed terminal execution gate.

## Existing original-reference pictures

The following existing pictures were viewed directly and rehashed against
their finalized launch inventories. No new emulator was run.

- `build/bizhawk-wsc-healthy-shoot-terminal-20261109-a/shoot-active-frame.png`
  visibly has green repeating lettered boss strips before the lethal hit.
  SHA256 `D357DA0B7FC3A25AE4C3FA3FA5FAA8C86C978D40F38C948D5271E74FC8FE73F4`.
- The same run's `final.png`, core100570, has the lettered texture over
  the boss during terminal disappearance.
  SHA256 `6D721039355259333B442B75A15823297846C495DCD0374D6A197662FEBC328C`.
- `build/bizhawk-wsc-terminal-tail-20261109-a/first-potential-visible.png`
  likewise contains it. The existing scalar record identifies event100571,
  outer picture100572, old_k114; it explicitly does not read actual LCD line.
  SHA256 `CFC03D0297CBC3413BAF27802E22765077D1BB0A91C331497FC9DC04E7F261F4`.
- That continuation's `final.png` is black at mode8/core101035.
  SHA256 `E8C58FD046279C6B80395A565BF1971A1DF1B6F9ABAAB46DEBA2B99ABCCC83B5`.

The original healthy launch is92EFF38611C794E82865B1EB5E52A0CE986942D5E27CB67D5986BEFE30E922EC;
the neutral tail launch isA40BFD5ABDE950B42A806E8B9EAFA0B2CF729A4CD59CFF1C5476387BD9D79939.
These are original WSC emulator observations, not physical-hardware tests.
The references and native trial differ in game frame/phase/counter, HUD
and canvas; no source/native pixel-perfect phase alignment is inferred.

## Native predecessor comparison

Current280D `00-before.png` already contains the green lettered pattern.
It is byte-identical to the existing genuine healthy activation picture
`build/bizhawk-gba-shoot-entry-replay-20261109-a/13-healthy-activation.png`.
Thus the pattern predates the terminal lethal hit and all subsequent280D
display-consumption changes.

The current native00/13/17 pictures were compared with matching named
captures in each frozen FF3A palette,46B3 owner and280D display-epoch run.
Every PNG, complete VRAM and complete OAM buffer is exactly equal:

|Snapshot|PNG SHA256|
|---|---|
|00-before|5D63E399EBBD2A1C93512F13501D6093EB83A587E949F05F93371083602CAEA8|
|13-actor-85BF200|E06E35621D06F4FAB73103B172582F7AEB67EDECC48679C31DBDFF25A4091E6D|
|17-phase-85CD510|D34FBA2D185F60CCC7CBE59767758D78124006022A7A889A0126751BD2096E58|

Current18-irq-queue-selected is also exactly equal to the prior280D
display-epoch picture, VRAM and OAM; that equality is frozen in the native
terminal audit9F909134. The old46B3/FF3A runs have no same-frame69934 IRQ
capture, so their later bounded image is not substituted as a matched18
picture. The first known new execution divergence is guard acceptance at
69933; it is not a first appearance of the lettered tile payload.

## Tile and layer ownership

At native healthy00, serialized mode0 display state isDISPCNT3F40,
BG0CNT1F02/BG1CNT1E03/BG2CNT1B01/BG3CNT1A0C. BG1 therefore reads text map
0600F000 with character base06000000; its healthy scroll is104/8.
Using these stored inputs,298 black pixels in the visible letter band
x10..229,y96..111 reconstruct from a nonzero BG1 texel while BG0/BG2/BG3
are transparent at those sampled pixels. The complete healthy OAM has
only16 active, non-affine8×8 entries; their lowest row is71. None overlaps
that letter band. This locates the pattern in the background tile/map
pipeline, rather than an OBJ/OAM overwrite.

One explicit witness is native pixel17,107: BG1 map halfword0600F39E is
1777, selecting character377 at06006EE0 with horizontal flip and palette
bank1. Its relevant nonzero color1 is black and matches the PNG. The
32-byte tile SHA256 is
`2CCAED6E4B260A4DDD7C99FEC36CE1E600912D75F53C1B0805445C882F33FE80`.

That exact packed tile equals lossless4-plane conversion of original WSC
active RAM tileAEE0. Seven sampled letter-band tiles independently match
source RAM addresses native+4000. More strongly, the **entire16KiB native
character range06004000..06007FFF** equals lossless conversion of original
active WSC RAM8000..BFFF. The source active RAM itself matches its frozen
launch inventoryA6F8F2CDA04A1333AB5A9490BCE8FBE40C3B0215B141D3810317368A661EB245.
Conversion used the existing `build_zeed_boss_assets.py:convert_tile`
four-plane bit extraction; that file SHA256 is
0B4F4DCE0A7D2D873B2148F90C14B897DE1084D2EF9AA3AA3244518252086EE6.
No ROM or asset bytes are redistributed in this record.

The native entire0000..7FFF character-bank hash remains
013FE6DAA410EBCCF083AFBE8F20F127B4CA2F920E3F7EF9757B93F069BF3180
at00/13/17/18/20/21. The boss-map nonzero halfword counts atF000 are414,
418,418,255,0,0 respectively. Boss disappearance therefore changes map
coverage while these tile pixels remain stable. At20/21 the boss map is
clear and the lettered boss disappears. This is finite captured-state
evidence, not an instruction-time scanline reconstruction of IRQ frame18.
The lower16KiB character range was not equal to the corresponding source
conversion, so no whole32KiB/source-memory parity claim is made.

## First-divergence boundary and remaining scope

No new letter-pixel input divergence was found between the selected native
predecessors and current run. The earliest inspected native and original
active references already carry the pattern; there is no captured clean
predecessor-to-lettered transition to diagnose as a new regression. This
record does not explain whether the original texture is an intentional
asset, inherited source issue or another earlier condition. It does show
that changing280D terminal code or OAM to erase it would be unsupported by
this evidence.

The closed terminal flow audit remains9F909134. Overall screen-break
fixing and phase-aligned WSC/native visual comparison remain separate.
Only this new record was written; existing captures, code, ROM, main build
and Git were unchanged. No emulator, guest write or broader visual audit
was performed.
