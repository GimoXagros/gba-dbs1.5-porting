# Train source shake contract — 2026-11-17

The remaining component previously called a Train **hazard** is a four-update
BG0 vertical shake. Its reviewed body has no actor, damage, or collision-list
effect. The initializer is called by source Train initialization, but a positive
entry to the shake update has not been established. Adding it to every native
Train update now would introduce an unproved source control-flow edge.

This is a narrow follow-up to `train-graphics-repair.md`. Existing background,
collision, palette, resource, and native movement-helper proofs are retained;
their suites and runtime routes were not repeated. No ROM or main builder was
changed, no RAM allocated, and no emulator started.

## Five actual state fields

Source SHA-256 is
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The source segment is DS=1000, not the buffered display segment0300.

| Field | Producer | Consumer and lifetime |
| --- | --- | --- |
| 0376 word | 76B480 clears whole word; B3E6 sets bit0; B46D clears bit0 | B3D5 chooses idle countdown or active shake. Other bits are preserved by updates. |
| 0378 word | B483 initializes0; B3EE resets0; B448 increments; B460 loads delay | B3DD decrements while idle and starts when signed result is negative. During active shake B415 tests bit1 and B44C compares unsigned against4. |
| 037A word | B486..48C copies source0060 &001F | B3F4/B3F8 index amplitude table; B3FC/B400 increment and mask001F. |
| 037C word | B48F..495 copies source0062 &002F | B456..45D index delay table; B463/B467 increment and mask002F. This is **not modulo48**. |
| 037E word | B406/B409 select amplitude on idle→active transition | B40F reads on active updates. Initializer does not clear it, but the normal zero-status/zero-countdown entry writes it before its first read. |

Amplitude table raw76B312 contains32 words, each0100/0200/0300.
The following delay data at76B352 contains64 words, each10/15/20/30.
Mask002F permits only indices0..15 and32..47. Increment wraps15→0 and47→32;
neither the middle16 words nor the last16 words can be selected by this
initializer/update chain. Preserve that mask if an active port is later justified.

The initializer at68F7:2507/raw76B477..B49A is called at77DAA0, after both
Train backgrounds load and before the stage's initial BG1 positioning.
It preserves AX/DS and makes no RNG call. The seeds are already-retained menu
random words: source780734/73D calls4FFF:1CB5 and stores ES:config+12/+14
(config1000:004E →0060/0062). The existing native counterpart
08091180/188 calls08012600 and stores config03002310+12/+14, i.e.
03002322/24. This supports seed-input correspondence, not equal random sequences.

## Complete bounded update behavior

The near-return body is68F7:2462/raw76B3D2..B476. In idle state it decrements
the word countdown. A negative result starts a shake, zeroes the active phase,
selects an amplitude, and advances its table index. Thus the first invocation
after the actual initializer would start immediately, if this body were called.

Each active invocation selects BG0 source01CE, writes Xdelta+1C=0 and
Ydelta+1E=selected amplitude, and calls the existing background movement service
4FFF:3367. Modes are4,4,1,1 for phases0..3. It then copies BG0+1A/+1B to
0300:003C/003D. After phase3 it selects a new idle delay and clears the active
bit. There are no additional callbacks, object constructors, or actor writes.
The minimum prospective translation is therefore one initializer, one update,
and two immutable tables, using an existing movement service. Its invocation
site remains unproved.

Proved native endpoints are BG0 owner03002338, movement08013DD4, and the
BG0 scroll shadow0300456C/6D. Native080C8E18..28 loads that shadow and calls
08000F5C/08000F74; the paired BG1 calls consume+2/+3. Native08015D60..68
also clears the same eight-byte shadow. These are display endpoints, not owners
for the five private words.

## Reachability discriminator

The source stage update dispatcher at7693FD calls the near-pointer table at
7693AC. Its stage8 row7693BC is195C, resolving to76A8CC. That complete Train
update queues its scanline callbacks, calls76A9BC (horizontal BG1 scroll),
calls76A952 (palette), and returns at76A921. Neither call reaches the shake.
The separately reviewed stage8 display-dispatch row at768F80 resolves76932E,
which calls8347:02B6 and conditionally5EEA:0AD8; it does not name the shake.

The assertion script verifies no E8/E9 direct entry candidate in the surrounding
128-KiB physical window, including16-bit offset wrap; no9A/EA far entry candidate
in source code bank700000..end, including equivalent segment:offset addresses;
and no2462 pointer word anywhere in the64-KiB68F7 window. The only2462 word in
the source code bank is768B50, outside that segment, in a different table.
The preceding routine returns at76B311 before the192 bytes of shake tables,
so the shake does not inherit fall-through from that routine.

This evidence bounds the missing edge; it is not an exhaustive proof that no
computed or aliased execution can enter the body. The actual initializer's
presence alone is insufficient to make that claim. Do not change the existing
graphics omission into a gameplay fix based only on the routine's existence.

## Ownership and the one next witness

There is no established native private owner for these ten bytes. Source
display copying768FD7..FEB ends at1000:0370 (exclusive), so0376..037F are
outside that buffer. The native400-byte bridge03002478→03004578 and the
known0330→03002568/03004668 pair do not extend to these private fields.
Known0370→0300260B and0372→03002608 mappings already show why adjacency is
not a valid allocation rule. Neither03002568 nor the0300456C display shadow
can be borrowed as persistent shake state.

The next discriminating witness is **actual source execution at68F7:2462**
with predecessor/call site, CS/DS, stage index, and0376..037E. Observe the
initializer first and do not insert a call or synthesize guest state to obtain
the entry. A real entry identifies the scheduling/lifetime owner; the translated
graph can then be attached to its native counterpart and given independently
proved storage. If no entry is seen, report only the bounded observation—do not
invent a native shake to satisfy the old hazard label.

`tools/analyze_train_shake_contract.py` validates exact initializer/body bytes,
actual stage8 table/epilogue, masks/table domains, and the bounded entry-reference
checks. Its result is `build/train-shake-contract-20261117/source-contract.json`.
PASS means the source contract above matches the pinned ROM. It does not prove
runtime reachability, native storage availability, or full Train parity.
