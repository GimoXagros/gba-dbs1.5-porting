# Iraira floor launch — bounded native implementation

This layer changes an actual fighter floor dispatch entry that previously
returned immediately. It implements the WSC1.5 Iraira launch trigger, its quiet
initial/wait phases, and its eight finite sound phrases using the existing GBA
engine. It does not claim complete new-character move parity.

The fixed predecessor is Train repair
`96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530`.
`tools/build_iraira_floor_launch.py` produces
`build/iraira-floor-launch-v2-20261016/current-candidate.gba`, SHA-256
`7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470`.
Its manifest SHA-256 is
`B3F62F29113553D032964F382584C9A4B93B208F4902ED44EB26B438D276A4D0`.
The independently authored `tools/verify_iraira_floor_launch.py` passes.
Its report `build/iraira-floor-launch-v2-20261016/verification.json` has
SHA-256 `3E9CC0CD8498605C34DD8904663211875107F36D8FD5DE29F8140372DF7699B0`.
No emulator was launched by this workstream, and no supplied save was accessed.

## Why the collision repair alone was insufficient

The source floor collider writes the classified first cell word into fighter
`+4A`; the actual native collider writes it into `+5A`. The subsequent source
fighter dispatcher is `4090:2309` at raw `742C09`, with its 16-word table at
`742C1F`. It selects `(fighter[4A] & 003C) >> 2`. Entry 14 is `4090:25BF`.

The corresponding native dispatcher is `083549E0`, with 16 pointers at
`083549FC`. Entry 14 at raw `354A34` was `08354DD4`, a return. The added-stage
collision layer fixed the separate collider classification table and safely
produces this class. This layer changes only the later fighter class-14 pointer
to `08627A00`. The other 15 entries and the two collider dispatcher tables stay
byte-identical to the predecessor.

## Source trigger and proven native owners

The complete trigger and eight rows are source raw `742EBF..742FC9`, SHA-256
`E0274770ABE0046C029789753EA0EE8E938CF0FA97CDA4E3F4FFD96AF80B0EC4`.

The emitted trigger preserves this order:

1. Return when fighter flag `+6` bit `0001` is set.
2. When flag `+8` bit `0040` is set, assign the already-proven abort callback
   and return. Source `5FFD:258A` corresponds to native `0836CE38`, as retained
   by commercial class 5 at `08354CB8`.
3. Store flag `+8 |= 8000`.
4. Read the existing match timer, mask its low three bits, and select one of
   the eight sounds. Source `1000:03CE` maps to native `03004500`, proven by
   the commercial timer producer at `080D17F8` and the HUD consumer at
   `08373D34`. The GBA timer uses 60 Hz units; this implementation uses its
   actual low three bits and does not invent a second 75 Hz clock.
5. If fighter flag `+6` bit `1000` is set, submit the request only if the
   existing request slot is free. Source `0C00:390E` maps to native
   `030022F0` through the actual helper `080D15C0`. Source raw
   `742EFD..742F05` contains `2E8B5702 2E8B5F02`: both arguments read row
   `+2`, so both are **1**, despite the unused row `+4` containing zero.
6. If flag `+8` bit `0400` is set, call the existing presentation release
   helper (`4FFF:2A16` / `08012BBC`) and then clear that bit.
7. Assign the new private initializer and enter native `08354D20`. That
   existing continuation selects animation `0B` or `28`, then stores native
   launch values `FB54`, `14`, `0F`, `0` into `+A0/+A2/+A4/+A8`, in order.

These parameter conversions come from actual common launch producers, not an
inferred field adjacency. Source raw `742DCA..742DE2` equals the commercial WSC
ancestor `392AE2..392AFA`. Native `08354C24` and `08354D4C` use the matching
fields and values. Source `FC43/0010/000C` becomes the commercial native
`FB54/0014/000F`. Source `+92 = 0` is the class-5 native `+A8 = 0` path.

## Private initial/wait phases and native continuation

Source callback `668E:207B` is raw `76895B..768B4D`, SHA-256
`3C28DB2780AA08B3FBEF1BC6B1AFBD802CD36FE22B8F0BB13AC86AA45C9ECC6D`.
Its initial state matches source common jump `668E:1E51`. That common initial
prefix also equals commercial WSC raw `3ADBF7..3ADC1A` and corresponds to
native `08357670`.

The private initializer at `08627B00` sets the native state byte `+6E = 3`,
clears `+A6/+42/+44/+46/+48`, sets flag `+6 |= 1`, and calls existing effect
constructor `0835972C` with effect `8005`, native X/Y, and parent. It assigns
`08627C00` and calls it immediately, matching source fall-through behavior.

The effect constructor had a vertical-flag adapter at
`083597D0 -> 08584940`, but it read the progression field directly. That was
incorrect when the existing temporary character route selected Iraira while
progression remained 1. Independent review caught this in the first candidate.
The old candidate `A822BF92...` and its builder snapshot remain preserved in
`build/iraira-floor-launch-20261016`; they are not the final implementation.

Both actual source effect consumers are now repaired. Source raw
`786C5C..786C7C` reads source stage `1000:004E+0E` and sets presentation flag
`2000` only outside stages 9 and 10. The second producer at
`781BEF..781C0F` has the same condition before ORing its local flags. Their
native caller sites are `083597D0` (value register r8) and `08359568` (r0).
The new adapters at `08627D00` and `08627D80` first recognize actual stage
11, then otherwise call the exact existing logical-stage getter `080D1C78`.
This preserves Shoot's dedicated stage-11 state while making both ordinary
effects use the same stage as current stage setup.

