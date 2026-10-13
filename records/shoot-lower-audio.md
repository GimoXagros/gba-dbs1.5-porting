# Shoot CF and D1 native audio resources

The lower rule graph requests source CF/type2 and D1/type1. They now use the
existing commercial M4A engine with native IDs `5D` and `5E`. No CPU/APU
emulator, save file, audio playback or new sound driver is involved.

## Fixed inputs and output

`build_shoot_lower_audio.py` accepts only committed v51 candidate
`726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`
and the three original ROM hashes specified in `ASTRA_HANDOFF.md`.
Its output `build/shoot-lower-audio-20261013/audio.gba` is
`0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103`.
The independent verification report is
`D177C343BCA6776520048CDA97D584EE539A005577E8CA5B7773E494B2A61AFE`.

| Resource | ROM offset | Bytes | SHA256 |
|---|---|---:|---|
| CF native song | `5CA000` | 169 | `211F1717B4F80EF9D34976833E36142ED2257AE396D6F7E3BF44B5DEEFD2E92C` |
| D1 native song | `5CA100` | 144 | `C26570718A39C73572FB9C7994928370607E431F51546E300DE51EAC593D238B` |
| Three commercial voice records | `5CA300` | 36 | `D20A562550E6E6209BC0DB2C31482A5EE23F2A5E3055E51CEB9C552D0D909C65` |
| Two appended song-table entries | `5BA6E8` | 16 | `842B1544B651EFC0AF5FBB30B5F56EADEE6A4C111A1067E04E17AB0574678F59` |

All writes require unused FF bytes and no preexisting aligned pointer or ARM
branch into the actual intervals. The existing song table through ID5C is
unchanged. The full-ROM difference is exactly 365 changed bytes within those
five Expected Writes. The neighboring scene and lower-rule code do not overlap.

## Source score and envelope evidence

CF is the complete 42-byte score at raw `3F891A..3F8944`, SHA256
`FE69FBE714FB625FA6939A6DE5BECF9B18E2C5882BCF57B442313582580A87C4`.
It has a seven-tick leading wait followed by seven pairs of three-tick rests
and seven-tick notes. The packed notes are `13,16,19,20,23,26,29`; duration is
77 source score ticks. D1 is the complete 38-byte score at `3F895E..3F8984`,
SHA256 `B13EB3A8D4BC8CCCEB1323193C955F2D680F9900A288E6A7D3D0EE6A787B4042`.
Its five notes start at 0, 8, 24, 32 and 44 and last 8, 16, 6, 8 and 6 ticks;
the final end is 50. Native tempo follows the existing commercial value75.

The command consumers at `75445D..7547B3` distinguish packed notes from rests
by the low nibble, reset envelope age at each note, and select envelope mode
and period from the C-command. The envelope consumer `753E80..753F28` computes
four successive quotient bits. For these bounded notes this is
`floor(age*16/period)`. It indexes the high nibble of
`754DA0 + mode*16 + index`, combines that with source amplitude, and reads
the amplitude LUT at `754867`. The generator emits changes in native VOL for
each source score tick. Its mathematical implementation is checked against
an independently written four-step shift/subtract calculation.

D1's three decaying notes have source amplitudes
`15,15,13,11,8,8`; `5,5,4,4,3,3,3,3`; and `2,2,2,1,1,1`.
The reused voice records have their ADSR fields neutralized, so a second
native envelope does not unintentionally modify these finite source curves.

## Commercial analogues and fidelity limits

For source wave00, retail WSC A9 at `2D83B6` contains A2=00 and the matching
native request at `08370AA8` selects ID4D. Its track at `38753C` selects
voice17 from `37E8E0`. For wave04, retail WSC93 at `2D81DC` contains A2=04;
the corresponding request at `0836EFA4` selects ID38 and the track at
`387194` selects voice8 from `37EAA8`. Matching subsequent animation/event
operations provide the request lineage, rather than arithmetic ID offsets.

CF's wave02 uses the same bounded commercial voice14 analogue as the prior
CE reconstruction. It is not proved to be an exact waveform match. A3 is
represented by native MOD with pitch modulation; source hardware modulation
and CF's conditional A1 sweep are not proved equivalent. Right pan retains
the earlier bounded reconstruction convention, but source stereo mixing is
not yet established. These are explicit audio fidelity limits, not a claim
of complete or audible source parity.

`verify_shoot_lower_audio.py` imports no generator. It checks the immutable
sources, source command consumers, commercial voice/request lineage, complete
native score decoding, every onset/duration/pitch/voice/amplitude, table and
voice pointers, Expected Writes and full-ROM diff. Five mutations (song table,
pan, timbre, hidden ADSR and voice pointer) are rejected. No runtime or
audibility acceptance is inferred from those static checks.
