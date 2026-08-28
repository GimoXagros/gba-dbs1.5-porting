# GBA stage-ID consumer audit

## Method and boundary

`tools/find_arm_calls.py` enumerates aligned ARM `B`/`BL` encodings that
resolve to the exact retail getter address `0x080D1C78`. It is a structural
candidate scan, so every one of the twelve matches was contextually
disassembled before classification. The source ROM is the exact USA image
identified by SHA-256
`996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`.

## Confirmed direct callers

| Call site | Immediate use | v24 policy |
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
| `0x0836D28C` | eight-byte graphics/object configuration record | native twelve-entry Ver. 1.5 table |
| `0x0836D2F8` | eight-byte object movement-pattern record | native twelve-entry Ver. 1.5 table |

The setup routine also uses the actual stage ID at `0x0803EE70` to index an
eight-entry dimension table without another getter call. v24 maps only the
derived byte offset there, preserving the actual ID in `r1` for the expanded
initializer dispatch.

## Remaining native-port gate

The two `0x0836D2xx` consumers correspond to adjacent movement-pattern and
object-configuration families. Both tables are now structurally expanded
through stage 11. The configuration consumer uses the actual stage ID and its
commercial conversion rule is verified across stages 0–7. Stages 8–11 use
their native pairs at WSC physical `0x745081..0x745110` and all eight source
callbacks. No entry in either object table remains mapped to a retail analog;
the four other bounded getter consumers are independent legacy systems.
