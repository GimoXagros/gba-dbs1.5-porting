# Runtime investigation, 2026-10-15

All runs used invisible private desktops. No supplied WSC save was opened,
hashed or loaded. Full manifests, memory dumps and screenshots remain under
ignored build/runtime-* directories. No modified ROM is a release.

## GBA environment and observations

The old local mGBA0.10.5 environment gave abnormal images for both retail USA
and v54; those runs are not sufficient to attribute a port regression.
The preserved development build fa977ccbc815efc93aefad9acddc9af0577d7827
displayed retail USA's title normally at25 host seconds. v54 displayed corrupt
intro sprites/palettes at25 seconds without input. With Start at28 and A at32/36,
the45-second run stopped with GDB S04, PC00000004 and CPSR4000009B.
This is a failed runtime check, not evidence that Shoot was reached.

Using that same development binary,25 seconds and no input:

| Intermediate | Observation directory | Image |
| --- | --- | --- |
| shoot-aux-object | runtime-bisect-20261015-aux | three recognizable intro figures |
| shoot-far-tiles | runtime-bisect-20261015-far | three recognizable intro figures |
| shoot-other-player | runtime-bisect-20261015-other | corrupted intro |
| shoot-rules | runtime-bisect-20261015-rules | corrupted intro |
| shoot-lower-audio | runtime-bisect-20261015-lower-audio | corrupted intro |
| v54 | runtime-bisect-20261015-final | corrupted intro |

A diagnostic-only copy of shoot-other-player restores only the three previous
words at485030/485034/485038, leaving its new resident code untouched. It shows
the recognizable intro figures again. Hash:
`D3408C6D1A5BE520CAF704DD6059CFE1DFFBCF374534BAD26C664D9F230A12CC`.
Artifacts: build/diagnostic-20261015 and runtime-bisect-20261015-revert-physics.
The comparison implicates these changes but is not a complete deterministic
regression proof: these captures are host-time based, not equal game-frame
anchors. Repeat at an actual consumer breakpoint and trace reads of the three
words before adopting any fix. The previous pointers are known not to address
the intended complete source physics records, so blindly reverting them is not
an acceptable final repair. No pipeline reversal was made.

## Capture transport repair

A queued GDB stop packet can precede the ACK for the following command. The
old capture code rejected '$' as an invalid ACK. It now validates and records
only S/T stop packets while waiting for ACK; unexpected packets still fail.
Checksum digits are read individually rather than assuming recv(2) fills both.
tools/test_mgba_gdb_transport.py reproduces that ordering with a socket peer
and passes. The real retail and candidate capture runs then completed.

## WSC source observation

An isolated fresh Mednafen1.32.1 build6985841, matching corecd0a39b, started
frozen before the first instruction. Contracts validated. Menu, roster and
first battle were reached with input only. RAM4000..401F was zero in the first
battle; this alone does not establish Shoot terminal tile lifetime. Source
execution breakpoint addresses are16-bit logical IP, not linear CS:IP; an
attempt to pass7E325 was rejected. Interrupted writes and CPU values are in
build/source-runtime-20261015/probe-log.json, SHA-256:
`1A932EA843663E5F7FFF787F6C6FA1C027D8BBE604650FF0225D1826FD14965B`.
The exact managed source generation and the earlier incompatible-core probe
were stopped after recording evidence. No source SRAM-observer gate was closed.
