# Source SRAM tail boundary

Recorded 2026-10-13. This is a positive save-record layout proof and a bounded
address inventory. It does **not** prove that the source writes are dead and
does not authorize mapping them to the ordinary fighter HP cache. No game,
CPU, emulator, or save file was executed or read.

Source raw `747CD6..747CF0` sets ES to `1000` and clears `0660`, `3CD8`, and
`3CDA`. The last two linear addresses are `13CD8` and `13CDA`. The ordinary
fighter cache at `0C00:3CD8/3CDA` occupies `FCD8/FCDA`, a different region.

## Positive serialization boundary

Source `85DE:02EF`, raw `7860CF..786147`, loads CX=`E8` after its initial
helper calls. The read branch copies exactly `1000:0076..015D` into
`0C00:392C..3A13`. The write branch copies the same count in reverse. Its
eleven valid mode-table entries lead to only three destinations (`033C`,
`0346`, and `034F`), none of which changes CX. Startup `85DE:007B` validates
the record signature and clears the same `E8` bytes in the internal buffer
when initialization is required.

This positively excludes `3CD8/3CDA` from that serialized record. It does
not establish that no other work-state reader can observe the two words.

## Finite address inventory

The immutable fixed-ROM range `700000..800000` contains no byte-aligned
four-byte `offset,segment` pair whose linear address is `13CD8`, `13CDA`,
`1BCD8`, or `1BCDA`. It contains no `BCD8` or `BCDA` operand-byte candidate.
The latter two addresses cover the simple upper-half aliases under the
32 KiB SRAM mapping; arithmetic and inherited segment values still require
separate proof.

There are 690 byte-pattern candidates for an immediate `1000` load followed
by a segment-register load. Only 684 load that same register into DS or ES.
The other six use a different register in a paired segment setup; their
addresses are included in the JSON. This denominator does not include
nonadjacent assignments, segment copies, stack-restored segments, or
segments loaded from arguments. It must not be presented as an exhaustive
segment-flow proof.

The corresponding scan of immediate segment values that could, with some
16-bit offset, reach the SRAM targets also identifies `0400`, `0800`,
`0BDE`, `0C00`, `0FE0`, `0FEE`, `0FF0`, and `1073`.

The `1073` owner is a background-animation command/transfer area, not the
audio channel work state. Its initializer at `753B9E..753BC6` zeros relative
`0000..0169`, or SRAM `0730..0899`: 32 six-byte records, a count at `C0`, and
42 four-byte transfer entries at `C2`. That initialization extent does not
by itself bound the subsequent count or indices. The generic reader at
`753BC6`, record/queue producer at `753C4C`, and seven fixed record readers
are recorded separately. The target words would
require relative `35A8/35AA` or `B5A8/B5AA` under segment `1073`.

## Stage-11 background owner

The generic record reader at `753CDD` obtains both its starting record index
and loop count from individual ROM bytes. Records have six bytes. Even the
largest byte values and a zero count wrapping through 256 iterations keep
all record accesses inside relative `0000..0BF9`; this is below the target
offset `35A8`. This is a width-based bound on the record accesses, not a
bound on the separately accumulated transfer queue.

The complete-ROM direct far-call census finds seven calls to the queue
producer `4FFF:3C5C`, six to its flusher `4FFF:3BD6`, twelve to its record
writer `4FFF:3C26`, and two to its initializer `4FFF:3BAE`. The report lists
every site. An all-byte scan of the complete `4FFF` code-segment window
finds no near `E8/E9` encoding targeting these four entries. Indirect
function pointers and inherited segment flow remain outside that census.

The two actual stage dispatchers read `1000:005C`. For stage 11, the
preparation table selects `68F7:03F7` (`769367`) and the update table selects
`68F7:2067` (`76AFD7`). Neither calls the generic animation producer, record
writer, or queue flusher. Preparation calls the bounded display helper
`4090:0000` and palette dispatcher `8347:02B6`; its stage-11 table selects
`8347:082E`. Updating calls `5EEA:0E0B` and the local palette-state updater
`68F7:226B`, which uses SRAM `0174..01B3`. The complete decoded local call
edges are pinned in the analyzer. `5EEA:0E0B` imports `4FFF:3367`. Its actual
two 2-by-3 BG descriptor sets select twelve ROM ranges `49C4D0..49F410`,
each `3F0` bytes. The analyzer checks every selected address, and the
[stage asset consumer proof](shoot-stage-assets.md) separately verifies the
real loader/scrolling reader. These map arguments do not select SRAM.

