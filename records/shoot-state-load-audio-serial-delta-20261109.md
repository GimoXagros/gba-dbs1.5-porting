# Exact native load/resave differences

Read-only diagnosis of the twelve native bytes differing between genuine
`bizhawk-gba-shoot-entry-20261109-b/stage7-hp1.State` and
`bizhawk-gba-shoot-entry-replay-20261109-a/restored.State`, beyond the expected
ROM CRC. These bytes are functional audio and serial state, not padding.
No State, ROM, verifier acceptance rule, or emulator state was changed here.

The source is the exact BizHawk mGBA submodule revision
`94b1578f8545d8ad17bb4036dba908612d5731e2`, not current upstream.
`gba-serialize.c` deserializes IO before calling `GBAAudioDeserialize`.
The latter restores PSG counters first, then invokes the SOUND1/2/3/4
frequency-register writers. Those writers run the affected PSG channel at
the current timestamp before setting its frequency/control values.
[Pinned GBA audio deserializer](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gba/audio.c#L494-L505).

## Exact audio arithmetic

The master cycle value is `335EA670` and CPU cycle offset2, unchanged across
the load/resave. The source PSG timing factor is4. These field changes follow
the native lazy-update formulas; they do not require a game frame to advance.

| Native field | Before | After | Meaning |
| --- | --- | --- | --- |
| 130 envelope word | 00005040 | 00805040 | Square1 duty index0 to4 |
| 140 lastUpdate | FFD58E0E | FFFF8E0E | Relative time -2781682 to -29170 |
| 144 envelope word | 00E00040 | 00800040 | Square2 duty index7 to4 |
| 150 lastUpdate | FFD147AE | FFFFC7AE | Relative time -3061842 to -14418 |
| 17C noise LFSR | 00002BB7 | 00007A94 | Noise sequence advances28 steps |
| 184 noise lastEvent | 335EA2EB | 335EA66B | Advances896 cycles |
| 188 noise nextEvent | 335EA32B | 335EA6AB | Serialized lastEvent plus64 |

Square1 executes84 periods of32768; square2 executes93. The duty indices
advance modulo8. These formulas exactly reproduce both duty words and both
relative timestamps. `GBAudioRun` explicitly updates a square channel when
called with that channel's dedicated mask, even if its envelope is dead.
[Pinned square update](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gb/audio.c#L479-L505).

Noise needs an important qualification: advancing14 steps of the *restored*
64-cycle period would give LFSR0326, which does not match the saved result.
Advancing28 steps of the prior live32-cycle period gives7A94 exactly and
advances lastEvent by the observed896 cycles. Reset initializes noise ratio0;
`GBAudioPSGDeserialize` restores its LFSR/timestamps but not the ratio.
`GBAudioWriteNR43` runs the channel before installing restored ratio1 from
SOUND4CNT_HI=0001. Re-serialization then computes nextEvent using the restored
64-cycle period. Thus the observed noise result is explained by the actual
load ordering and prior live controls, not a generally harmless re-encoding.
[Pinned noise register write](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gb/audio.c#L348-L352),
[pinned noise update](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gb/audio.c#L579-L638).

The captured three PSG envelope volumes are zero. That limits the immediate
audible consequence, but does not turn their oscillator state into padding
or prove identical subsequent audio under all input sequences.

## RCNT is a separate restore asymmetry

Native offset534 is IO offset134, RCNT. Its0001 to0000 change is SC bit0,
a real serial clock/input level. Captured SIOCNT=200F selects multiplayer.
The IO loader restores SIOCNT through its special-register direct assignment,
then calls `GBASIOWriteRCNT`. In non-GPIO mode that function preserves live
RCNT bits0..3 and takes only bits4..8 and the mode bits from the saved value.
It therefore cannot restore saved SC=1 over a fresh live SC=0.
An ordinary multiplayer SIOCNT write fills SC, but the load path bypasses that
writer. `GBAIORead` returns live `sio.rcnt`, which explains its next serialized
value. This is a functional serial-register restore difference.
[Pinned IO load](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gba/io.c#L1038-L1076),
[pinned RCNT writer](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gba/sio.c#L122-L140).

A narrow literal census of D0 finds its sole exact04000134 constant at raw
37B10C; the bounded Thumb reference at37B046 uses it for a write at37B048.
This is not a whole-game absence proof for indirect IO reads. No claim that
the serial delta is irrelevant to every game path follows from this census.

## Acceptance consequence

Retain the strict failed full-Core equality result. A same-D0 fresh-host
load/resave with no frame advance is the appropriate control for separating
these loader effects from the five-word ROM repair. Matching that control
would establish patch independence for this observed restore, not literal
identity to the original checkpoint or a permission to mask arbitrary bytes.
Healthy Shoot activation and checkpoint-restoration fidelity remain distinct
claims. The control was not run by this source diagnosis.

Fetched source SHA256 at the pinned commit:

- src/gba/audio.c: `0BD5DC474767C048D995E9F773CCF9E0E0F90399322FEA611FF9AA4BFB81DCDE`
- src/gb/audio.c: `41536AE04B3345154D83F63F044FEFBBC4957F58C16B20A5ECE7776CE95A09C6`
- src/gba/io.c: `1FB6080312BE49BCBD934CBCC0BFD7C8BB69B850D26EE4A933E48EE78D6FAF81`
- src/gba/sio.c: `617058EA2712953B5058810288815EC8A415EF28D9EC28D4D8D50943EE0A0703`
- include/mgba/internal/gb/serialize.h: `FE297E1F216F365B73EBC6360D79BC73BC701343223D3CDB15EEB01DBE5368BF`
