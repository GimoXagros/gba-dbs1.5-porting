# Independent fatal callback route QA

PASS for the single four-byte hook at36E5EC. The verifier imports no
production builder/analyzer and reruns no old callee corpus.

| Artifact | SHA256 |
| --- | --- |
| Predecessor IRQ component | `18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1` |
| Fatal-route component | `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7` |
| Component manifest | `69D9E5140216D8479124DD230A5F1ED19676491FA10686D61542FD3DA28F5EE8` |
| `tools/verify_shoot_fatal_callback_route.py` | `48600765FC794FBB3A0859520125AB21B3736DCDAD76B491F020F71ADCFBFCF0` |
| `build/shoot-fatal-callback-route-qa-20261109/audit.json` | `61656691CD4126193003FB2E43B851F3CAA57A8C6C78A147ED602B181F2F2FD4` |
| Reused resident adapter64 bytes | `49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246` |

The exact displaced MOV R0,R5 becomes an unconditional, non-linking branch
to085CD960. Both adapter paths execute that displaced operation. The full
ROM inverse restores the exact predecessor; no other byte, including the
resident adapter or preceding HP arithmetic, changes.

Actual ARM execution covers all256 stage bytes under all16 incoming NZCV
combinations:4096 joined cases. Only stage11 substitutes upper085BDD00 and
linked auxiliary085BF204, corresponding to source4090:7AB1/7D8D. Every other
stage keeps the retail callback pair and exact ordered writes. Execution
continues through real36E604 cleanup to36E438, checking all live registers,
both76 timer resets, parent94=1 and03004D40 reset. Ten additional cases run
the actual HP subtraction/halving prefix, including nonfatal exits and signed
underflow, without service models or changes to damage arithmetic.

A separate restricted71-state flags walk covers the14 typed attacker
continuations. Logical TST/ORRS define fresh Z but are not treated as complete
NZCV kills. Any conditional consumer of still-incoming flags is rejected.
Return-only paths reach the real caller353FF0 and full flag overwrite at
353FF4 SUBS; the typed freeze import reaches36A6A8 CMP. Seven complete kill
sites close the remaining branches. Dead intermediate CPSR values need not
equal the old fatal subtraction flags.

Eight negative controls reject a linking hook, wrong adapter target, write
outside the four-byte span, changed resident target, actual wrong selected
callback, conditional common-tail consumer, removed caller flag overwrite,
and removed freeze-prefix overwrite. The semantic negatives are exercised
without relying solely on whole-ROM hashes.

This approval connects the existing stage11 fatal selection. It does not
open the external Shoot scene entry, implement a new non11 difficulty table,
repair E5, or establish complete Shoot behavior. No emulator, save/state,
guest-memory write or main-build edit was performed by this audit.
