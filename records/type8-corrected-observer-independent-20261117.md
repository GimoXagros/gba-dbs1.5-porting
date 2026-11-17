# Corrected type8 observer: independent delta review

Final corrected wrapper `844C896950AFFDB42B255CB843AEE8F2354A61237E0997506D0A74EAC81B00EC`
is independently PASS. Report
`build/type8-corrected-delta-independent-final-20261117/report.json` is
`F34ADBF62A1EDEEB1D3E7D0DB421A6BA6F9099463BB182A327CAFB47AFC0A6F5`.
This review executes the new delta only; the completed E999/F393 suites were
not repeated.

The actual transformed Lua is checked against the complete E999 predecessor.
Changes are restricted to the75BD ROM pin, bounded first-evidence buffers,
their file output, and one nested F393 ROM substitution. The F393 input loop,
assisted write rules, failure guards and completion rules remain exact. The
existing close insertion still closes the journal before the completion marker.

The fixed8667..8673 window retains at most256 rows. A second buffer retains the
first true evolved-air selector through a correct event16 store, within the
same or next core and at most32 rows. It verifies the actual scratch subtype
0..3 against record `0836C2AC + subtype*32`. This matters because all four
subtypes are valid event16 paths. The first completed chain stays preserved
after later ring rollover.

The independent fixture executes953 observed events. It confirms first256 and
last256 ring rows, accepts subtype1, and refuses candidates with a false
selector condition, a wrong record, an expired core window or32-row overflow.
It checks the effective parent code byte-for-byte and supplies no game-writing
or input APIs. The author's separate composed fixture is `C7581713`, covering
the retained actual campaign/driver/observer composition.

The root host `18DDDFCFE48DD615B6F64A2B46755D270831428FE951B72A2859CCB747366864`
has an exact seven-group inverse to the frozen `1E18406F` host. Only fresh output
identity, script/pin paths, ROM source/hash and observation label change.
Pins `0126D44047D3AD655DA84C34E3DF75CBC33360CAD5B3450CE335B57AAD0DCD2B`
match all seven actual Lua files. The full120000-frame/1800-second bounds,
hidden launch, authorized score/HP writes and strict completion assertion stay
unchanged.

## Why the runtime witness is independent of core8671

The old actual journal already contains earlier evolved-ground type8 reads at
cores8483,8541 and8599. Each indexes short table `0836BEA4` with ID13 and wrongly
selects airborne record `0836C2CC`/event16 for subtype1. The corrected ground
path instead selects `0836C24C`/event15. These valid-but-wrong old reactions can
change gameplay timing before the later invalid event36. The positive witness
must therefore prove the correct selected table/record/event, without requiring
the old absolute frame. The original fixed window is retained as comparison
evidence, not a success condition.

`tools/verify_type8_corrected_capture.py` owns the subsequent narrow actual
event16 chain check. It requires a root-finalized run, the first causal chain
and bounded native P1 command data. Any later invalid-producer guard or other
failure is reported separately and does not erase this scoped witness. Campaign
completion, write-ledger and visual QA remain separately owned. No emulator,
main build or Git changes were made by this reviewer.

## Finalized75BD runtime: bounded evidence only

The root's corrected run `build/bizhawk-type8-corrected-v81-20261117-a` ended
at core120001 with `bounded-no-activation`; the strict full-campaign assertion
exited1. The narrow actual report is
`build/type8-corrected-causal-qa-final-20261117/report.json` with status
`TYPE8_CORRECTED_WITNESS_NOT_OBSERVED`.

There is **no actual event16 causal-pass claim**. The first-chain count is0
and no evolved-air selector hook fired during the typed CPU13 observation.
At cores8667..8673 this run instead retains base resource `086156B4` and
event0C. The source-correct four-table implementation remains independently
verified by0A5E, but this altered gameplay path did not exercise the particular
evolved-air event16 witness.

The invalid-producer guard did not fire, and all127 retained collision producer
rows have valid types. Campaign producers and active owners reached progress0,
1 and2; the final reported stage is9 with CPU14. The last retained collision
producer is core20164; the final clock is7177. The final CPU snapshot is in
undefined mode (`CPSR4000009B`, PC00000394, LR=E3A00004), so the frame cap
does not establish continued game execution or campaign completion. The new
AI indirect-call failure is tracked separately from the type8 table repair.