The logical getter's full implementation at `08582C40` is guarded: character
`0B/0D/0E` selects stage `10/8/9`, otherwise it returns progression. This is
the already-existing temporary route; the adapters neither alter that policy
nor write progression. Only stages 9 and 10 suppress OR `2000`; no existing
bit is cleared. Incoming values, all other registers, SP and LR are preserved.
Native `083597DC` and `08359588` overwrite condition flags before their next
conditional consumers, so the temporary comparisons introduce no new flag
dependency.

The private wait callback tests presentation `+0A` bit `2000`. While clear,
it enters the existing frame-advance block at `0835778C`. When set, it applies
the common age/flag condition: fighter `+4` bit 1 clear and native age byte
`+70 >= 24` selects `FDD4/14/0F`. Source age `+5C >= 30` and velocity `FE43`
have the same commercial producer/consumer lineage, including source
`74348F..7434AC` / old `393064..393081` and native `08352E1C`.

All complete-wait paths then enter `0835774C`, which moves the launch values
to the existing vertical velocity/acceleration fields, sets animation `0C`
or `29`, and assigns the native common ascent callback `083577A8`. This
deliberately bypasses native `08357724..08357748`: its voiced request is
present in source common jump `1EBE..1EF5`, but absent from source Iraira
`207B`.

The subsequent native ascent/fall continuations are retained. They provide
the proven common motion and existing landing services. WSC1.5's later
character-13 aerial branches to `8522:0577` and `8522:02BD` have no verified
native adapter yet. They remain an explicit new-character move parity gap.

## Stack and register boundary

The class-14 trigger is a dispatcher target, not a new public function. Its
live stack is the native `08354910` saved `{r1,r3,r5,lr}`. It uses `r4` as the
fighter and `r5` as the presentation. Early exits enter the existing native
epilogues; the ordinary path enters `08354D20` and returns through
`08354D6C`. All temporary native-helper argument pushes are balanced before
that continuation. The source timer index uses saved `r1`; the native request
helper's existing `r6/r7/r8` clobbers are retained under the same native caller
contract.

The initializer and wait callbacks each save their own LR. Both wait
continuations reach the existing `08357974` LR pop/return. Calling the wait
callback from the initializer therefore returns through the private init's
own LR pop, as the commercial initializer does. No new writable memory owner
or scheduler contract is introduced.

The r8 effect adapter saves `{r0,r1,lr}` and keeps the incoming value in r1
while the logical getter clobbers r0/r8. The r0 adapter instead saves
`{r1,r8,lr}`. The exact getter preserves r1. Each adapter copies r1 back to
its output register, restores its saved registers, and returns to the
original immediate halfword store. This preserves the live r1 presentation
pointer at both call sites.

## Eight finite native scores

Source IDs `BE..C5` resolve through the actual six-byte sound table at
`3F0000` to eight 26-byte payloads starting `3F8746`, stride `1A`.
Their three note onsets are 0, 10, 20, each note lasts 9 ticks, and two
one-tick rests yield 29 total score ticks. The right-volume sequence is
15, 6, 2. The first packed notes are `29,2B,30,32,34,35,37,39`; the last two
notes in each phrase are one packed hexadecimal step higher (`+10`, one
octave). This is converted through the already-established bounded native
score policy, with explicit key, volume, duration, and pan events.

| Source | Native | Native first key | Native last two keys |
| --- | --- | --- | --- |
| BE | 64 | 69 | 81 |
| BF | 65 | 71 | 83 |
| C0 | 66 | 72 | 84 |
| C1 | 67 | 74 | 86 |
| C2 | 68 | 76 | 88 |
| C3 | 69 | 77 | 89 |
| C4 | 6A | 79 | 91 |
| C5 | 6B | 81 | 93 |

Native song-table entries `00..63` are copied unchanged from `08683200` to
the new 108-entry table at `08686800`; the eight entries are appended.
The five actual lookup literals at raw `37C2A4/37C2D8/37C324/37C378/37C3AC`
are updated. The current three-voice array at `08683520` is reused and
guarded against its commercial analogues. The scores preserve the bounded
note/timing/volume/pan policy; WonderSwan timbre, native noise-frequency
parity, and audible parity remain unclaimed.

## Storage and verification boundary

Code reservations are raw `627A00..628000`, with actual blocks of 128, 116,
and 72 bytes at `627A00`, `627B00`, and `627C00`, plus two 60-byte effect
adapters at `627D00` and `627D80`. Audio reservation is
`686800..687000`. The originally considered `684000..684800` was rejected
because it had two ARM branch-like incoming encodings.

The accepted reservations are all `FF` in the fixed Train predecessor and
have no whole-ROM unaligned encoded-pointer, aligned ARM B/BL-like, or ARM
PC-relative load/store-like incoming encodings. Each actual write has an
Expected Write guard; the full-ROM inverse restores the predecessor.
There are 1,861 changed bytes. Static validation does not establish runtime
or audible success; those remain separately reported by the root workstream.

The separate verifier binds all 102 emitted instructions and their literals,
24,576 effect-selector ABI cases, 256 trigger/busy-request cases, 1,024 wait
cases, and the nested initializer/wait return path. It independently decodes
all eight scores and confirms all 100 prior song rows are unchanged. It also
passes 18 negative mutations, the complete-ROM inverse, and the allocation
ownership checks without importing this builder.
