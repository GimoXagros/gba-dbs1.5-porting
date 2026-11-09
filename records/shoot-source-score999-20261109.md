# Authorized original-source P1 D-Spirit999 module

This module implements the user's explicit permission to hold the original
reference game's P1 D-Spirit score at999. It changes no ROM, final GBA port,
HP, stage, progress, callback, register, timer or save field. Root owns the
separate saved-copy launcher/runtime; no emulator or guest write was performed
during this module's authoring or mock verification.

| Artifact | SHA256 |
| --- | --- |
| `tools/bizhawk_wsc_score999.lua` | `F94DA2687D8445F4464F68B427B7088A00FC296E4B56D618BABA596B864EB8F8` |
| `tools/verify_wsc_score999.py` | `ADC538BFDF06B9091CC9DB53F7F9C0E9EC9A9176AA35991390C14C2F1AABB55B` |
| `build/wsc-score999-20261109/proof.json` | `CA7006BAFA55671B986F890A28B9AAA84066668A59CE03D716F760C94E0D32A9` |

## Exact owner and single write

Source constructor `743630..63F` assigns player index at actor+10, initializes
HP WORD+50 to8 and score WORD+52 to0. FIRST is the payload handle at
`1000:065C`, accessed by the existing SRAM memory domain at065C. Its physical
source actor is `C000+FIRST`. The sole write is little-endian WORD999 at
`C000+FIRST+52`;999 is `E7 03`. It is computed from the live handle, not fixed
to a previously captured actor address.

The module requires mode7, single-player mode word0050=0, normal game-kind
03D0=0, controlled-player byte03CC=0, unpaused03CD low3bits, and stage0..10
except7. FIRST and SECOND must be distinct valid52-slot payload handles:
0024..3654, stride0110. FIRST's task-status halfword at payload-6 must have
active bit2; its actor kind low nibble must be0, player index+10 must be0,
and opponent link+14 must equal SECOND. Stage7's HP victory and stage11 Shoot
are excluded. Menus, initialization and result modes cannot write.

If already999, nothing is written. Otherwise the module performs one
`mainmemory.write_u16_le` call, checks the999 readback, and checks unchanged
P1 HP+50, adjacent+54 and P2 score. Every actual write is recorded in
`score999-writes.txt` with frame, stage, live handle/address, previous score,
HP/adjacent/P2 witnesses and exact width2.

## One source-backed hook and supported consumers

The hook is source raw7417A1 / physical0417A1. Source battle collision/orb
processing runs earlier at74161F. The hook immediately precedes the four875A
HUD calls; source7417B5 then checks HP/timeout and7417FE can dispatch the real
result route. It uses the already calibrated BizHawk2.11.1 swapped callback
binding: `event.on_bus_write` observes opcode fetch. Each delivery verifies
PS:PC equals physical opcode address+1 before any write.

This placement matters: source742B50 increments score but742B53..5A clamps an
orb award to250. A pre-frame-only999 write could therefore be undone by an
orb pickup during the final frame. The single post-award hook restores999
before both HUD and result processing, without adding a second hook.

Source HUD875A:00EC at78769E explicitly excludes stages7/11, selects FIRST or
SECOND using03CC, reads score WORD+52, clamps only its AX display value to999,
then renders three decimal digits using division by100 and10. Thus999 is
directly supported by that HUD consumer.

Source result export77243A..450 reads score WORD+52 but stores only AL into
1000:066E/066F. Consequently999 exports231. The7755C9 win-streak consumer
zero-extends those bytes and uses unsigned comparison at77560B. A separate
stats consumer at76D00C uses signed byte comparison, interpreting231 as-25.
The module preserves both original consumers and does not claim that999
guarantees every ranking/continuation outcome, especially against scores>=231.

## Interface and verification

`dofile` returns `tick()`, `status()` and `finish()`. Tick installs the one hook
once; repeated ticks are harmless. It needs only existing `output` and
`callback_order=bizhawk2111-rew` userdata. Status reports enabled/finished,
hits/eligible/writes, value999, bytes_per_write2 and hook_raw. Finish disables
future callback writes, appends a ledger summary and returns status.

The actual Lua module passes66 finite mock guard cases, idempotent install,
unchanged-score suppression, post-pickup restoration, calibration rejection,
adjacent preservation and final disablement. Ten mutations reject HP targeting,
wrong value, boss scope, wrong owner, wrong hook and five actual source changes.
These are host mocks with source instruction guards, not runtime success.
Independent module/driver integration QA is separate.

## Parked ordinary-input correction

The previous v4 capture already scored4→5 against8 in Stage1; attacks/collection
were not universally broken. A concrete source control defect is that idle
668E:115D and walk11C9 poll fresh B helper0224 before movement helper06A6
updates facing. DefaultID0 neutral attacks reach P4 rows0/1 or5, whose held-
direction turn flags are zero. Simultaneous direction reversal+B can therefore
commit a neutral attack with stale presentation facing at actor+9E bit4000.
The proposed v5 was a narrowly scoped fresh-B veto until the requested facing
is actually present, preserving airborne/unrelated actions. It was parked
before authoring for this explicitly authorized score experiment. Existing
captures do not contain per-attack callback/facing records, so this is not
claimed as the observed sole cause of the earlier losses.

## Follow-up: actual campaign advancement versus signed statistics

The actual main-mode table at `74FACC+8*12` selects `76F1:0000` / raw776F10
for result-mode initialization. At776F50..61 it clears CX/DX before loading
066E/F into CL/DL, so the exported bytes become positive16-bit scores.
The WORD compare at776FC6 uses JE for a tie, JB for P1 loss and JG for P1
win. With zero-extended values0..255, that JG cannot interpret231 as-25.
P1 WIN reaches777014 and sets0100 in source0068; the presentation state
receives WIN flag0010 at777011/41. The separate winner-label selection at
7772A9 likewise compares WORD scores with unsigned JB for controlled P1.

The actual exit callback `76F1:0B93` / raw777AA3 tests that WIN flag at777AD1.
On the ordinary campaign branch,0068 bit0 is clear:777AEB increments the BYTE
campaign-order field `004E+1E=006C`, then777AEF calls `76F1:17B2` / raw7786C2.
That source stage selector reads006C at7786DC, dispatches through its179C
table and writes the next actual stage at778725 (or its boss branch77871D).
Its first five fixed stage bytes are8,1,9,6,10; order10 selects stage7.
Thus the score-only module's ordinary-stage guard also covers the actual
intermediate stages9/10 without changing their stage fields itself.

The signed statistics call is a different positive branch: result initializer
777044 calls `76F1:15C9` / raw7784D9, whose7784E9 tests0068 bit0 and7784EE
skips the entire statistics block when it is clear. Only the bit-set branch
calls `6B4A:1B18` / raw76CFB8 at778526. That routine increments per-character
played/win counters under `0C00:392C`, with the signed AL/AH compare at76D00C;
it does not supply the campaign WIN flag or the order increment above.
The ordinary campaign therefore neither invokes that signed comparison nor
uses its win counter to decide the result. The previously established Shoot
case5 gate at771F8A uses difficulty and0068 progress0400, not those counters.

The remaining numerical limitation is truncation, not signed campaign logic:
999 exports231, so actual result P1 wins against opponent scores0..230, ties
231 and loses232..250. All251 natural opponent scores were checked against
the source compare semantics. No module, driver, ROM, runtime or save was
changed by this follow-up; only this record was appended.