The dedicated Shoot graphics initializer calls the queue reset at
`77DCF8`. Together, these observations establish that the known generic
queue is not populated or flushed by the stage-11 dispatchers after that
reset. They do not establish that every other-stage queue count is bounded,
or that an arbitrary indirect caller cannot reach this family.

The real Shoot BG descriptors are the 24-byte records `3B5178` and
`3B5190`, selected by indices `27` and `28`. Their `+14` fields are zero;
the constructor at `753003` copies these fields into runtime BG `+2E`.
Zero is **not** an empty-animation sentinel: source ROM `42DE00` begins
with a three-record animation header. The dispatcher exclusion above is
therefore necessary; simply treating zero as "no animation" would be wrong.

## Owned task objects and the generic byte copy

The source task initializer `750928..750970` selects ES=`0C00`, starts at
offset `0014`, and clears `1BA0` words. Its allocator `750970` scans slots
at stride `0110`, tests the allocation flag at `+0A`, and returns segment
`0C00`. This identifies 52 task slots with `10` header bytes and `100`
payload bytes each. Valid owned payloads occupy the linear envelope
`C024..F753`, disjoint from `13CD8/13CDA` and their SRAM aliases.

The object initializer `741F6E` obtains 26 of those task handles and stores
them in `1000:060C..063F`; its six object-kind groups use flags at
`0640..0659`. Object allocation at `74202A` retrieves a handle from that
table and returns the task address plus `10`. This is positive storage
ownership evidence under the normal initialized-battle precondition.
The task scan has no exhaustion guard, so it is not a proof after pool
overflow or for arbitrary pointers. An imported callback's actual arguments
still need to be shown to inhabit this typed domain.

The generic byte-copy helper `4FFF:2178` (`752168..7521A9`) has exactly
three encoded direct far callers in the whole ROM. The two at `76B67F`
and `76C36F` read SRAM `03EA..05E9`, copying the captured palette into
internal palette RAM. The third at `76BF7E` writes SRAM `03EA..04C9` from
one of three ROM ranges: `4A0000..4A00DF`, `4B0000..4B00DF`, or
`4B6140..4B621F`. The helper's argument order and each constant call setup
are machine-checked. None of these direct calls reads the target words.
This does not rule out an unencoded indirect caller.

## Exact remaining argument gates

The fixed-ROM byte inventory identifies 36 `mov DS,[BP+disp8]` and 31
`mov ES,[BP+disp8]` candidates. The JSON records their addresses as a
diagnostic denominator, not a complete reachable-call or segment-flow
proof. The unresolved first-milestone obligations are now narrower:

- Resource readers `4FFF:226E/22CA` load DS again through a descriptor's
  segment field at `75228E/7522EA`. Every live call must be tied to the
  already decoded ROM P0/P1 resources, including restored normal callbacks.
- Palette helpers with segment-argument loads at `751DD3`, `751E9E`,
  `751EF6`, `751F7C`, `751FE0`, and `75206A` need complete live call-argument
  domains. The scene's bounded `03EA` snapshot proves only its own calls.
- Collision imports with argument loads at `76F87C/76FB30` need the
  restored common callback's object/BG argument pairs bound to the owned
  object pool and actual stage-11 background state. A pool bound alone
  does not establish what an arbitrary caller passes.
- The persistent-state claim after leaving stage 11 still needs any
  observer before the next owner initialization excluded. The canonical
  `E8`-byte save-record boundary does not prove this by itself.

No positive consumer of the two high SRAM words was identified. That is
not yet a complete no-observer proof, even with the valid-owned-object
precondition. Both the global and scoped first-milestone conclusions remain
explicitly unresolved. No native storage was invented and no source store
was silently omitted.

## Reproduction and remaining gate

Run from the repository:

```powershell
py -3 tools/analyze_shoot_sram_boundary.py `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  --output build/shoot-sram-boundary-20261013/analysis.json
```

Report SHA-256:
`29304FA84432898B857AC8874C1525E57FDE0EABBAFFC5008DBFA80962E27295`.
Eight mutations of the serialization count/source/destination, stage-11
dispatch target, record stride, descriptor animation field, task-allocation
stride, and generic-copy count are rejected.
The report deliberately returns `UNRESOLVED_OBSERVER`, with both
`dead_store_proven`, `native_storage_mapping_proven`, and
`scoped_first_milestone_no_observer_proven` false.

Next work must bound the generic readers and their actual arguments in the
live Shoot graph, including the normal callbacks restored on scene exit.
An unused four-byte native palette tail would be a proposed representation,
not a proved consumer mapping; it cannot remove this gate by itself.
