# Mode23 private flag bit1 reachability

The source audio/display bodyC9B9 calls sound service8719:0148, then calls4FFF:4F84 only when private word0200:0012 has bit0001. That branch has no producer in the reviewed valid scene lifecycle. This is a private flag invariant, not a claim that4F84 is generally a no-op.

The existing44-root/4052-instruction closure is reused from `shoot-normal-entry-save-copy-20261109.md`; no cached graph artifact was available and no new full graph traversal is claimed. Independent bounded inspection of the exact source producers and all literal0012/0013 occurrences in raw74A940..74D2FF gives:

| Source address | Typed action on0200:0012 |
|---|---|
|74A9C3/74A9C6|SetSI=0012, thenES:[SI]=0000 during creation|
|74AE21|ANDFFFB|
|74B578|ANDFFFB|
|74B5AB|OR0002|
|74C388|OR0004|
|74CF1C|ANDFFFB|
|74D2CB|TEST0001 before optional4F84 call|

Other absolute0012 references are read-only tests at74B706(bit2),74C37C(bit4),74C5DF(bit4) and74CE60(bit4). Remaining literal0012/0013 bytes in that interval are rectangle-height arguments or branch displacement bytes. The only immediate pointer-to0012 is the creator'sSI initialization; there is no additional immediateSI/DI/BX alias to0012 or byte store to0013 in this bounded census. The source producer population is six writes, with the pointer setup counted separately.

Starting from0, the listed operations close over `{0,2,4,6}`. Consequently bit0001 stays clear. The legal source participant-handle population is3–6: roots occupy00..05 and participant handles06..11, ending immediately before flags12. Source presentations begin20/62. Thus correctly bounded handle/presentation services do not alias flags12. This reasoning assumes the already required valid handle population and owned scene state; it says nothing about corrupted pointers or arbitrary seeded flag words.

The current native translation places flags at context+24. Its explicit stores in lifecycle, item and collision modules are BIC4, OR2 and OR4. Creator allocation uses the typed `m23_spawn` payload-clear contract. Nine widened handles occupy00..23; presentations34..83 and84..D3 and the FC context pointer are disjoint. Imported presentation services receive the presentation addresses, and participant services receive separate participant payloads, not the flags address. Native sound/display services have fixed established owners and no source0200 global alias.

It is therefore appropriate to omit this unreachable fade import from the valid-scene translation. It must not be satisfied by a fake live BXLR adapter. The final linked-component gate must retain the invariant: no newly introduced flag-bit1 writer, bounded handle population, disjoint live task payloads, full payload initialization before scheduling, and the same typed helper pointers. If any of those conditions changes, the branch must be re-evaluated and4F84 implemented before it can become reachable. No emulator, installed mode23 scene or arbitrary-state equivalence is claimed.
