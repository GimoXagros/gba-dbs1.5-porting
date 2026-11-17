# Ordinary campaign stage producer and progress consumers — 2026-11-17

The source campaign has eleven ordinary encounters. The previous port retained
the retail eight-encounter producer and overrode the stage getter for player
IDs11/13/14. The isolated correction writes the source stage and CPU identity
at the actual campaign producer, then reads that stage consistently. A second
component extends the AI progress tables and round label required by the larger
progress domain. Neither component allocates RAM or writes progression from a
host tool. Runtime entry and complete playthrough are separate from these
source/ARM checks.

## Actual source producer

Pinned WSC1.5 SHA-256:
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The producer is76F1:17B2, raw7786C2..77874F. DS1000:004E owns the campaign.
Its physical-stage byte is+0E=005C, progress is+1E=006C, and the route-row
selector is+1F=006D. Source780715 initializes progress0; source78074F..75A
stores the fourth RNG result masked7 as the route row. This row is **not
difficulty**. Native equivalents already exist at0809114C and08091198..1A0,
using0300232E and0300232F. The native physical-stage owner is0300231E.

The near dispatch table7786AC has five initial arms, five row arms, and one
final arm. The source stage order is:

| Progress | Actual stage selection |
| --- | --- |
| 0..4 | 8,1,9,6,10, from raw778674 |
| 5..9 | row[RNG&7][progress−5], from raw778679 |
| 10 | final stage7 |

The eight five-stage rows are exactly:

```text
5 0 3 2 4
0 3 2 4 5
3 2 4 5 0
2 4 5 0 3
4 5 0 3 2
5 0 3 2 4
0 3 2 4 5
2 4 5 0 3
```

Raw7786A1 maps physical stages0..10 to CPU IDs
`0,1,2,5,6,4,3,15,13,14,11`. The previous current ROM already correctly used
CPU15 at stage7; the old retail USA value12 is not reintroduced. The actual
source stage stores are77871F and778725, followed by CPU/form writes778738/73B.
If P1 and CPU identities match, CPU form is P1 form XOR1; otherwise it is0.

The native successor0808A6F4..700 increments the existing byte and calls
0808B638; it has no hardcoded upper limit7. Source777AEB..AF4 does the same.
Initial roster confirmation source778F49/native0808205C invokes the producer
without incrementing. Continue/reselection source777B41/native0808A754 also
invokes it without a new counter. The source's additional caller772498 is a
separate mode/scene path; this component does not invent a new native call to it.

## Clean1.5 mode and dedicated routes

Source778728 tests config+25 bit01 before calling the old Impmon interruption
scheduler7785E5. Clean startup74FC0D..4A clears this source mode byte, matching
the previously declared clean1.5 collector/roster scope. No native owner for
the alternate-mode byte is established. Accordingly the correction removes
the retail unconditional scheduler call0808B6D8 for this same clean scope;
it does not read a guessed native03002335 flag.

The pre-existing scheduled-challenge branch remains exact: source7786E8/native
0808B674 clears run flag10, sets20, selects CPU11, and preserves the physical
stage. It bypasses the progress tables. Ordinary clean1.5 encounters now select
CPU11 at physical stage10 through the source table, rather than scheduling the
retail extra challenge on a guessed difficulty condition.

The older `evolution-music-6f-cpu-route-analysis-20261116.md` describes a valid
observation of the then-retained retail scheduler, but its +1F field label and
address were wrong: this is RNG row0300232F, not difficulty0300231F. Existing
captures are not rewritten; the correction changes future ordinary routing.

Stage11 is a dedicated route, not an extra ordinary table entry. Source747A95
writes11 immediately before its initializer; the existing native dedicated
initializer and manager priority helper remain untouched. Source777049/04F
treats physical stages11 and7 as terminal cases; the current port's dedicated
stage11/legacy stage7 result paths are retained. No score, boss HP, stage, or
progress was modified by an emulator or host during this authoring task.

## Two isolated reproducible components

The first component consumes the frozen ID13 candidate FBD9 and makes14
disjoint writes,140 declared bytes/126 changed bytes. Four relocated immutable
tables occupy100 bytes within the exact112-byte suballocationD3FB10..D3FB80.
It changes native row indexing from4*row+(progress−3) to5*row+(progress−5),
replaces the four producer table pointers, and skips the legacy scheduler call.

Both stage getters retain their existing state-owner load. One branch bypasses
each temporary player-character override:08582C44→08582C6C and
08584A04→08584A2C. The public getter returns actual stage. The legacy getter
retains the previously proved analog map8→0,9→6,10→3,11→7 for its four
eight-entry consumers. The stage11 priority helper08629500 is unchanged.

- Builder `tools/build_campaign_stage_progression.py`, SHA-256
  `91214454AEA2B90B8FC394C0E613A4B2CD3FC71A12B58A82C270531E5CA77699`.
- Frozen output `build/campaign-stage-progression-v80-20261117/component.gba`,
  SHA-256 `ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9`.
