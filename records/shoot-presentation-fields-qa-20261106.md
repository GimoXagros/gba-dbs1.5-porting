# Presentation parity and pending-upload fields: independent ownership check

**PASS for field correspondence and the bounded alternate-owner classification.** This read-only review does not approve a complete upload-queue or renderer projection. `terminal_path` owns the source lifecycle and implementation proposal; this review independently checks native object identity and constructor layout. Original retail996D, sourceC415 and actual v70 candidate8EC8 supply the inspected bytes. No emulator, guest writes, save content, main or production tool changes were used.

| Logical role | WSC1.5 presentation | Native presentation | Positive constructor evidence |
|---|---|---|---|
| Fixed tile base | word `+10` | halfword `+14` | Source752440; native08012808 |
| Parity | byte `+14` | byte `+16` | Source752474; native0801283C |
| Pending upload task | near handle `+2A` | pointer `+38` | Source752478; native08012840 |
| P1/P0/P2 resource references | `+30/+34/+38` far-reference groups | pointers `+44/+48/+4C` | Matching resource assignments before the zero-initialization sequence |

Source constructor loads its output object as ES:DI from BP+6/+8 at7523F5..7523FB. Its zero sequence clears status+0A, parity byte+14 and pending word+2A. Native080127E4 saves four registers, loads output R5 from adjusted SP+48, then clears status+0A, parity byte+16 and pending word+38 in the same order at08012834..08012840. The fixed tile base and resource assignments independently anchor the widened layout. In particular, native+38 is not source+38/P2: native P2 is+4C.

The source parity width is positive:75260E loads byte+14,752612 XORs1 and752615 writes that byte. The pending check is word+2A at75261F, and allocation return AX is stored there at752686 after `4FFF:0980`. This agrees with the lifecycle specialist's role classification. Native restoration must preserve the byte width of+16 and use the full pointer width at+38; the adjacent parity padding byte is not initialized by0801283C.

The entire actual native presentation/P1/P0 core range raw127E4..132EC remains byte-identical to retail. A bounded per-instruction immediate-offset inspection finds only the two constructor stores for object offsets+16/+38 in that range, including the retained P0 renderer. That observation alone is not a whole-program free-field proof.

The nearby offset matches have positive, different owners:

- **08013814** reads background state+38 through R5 supplied to080137AC at SP+24. A concrete caller08015DFC loads literal03002338 and passes it at08015E04..08015E10. The background constructor is independently tied to the same03002338 object by actual calls at0803F204..0803F224 and0803FD94..0803FDA8.
- **08013C84** reads background row coordinate+16.08013C64 obtains the map object from its argument; it multiplies+16 by width+0C, adds+14, then selects through map descriptor+24 and calls080110DC.08013BF8 positively initializes those dimensions and descriptor fields.
- **0801422C and0801448C..08014530**, plus field reads at0801482C/0801487C and08014B34/08014B4C/08014B60/08014BB8, belong to that background scroll path.08013DE8 binds R5 to the background argument and does not rebind it before these accesses. Its direct calls into080146E0 and08014A14 preserve that owner; neither helper rebinds R5 before the listed reads. There are sixteen such object-offset accesses in the bounded background ranges.
- **08015F10/08015F48** load/store a counter at fixed global03002568+16. The base is resolved directly from the08015F08 PC-relative load and literal at08015F80. It is not the presentation argument.
- **08015DAC** uses a PC-relative displacement of38; this is a literal load, not an object+38 consumer.

The corresponding field instructions and owner bindings are retained in the actual v70 ROM. The larger background-module interval is not wholly retail-identical: the dimension-table literal at raw146DC and the existing stage-bounds hook at15D9C differ. Neither changes the classified object-field sites; they are not silently omitted from the comparison.

The result supports these two intended fields on a positively identified, initialized native presentation object. It does not authorize changing arbitrary matching offsets on background objects, treating every native+38 as a pending task, or assuming absent direct accesses exclude arithmetic/indirect aliases. Queue insertion/cancellation/destruction, inherited actor state across scene transitions, F001 priority representation, IRQ/VRAM ordering, parity rollback and renderer-clone lifetime remain the implementation specialist's separate obligations. No complete projection or runtime behavior is endorsed here.
