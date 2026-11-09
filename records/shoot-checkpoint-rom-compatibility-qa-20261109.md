# Native checkpoint compatibility with the bounded ROM correction

**Source compatibility passes; actual restore remains untested.** The exact pinned
mGBA deserializer treats a ROM CRC mismatch as a warning without setting its
error flag. A title or game-code mismatch sets error and causes load failure.
The serializer always emits the current loaded ROM CRC; deserialization never
replaces that current CRC from the old state. This follows the exact
[native source](https://github.com/TASEmulators/mgba/blob/94b1578f8545d8ad17bb4036dba908612d5731e2/src/gba/serialize.c),
SHA222A79513CD6B94354E3B56EE38E3EB46BA933B709C0D2686CADDB683A960482.

The already validated checkpoint438C8598 and full CoreC6E8036B were read without
loading or changing them. For the separately approved equal-length five-word ROM
correction, title and game code must remain identical. A subsequent save under the
corrected ROM may refresh native bytes8..11, which are decompressed Core bytes
12..15 after its four-byte native-length prefix.

Only those four bytes may be replaced in an **expected comparison buffer** with the
little-endian CRC32 of the approved corrected ROM. Every other full Core byte,
including all CPU/RAM/native-extension/managed state, must equal the original.
The original `.State` file must never be edited. The future loader must still
prove actual restore/resave equality; warning-only source handling is not that proof.

Machine report: `build/gba-shoot-checkpoint-rom-compatibility-qa-20261109/report.json`.
SHA256: `84DF3F258D8D7AB3EF132D3D8E053E4B82C6D4C1FFF72AE41004E183F3AC659B`.
No emulator, state load, ROM modification or full previous suite was run.
