# 6F event-table cause and fixed gameplay

The first two isolated 8C72 campaigns reproduced the same
premature replacement of song 6F. The focused second capture
matches the first capture's ROM, input trace, music telemetry,
score ledger, alignment journal, and terminal IWRAM/EWRAM byte
for byte. Both failed the full stage-return check.

At core 34954 the live CPU Impmon's air transition reads beyond
the 11-entry native event table. ID 11 reads low halfword 4000
from the next ARM instruction at 0835A5AC. The native P1
initializer receives event 4000 and the indexed row contains
command pointer FFFFFFFF. The accepted type-1 song 04 request
in the same core returns to caller 08012918 with that invalid
pointer and the same CPU presentation. Player zero starts 04
in the following frame. The animation tick hook observes no
04 requests, distinguishing this path from the tick routine.

The C91 repair extends the entry, ground, and air selectors
to the 15 source WSC identities. All existing entries 0 through
10 retain the same values and all 45 source values are inside
the corresponding native P1 event table. Each base load
preserves its condition and destination register. The air
literal is word aligned at 0835A598. The full inverse restores
8C72, with 114 declared bytes and 109 actual changes. The new
90-byte data range is erased in the predecessor, beyond the
last owned audio payload and free of conservative incoming
encodings. The replaced words show the expected ARM references;
two Thumb-shaped encodings are high halfwords of known ARM
CMP and BX LR instructions.

## Fixed actual capture

The exact C91 score-assisted Normal campaign passes end to end.
The three scoped Korean captures each loaded their pinned ROM.
The 6F scores were assisted through seven live player-score
writes to 999 before the target. Item collection, evolution,
native pause and resume, devolution, and the stage music return
were performed by the running game.

| Core | Observed CPU Impmon and audio state |
| --- | --- |
| 33629 | The extended entry table returns source event 105 for actor 11. |
| 33689–33690 | Impmon's native selector queues 6F, which starts with header 08D782CC and cache 6F. |
| 33691 | One equal native header comparison invokes MPlay Stop. |
| 33695 and 33724 | Same header and cache, with stopped status during the neutral hold. |
| 33726–33729 | One equal native header comparison invokes MPlay Continue. The same song and header are active at the resume boundary. |
| 34954 | Air transition reads source event 25. The replacing 04 request is absent throughout the target interval. |
| 35013–35015 | The same CPU naturally de-evolves, queues prior stage song 16, starts it at core 35014 and reaches the next boundary in battle. |

The fixed run independently verifies all 87 top-level artifacts
and 11 complete capture sets. Both canonical IWRAM alias counts
are zero. The separate journal records 83 metadata and 80
dispatch observations, with zero odd-pointer and E5 events
for this route. Historical E5 remains open. The run was silent
and verifies native player state. Two in-memory contradictions
restoring the old invalid event or inserting an 04 takeover
were rejected.

| Evidence | SHA-256 |
| --- | --- |
| tools/verify_evolution_event_tables.py | B9BB463EA86CBF76A5534B954DF7FE6555F4CA5BD1AA81FB8FD59212EC994A67 |
| Independent C91 component gate | A787F41CD3A78BD0B509F2A7EC96C10133BDB825292BC11EDB169D162AA2469B |
| tools/verify_evolution_event_queue_capture.py | C015ACA17FE6DB865A2D08A52671EA87614E74C3276AC0618E4DB894E27F92E5 |
| Focused 8C72 causal audit | 3C100952B784CEBD841485D7624352D45A20FAC130FEB6F791778B2742E8190A |
| Fixed C91 gameplay audit | F72A105BDFA4989CCAB96AAEF0222CDB5C4E5FE0DECED4A239560FDBA3C05BB3 |
| Old focused queue journal | 6583A07BE8551107B020D877FCFF6F730A618D54D60BA0151EC8984B54A086B4 |
| Fixed queue journal | 9ADD021F2EC1A5C6A18262D2639AC163960ADA1C8C7443D1EDAE53B52BD49D62 |
