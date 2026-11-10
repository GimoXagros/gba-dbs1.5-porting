# Terminal prospective mapping and live consumption check

Isolated280D repairs the confirmed phase-order failure over46B3. It is not
integrated into mainv75. The actual two-frame cause and independent capture
auditF25BB784 are recorded in `shoot-terminal-bg-epoch-20261110.md` and
`shoot-native-terminal-bg-epoch-capture-qa-20261110.md`.

The existing heavy queue-time guard remains. Its BG1 predicate now evaluates
the mapping that its selected display will produce: actual085E7418/1C calls
FEC with21; actual08001004..10 replaces the high byte with1E and preserves
the low byte. Source75FAE6/FAE8 establishes the corresponding selector21
before transition IRQ installation. For every16-bit control word,
`(((current & FF) | 1E00) & DFCC)==1E00` is equivalent to
`(current & CC)==0`. Thus map/size bits are bound to the actual queued
producer; charbase0,4bpp and no mosaic remain required.

The short new consumer at086FF720 additionally checks live hardware
DISPCNT mode0, live BG1 low bitsCC and both32-bit velocity words2354/23A4.
Those two words cover all four original halfword velocities. Mode7,
stage11 and0400 retain their existing checks in the enclosing wrapper.
Any failure branches to its existing stale unwind086FF6F4 and original
08587200 fallback. Success reloads R0=086FFE10 and branches from086FF75C
to the real085E7400 display, whose FEC mapping precedes IRQ installation.

This avoids putting the heavy actor/tile/map scan in an IRQ. The stub has
16 instructions, two literals, no loop and no extra stack frame. It uses
only R0/R1 already saved by the retained wrapper; the hook's BL preserves
the original return086FF6EC. All other live registers are retained.

| ROM span | Change |
|---|---|
| 6FF6E8..6FF6EC | existing display BL retargets to086FF720 |
| 6FF720..6FF768 | 72-byte consumer in the existing adapter reservation |
| 6FFDE8..6FFDEC | prospective maskDFCC→CC |
| 6FFDEC..6FFDF0 | projected comparison1E00→0 |

Total84 declared bytes; exact whole-ROM inverse restores46B3. No RAM
allocation, new task or additional stack bytes are introduced. The whole
tail6FF720..6FF800 is erased in the exact predecessor; its owning adapter
reservation6FF600..6FF800 and former288-byte body are retained.

The complete conservative inbound scan finds seven apparent Thumb branches,
all from the upper halfwords of exact existing ARM loads. They are retained
in the manifest, not silently filtered or described as a zero-hit scan.
Containing ARM words are6FF3B4,6FFBE8,6FFBF4,6FFC00,6FFC0C,6FFC1C,6FFC20.
The first belongs to the complete pinned ARM scene adapter entered by
033FD04→086FF380; the others belong to the pinned ARM guard entered by
086FF694→086FF9C0. Their exact words and interpreted destinations are
checked. There are no pointer, ARM branch/literal or other unexplained
references into the new body. Independent QA owns final classification.

The typed stationary actors, exact presentation resources, FIRST-only
upload ownership, blank tile and sampledF000 rows retain the bounded
555554FD contract. This is not a claim of scheduler quiescence or exclusion
of every possible DMA owner. The source terminal0400 update only clears
its sampled map rows;1000 shake uses the other descriptor2338/F800.
The actual volatile hardware and descriptor fields are now rechecked at
consumption, instead of relying on their queue-time values alone.

Author checks cover65536 mapping words, actual queue/copy/dispatch/FEC and
30-interrupt chains for k1 and143,22 intervening-field mutations with exact
existing fallback register/stack/nonstack-write equivalence, success
register preservation, and seven inverse corruptions. No service models
are used. The two first compares are8 and150, but these instruction-model
results are not measured hardware timing. Actual k1 deadline verification
remains required. No source-DI value or final-port completion is claimed.

Production `build(before,source)` reads only the exact predecessor and WSC
source; optional author checks use synthetic fixtures separately. A fresh
production replay produced identical ROM and manifest bytes.

| Frozen artifact | SHA256 |
|---|---|
| `tools/build_shoot_terminal_display_epoch.py` | `93BDB86A50E72E7227476369CA2DDFD8F9301B93BB3E40928291C48BFA16B260` |
| `build/shoot-terminal-display-epoch-20261110/component.gba` | `280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7` |
| `component.json` in that directory | `F8C53C3C4FCA703316F0638DE0DFC61AEA16F3A2D987D781DB7215A9D82F345B` |
| `author-report.json` in that directory | `6E1206A4574F06E249349FE01A839FF47A48B4E2B2ECBC777818048C9789E8A5` |

The runtime observer must use the projected early predicate and recognize
guarded display at086FF75C, with R0=086FFE10, rather than the former callsite
086FF6E8 before the new checks. Early queue selection is not successful
consumption. A new consumption refusal reaches086FF6F4 with LR086FF6EC.
No existing observer, host, main build, capture or Git state was edited by
this component author. Independent component/observer QA and root's
controlled runtime trial remain separate gates.
