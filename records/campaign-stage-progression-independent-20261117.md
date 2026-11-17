# Campaign stage progression: independent producer verification

The isolated campaign component passes independent source and actual-ARM
verification. This is a producer/getter/allocation result, not a complete
campaign playthrough or blanket clearance of every downstream consumer.
The separate direct-stage/progress-display review remains relevant before
main integration.

Input FBD9 SHA-256:
`FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD`.
Reviewed output `build/campaign-stage-progression-v80-20261117/component.gba`:
`ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9`.
Its manifest is `54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55`.
New verifier `tools/verify_campaign_stage_progression.py` imports no production
builder. Final report
`build/campaign-stage-progression-independent-v80-20261117/audit.json` is
`1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0`.

## Independent source model

The source table at raw `778674` begins with physical stages `8,1,9,6,10`.
Eight five-byte rows at `778679` select the next five stages; each row is a
permutation of `0,2,3,4,5`. The final stage is 7. Every row therefore visits
all eleven physical stages `0..10` exactly once, with stage7 only at the end.
The source CPU map at `7786A1` is `0,1,2,5,6,4,3,15,13,14,11`, and the
eleven dispatch words at `7786AC` contain five early, five RNG-row, and one
final handler target.

Source `778703..71A` independently establishes index `row*5 + progress-5`.
The row is config `+1F`: source `78074F..75B` calls RNG, masks by 7 and stores
that byte. It is not difficulty. Progress is config `+1E`; source `777AE3..AF4`
increments it before invoking the stage producer unless flag0001 suppresses
that ordinary successor. Native owners are `0300232F` and `0300232E`.
The initializer, RNG writer, and successor instructions remain byte-identical
to retail GBA and the FBD9 input.

Source `778725..731` invokes the legacy challenge scheduler only when source
config `+25 & 0001` is set. The clean default mode has that bit clear, so the
candidate removes the unconditional retail call. This verifies default-mode
semantics only; it neither invents a native +25 mode owner nor implements the
source alternate mode. The retained special flag0010 branch is different:
it preserves physical stage and progress, clears0010, sets0020 and selects
CPU11. Source `7786E8..6F9` proves that behavior directly.

The producer stores the CPU form as zero unless the selected CPU identity
matches the player, in which case it uses player-form XOR1. The independent
reference includes this source `778738..748` rule, rather than checking only
stage and CPU IDs.

## Actual native execution

The independent verifier executes the emitted ARM instructions, using the
existing hash-pinned strict interpreter. The source reference reads the WSC
tables and separately transcribes the documented branch behavior.

| Partition | Cases |
|---|---:|
| Eleven progress values × eight RNG rows × sixteen player IDs × two forms | 2,816 |
| Retained non0010 flag combinations across all progress/row values | 440 |
| Dedicated0010 path, including invalid progress/row values that must be bypassed | 1,536 |
| Both getters, physical stages0..11, all sixteen player IDs | 384 |
| Actual RNG mask/store with low and high boundary values | 8 |
| Fresh stage/progress/row initialization | 1 |
| Ordinary successor progress0..9, all rows, locked/unlocked flag0001 | 160 |

Each producer case checks the complete configuration and scene outcomes,
preserved registers/stack, absence of an extra challenge call, and the exact
typed ROM table read addresses. Unexpected changes to neighboring config
bytes are rejected. The function introduces no new RAM owner. The dedicated
0010 path performs no campaign table reads, even with progress/row255.

The public getter now returns actual physical stage independently of player
identity. The retail getter preserves the existing analog map
`8→0, 9→6, 10→3, 11→7`. Neither writes config. Stage11 stays outside the
normal eleven-stage campaign table; these getter tests preserve its existing
dedicated meaning without rerunning the already proven Shoot flow.

The actual successor retains progress and RNG-row owners. Cases0..9 reach
the next valid entry, including9→10/final stage7. The verifier does not call
the ordinary successor at final progress10 and pretend source progress11 is
valid. The source has eleven dispatch entries, and the existing terminal
caller is a separate established flow. No recovery behavior for corrupted
normal progress/RNG indexes is fabricated.

Ten semantic mutations are rejected without relying on candidate hashes:
wrong first stage, stride4, old opening threshold3, adjacent-field RNG read,
final entry incorrectly entering the RNG block, missing CPU13, restored
unconditional challenge, dedicated flag0010 selecting CPU15, and restored
character overrides in either getter. The ordinary/challenge tests execute
actual retained instructions; the RNG service return is the explicit boundary
used only to exercise the actual mask/store sequence.

## Allocation and complete inverse

The independent write definition contains four tables (100 bytes) and ten
four-byte code/literal edits: 14 spans, 140 declared bytes, 126 changed bytes.
The checker verifies both exact before/after bytes and reconstructs all
16 MiB of FBD9 by reversing only those spans.

The new tables occupy `D3FB10..D3FB7C`, inside the explicitly bounded
`D3FB10..D3FB80` suballocation of the existing `D33000..D40000` audio
reservation. The source-backed table/ID13 owner manifests remain pinned.
Every relevant earlier audio write and every earlier table/ID13 write is
checked against the input and again against the output. ID13's prior
suballocation ends at D3FA00 and does not overlap this range.

The conservative all-ROM encoded-pointer/ARM/Thumb/literal/ADR scan reports
zero incoming references for this exact new interval. The initially proposed
wider D3FA00 interval would trigger conservative Thumb interpretations of
existing ARM bytes; the author selected this smaller zero-hit range instead.
No scanner exception or assumption that blank bytes imply ownership is used.

## Remaining integration boundary

The scoped physical-stage consumer review is
`records/campaign-native-stage-consumers-v79-20261117.md`. It identifies the
retail CPU table as a proven unsafe direct physical-stage index; this candidate
replaces it with the eleven source CPU entries. Existing public consumers and
retail analog getters have separate bounded tables described there.

During that review, a separate progress display consumer at `080B5FB0` was
identified with a legacy compare against7. Its source semantics were still
under review when this producer report was frozen. This report does not
claim that unrelated progress display behavior is correct. Root owns that
integration decision, runtime capture, main wiring and publication. This
workstream launches no emulator or whole build and modifies no main builder,
original ROM, save, or frozen prior artifact.
