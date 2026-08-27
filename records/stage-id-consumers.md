# GBA stage-ID consumer audit

## Method and boundary

`tools/find_arm_calls.py` enumerates aligned ARM `B`/`BL` encodings that
resolve to the exact retail getter address `0x080D1C78`. It is a structural
candidate scan, so every one of the twelve matches was contextually
disassembled before classification. The source ROM is the exact USA image
identified by SHA-256
`996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`.

## Confirmed direct callers

| Call site | Immediate use | v20 policy |
|---:|---|---|
| `0x0803EE5C` | stage setup and expanded initializer dispatch | retain actual ID |
| `0x080C4BC4` | eight-entry jump table | bounded analog |
| `0x080C4CC8` | eight-entry jump table | bounded analog |
| `0x080C8264` | return value discarded before shared object update | unchanged |
| `0x080C829C` | retained as a stage discriminator | unchanged |
| `0x080C86CC` | direct comparison with retail stage 6 | unchanged |
| `0x080C87CC` | copied to runtime state, not used for an immediate table index | unchanged |
| `0x080D0BD0` | eight-entry jump table | bounded analog |
| `0x080D1408` | eight-entry jump table | bounded analog |
| `0x0835B384` | direct comparison with retail stage 3 | unchanged |
| `0x0836D28C` | eight-byte retail graphics/object-mode record | bounded analog, native callback pending |
| `0x0836D2F8` | eight-byte object movement-pattern record | native twelve-entry Ver. 1.5 table |

The setup routine also uses the actual stage ID at `0x0803EE70` to index an
eight-entry dimension table without another getter call. v20 maps only the
derived byte offset there, preserving the actual ID in `r1` for the expanded
initializer dispatch.

## Remaining native-port gate

The two `0x0836D2xx` consumers correspond to the object-mode family whose WSC
Ver. 1.5 functions include the producers at logical `4090:3DFB`, `4090:3EE0`,
and `4090:3FCA`. The movement-pattern consumer is now native through stage 11.
The remaining graphics/configuration consumer is still mapped to a safe retail
analog and does not claim those producer behaviors. Completion requires its
converted native callbacks and removal of the temporary mapping at
`0x0836D28C`.
