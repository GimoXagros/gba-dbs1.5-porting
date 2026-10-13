# Shoot scene object survival

`tools/analyze_shoot_scene_objects.py` verifies the native case-5 cleanup list
against its concrete producers and allocator pool dispatch. The report is
`build/shoot-scene-objects-20261013/analysis.json`, SHA256
`A4E1DE4CB5000EC31B56471D99490936E2B82C84277976B3FA0F5AA36665F8B5`.
Three altered pool/list selections are rejected. No game or save is opened.

The source EEA scene releases the objects in `1000:0670`, using byte count
`1000:066E`, before saving first-player HP. The existing commercial case-5
entry `0834059C` already performs the corresponding native list release:
`083405C8..083405F4` reads list `03004760`, count `0300475E`, and calls
`083524C4` on each entry. The new scene inherits that cleanup order.

The ordinary list producer `08341034` selects the first-player list at
`08341054`. It allocates pool0 at `083411A4` and appends that newly returned
object at `08341304`. The scripted presentation retains the same list
pointer in task data at `08378C28`; `08378CC0` passes that pointer as the
allocator's destination and `08378CF0` also selects pool0. These are actual
pointer-producing paths, rather than an assumption based on nearby globals.

The native allocator `08352374` selects one of six branches, reads the pool
flag address, subtracts the shared flag origin, and uses the resulting index
in the existing object-block pointer table. Its relevant owners are:

| Role | Pool | Flag slots |
|---|---:|---|
| Released list objects | 0 | `03004810..0300481E` (15 slots) |
| First player `0300489C` | 3 | `03004824` |
| Second player `030048A0` | 4 | `03004825` |
| Auxiliary `03004D3C` | 5 | `03004826..03004827` (2 slots) |

Player allocation sites `08352BAC` and `08352BE8` select pools3 and4 and
store the actual player handles. The existing auxiliary-lifetime analyzer
independently proves ID0343/pool5 at `0836FE9C`, its global handle, matching
commercial source lineage, and its direct consumers. This closes the
specific concern that the inherited case-5 list cleanup releases either
player or the auxiliary object.

The proof assumes an ordinary initialized retail battle with uncorrupted
engine-owned lists and pool pointers. It does not certify entry from an
arbitrary foreign task or prove absence of arbitrary memory corruption.
It also does not resolve the separate `1000:3CD8/3CDA` source-global stores,
nor authorize an external initializer hook before the other prerequisites.
