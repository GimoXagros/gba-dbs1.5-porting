# Independent terminal owner-link ARM QA — 2026-11-09

PASS for the bounded owner-field repair and capture-free production gate.
The component is `46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B`
over predecessor `FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8`.
No actual runtime guard acceptance or terminal completion is claimed here.

The complete eight MiB inverse proves that offset 6FFC00 changes exactly
`E5960018` to `E5960028`: LDR r0,[r6,+18] becomes LDR r0,[r6,+28].
The declared range is four bytes and exactly one byte differs. All other
bytes, including all constructor, fatal, auxiliary death, and guard code,
are unchanged. Nine mutations within and outside that word are rejected.
Builder, new manifest, original WSC1.5, predecessor, component, native
source ranges and WSC source ranges are independently identity checked.

Actual ARM constructor stores at 085BC29C, 085BC2A8 and 085BC380 establish
AUX+28=SECOND, AUX+18=FIRST, and SECOND+28=AUX. The fixed constructor
global literals identify SECOND at 030048A0 and FIRST at 0300489C.
Execution of the stage11 fatal adapter writes only SECOND and AUX
callbacks. Execution of the auxiliary entry and all sixty death updates
reaches final 085BF600 without rewriting any of those three links.
There is no added AUX+18=FIRST guard requirement.

The independent bounded Machine runs the existing guard instructions,
without service models, against the final snapshot from the completed
FF3A trial. The predecessor refuses the reverse owner because it reads
FIRST through AUX+18. The repaired guard proceeds past that test but
still refuses the actual final outer IO mapping: BG1CNT 1F03 instead of
the guard's required 1E03. Guard writes are restricted to its stack.

Replacing only BG1CNT with the earlier hook value 1E03 produces a
**mixed-epoch model**, which reaches the guard's acceptance branch.
This does not constitute actual same-instruction acceptance evidence.
Eight negative cases refuse: wrong reverse owner, wrong forward owner,
inactive auxiliary, wrong auxiliary resource, moving FIRST, nonzero BG
velocity, extra renderer, and auxiliary nonfinal callback.

The production gate is a separate process which reads only source,
component, predecessor, frozen builder and the new manifest. It imports
no Machine or production builder and reads no historical RAM, State,
capture or semantic report. It does not rerun the old full suite.

Frozen outputs:

| Artifact | SHA256 |
|---|---|
| tools/verify_shoot_terminal_owner_link.py | 90BE235C505F9D9D46382D071BF531E021B6E8F7B392022C6D7FF29C3A4022D4 |
| tools/verify_shoot_terminal_owner_link_production.py | 47144AA1300AB2C26907C8343306E4C9BA1C0ADB6025AE310E43A100AFFE7C13 |
| build/shoot-terminal-guard-owner-qa-20261109/report.json | 16E7D946820C2F08B921A35EA6F5859C20BA862170030C0CD654BDF8CC3C0194 |
| build/shoot-terminal-owner-link-production-qa-20261109/report.json | 8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3 |

The semantic pass clears this repair for the separately authorized root
runtime replay. Actual hook acceptance, IRQ, cleanup and mode8 must come
from that new replay. No emulator, main build, Git command, production
author edit, or historical evidence edit was performed by this reviewer.