- Manifest SHA-256
  `54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55`.
- Author execution:2,876 campaign cases,8,192 getter cases,seven meaningful
  negative controls. Independent producer audit:
  `1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0`.

ADBF alone is not sufficient to integrate: the larger progress domain also
reaches the following previously short consumers. Its files remain frozen.

## Progress-indexed AI and round label

All five calls to native progress getter080C8248 belong to one AI initializer:
080C6EE8,6F78,6FB0,6FD8,7004. This getter reads0300232E, independently of
physical stage or RNG row. Source782C34/93/BB/DF and782D08 read the same
config+1E field. The source segment base is raw782970.

| Source pointer table | Source rows | Native pointer table | Value contract |
| --- | --- | --- | --- |
| +DD | B9,C5,D1 | 080C7048 | three12-byte rows; byte addition then mask0F |
| +107 | E3,EF,FB | 080C7054 | three12-byte rows; unsigned byte added to halfword |
| +131 | 10D,119,125 | 080C7060 | three12-byte rows; stored after mask7F |
| +17F | 137,14F,167 | 080C706C | three12-halfword rows; signed native halfword addition |

All81 retained byte entries match the source exactly. All27 retained native
halfwords equal floor(source*4/5), including518→414,444→355 and148→118.
Only this fourth family uses that established commercial conversion. No global
clock or physics scaling is inferred. Existing native rows were nine entries
long, so progress9/10 could read the following row or pointer data.

The separate difficulty-zero table at source+185 contains13 bytes
`7,7,6,6,5,5,4,4,3,3,3,3,3`. Its first ten native bytes match. The correction
relocates the full source table and redirects the existing ADR at080C6EEC via
a12-byte adapter. The existing getter, field arithmetic, and difficulty owners
remain unchanged.

The round-label reader080B5FB0 also uses progress. Source77E389 compares10
for the final label; other rounds render decimal(progress+1). Native previously
compared7 and rendered one digit. At progress9 the correction writes digit1
and digit0 tiles2215/2214, then seven blank2201 cells. Progress0..8 retains
the old one-digit path and eight blanks; progress10 enters the existing final
label copy at080B6044. The continue bypass remains unchanged. All numeric paths
write exactly nine halfwords after the seven-word prefix, preserving the
16-word row and following mirrored-copy continuation.

The second component consumes ADBF and makes29 disjoint writes,313 declared
bytes/297 changed bytes. It uses the exact residualD3FEE0..D40000 allocation:
byte rowsFEE0..FF4C, halfword rowsFF4C..FF94, first tableFF94..FFA1,
HUD helperFFA4..FFD8, and initial-AI adapterFFDC..FFE8. Both component
allocations are contained in the existingD33000..D40000 owner, are disjoint
from audio, evolution table, ID13, and preceding campaign writes, are initially
allFF, and have zero conservative incoming-reference hits. No scanner exceptions
were required. Whole-image inverses recover each exact predecessor.

- Builder `tools/build_campaign_progression_consumers.py`, SHA-256
  `1B1E669C90CEB4D7736A97D84052613158625C91B3D955D98EE01DECA449CA04`.
- Output `build/campaign-stage-progression-v80-20261117-r2/component.gba`,
  SHA-256 `933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775`.
- Manifest SHA-256
  `6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C`.
- Author execution:36 typed AI row cases,13 initial table cases,11 HUD cases,
  and eight negative controls. The harness adds only exact retained instruction
  formsE19500F0 (register-offset LDRSH) andE0C500B2 (post-index STRH) to the
  frozen ARM interpreter. The final-label case stops before the unchanged DMA
  copy with its exact source, destination, and16-halfword count verified.
- Independent r2 audit at
  `build/campaign-stage-consumers-independent-v80-20261117-r2/audit.json`,
  SHA-256 `3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84`,
  passes864 typed AI-store cases,13 initial lookups,352 HUD cases through the
  actual native fill loop, ten negative controls, and both the r2 and combined
  FBD9 whole-image inverses. It found no candidate defect.

## Review and runtime boundary

The independent direct-stage review covers expanded12-row initializer, update,
object, collision, and camera consumers plus the four legacy getter users.
The only newly unsafe physical-stage table found was the CPU table, included
atomically in the first component. The subsequent progression review found
the AI and HUD consumers above, included in the second component. Final review
artifacts and gameplay results are owned by the parent/reviewers and should be
read alongside this author record; this file does not predeclare their result.

The smallest first-entry runtime discriminator is0808B70C, before the producer
restores registers. With progress0, all player identities must produce physical
stage8 and CPU13. CPU form is P1 form XOR1 only when P1 is13, otherwise0.
Record the actual progress/RNG row, committed stage/CPU, and subsequent stage
initializer; do not write these values into the guest to obtain the witness.
This first-entry witness alone cannot establish all later stages or terminal
completion. Alternate source mode+25 bit01-set remains outside the established
clean1.5 native-owner scope.
