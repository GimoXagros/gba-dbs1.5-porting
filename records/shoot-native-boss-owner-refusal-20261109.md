# First native attempt: wrong stage7 auxiliary kind guard

The first D0 attempt reached a healthy active stage7 boss, but the observer
refused its genuine actor pair. The sole failing pair predicate was the
auxiliary kind: the script required6, whereas the native stage7 constructor
creates kind3. This is an observer-contract error, not a failed Shoot entry,
corrupted actor or unsupported input. The earlier source advice incorrectly
applied the stage11 auxiliary contract to stage7; that advice is corrected here.

Frozen run: `build/bizhawk-gba-shoot-entry-20261109-a`. Refusal occurred at
core64229; exported memory is the next outer boundary64230, not instruction-time
RAM. At refusal the trace already records FIRST HP8, SECOND HP37, stage7,
difficulty2, progress01C0 and normal input/battle task handles. Nineteen expanded
pair predicates were evaluated against the exported RAM: eighteen pass; only
`word(aux+4)%16 == 6` fails. Constructor evidence below establishes the native
kind independently of the one-frame export delay.

| Field | Captured value |
| --- | --- |
| FIRST |02011710; kind0/index0/id0; HP8; self+14=FIRST, opponent+18=SECOND |
| SECOND |02011828; flags6303/kind3/index1/idF; HP37; self+14=SECOND, opponent+18=FIRST |
| Auxiliary global03004D3C |02011940; flags0343/**kind3**; active header02011928 flags2 |
| Reciprocal auxiliary links |SECOND+28=aux; aux+28=SECOND; aux+18=FIRST |
| Upper resources |actor+F0 P1=0834DFE0; actor+F4 P0=0834E27C |
| Auxiliary resources |actor+F0 P1=08341C00; actor+F4 P0=08341E70 |
| Controller |mode7; game-kind2; control4529=0; task callbacks08374FF4/083735BC |

Native stage7 auxiliary construction at36FE84 loads literal370094=`00000343`,
pushes it at36FE88 and calls352374 at36FE9C. Allocator35243C/352444 stores the
flags at payload+4. This whole lineage36FE6C..370034 is byte-identical to retail,
SHA256 `76FFA816A5E89667A947B9A046D1B94FE2D1F1AD0F79901A312E7CA4DE3FBF67`.
It is not a cross-platform kind-number discrepancy. Stage11 later transforms
this reused auxiliary at5BC270..284: clear lowF, OR26, clear6000 and40, store+4;
the resulting low kind is6.

Stage7 resource producers36FDC8/36FDD8 load the upper P1/P0 from37007C/370080;
36FF18/36FF28 load the lower P1/P0 from3700AC/3700B0. Native127E4 binds P1/P0
to presentation+44/+48, hence actor+F0/+F4. Stage7 links originate at36FEE4
(aux+28),36FEF0(aux+18) and370010(SECOND+28). The two source globals used there,
03004D34/03004D38, were populated from SECOND and its FIRST opponent by36FD68/74.

The minimal correction is an exact stage split, preserving all existing live
slot, actor index/id, self/opponent, reciprocal auxiliary, positive health and
active controller requirements:

| Stage | Upper kind/id and P1/P0 | Auxiliary kind and P1/P0 |
| --- | --- | --- |
|7|kind3/idF;0834DFE0/0834E27C|kind3;08341C00/08341E70|
|11|kind3/idF;085D0000/085D1000|kind6;085D029C/085D1100|

The stage11 resource producers are5C10C0/5C10D4 (upper) and5BC2D0/5BC2E4
(auxiliary), with corrected constructor bindings retained. Unknown stages or
crossed resource/kind combinations must refuse. Do not relax the guard to
generic `kind3 or kind6`. Stage7 callback370B84 in this snapshot is a genuine
moving lower callback; the gate should not require one permanently fixed callback.

The actual run recorded26 score writes and zero boss writes, then FIRST HP0
root4 at69904 and Continue at70147. It never reached the authorized bossHP1
write. Those observations do not establish a failure of the case5 selector or
Shoot scene. Root owns any minimal observer fix, genuine checkpoint and next
attempt; no observer/ROM/save edits or replay were performed for this diagnosis.

| Frozen evidence | SHA256 |
| --- | --- |
|04-typed-owner-refusal-iwram.bin|`17727C9E0A7B542781A4B1732B2A3D76C0A239AB550C6D61388E4A13069CD3AF`|
|04-typed-owner-refusal-ewram.bin|`BEEBADB0B5A220CA1F4749DD0A91F6C2D09064CDB89909DAF50511C835E5601A`|
|Frozen observer|`E620B76A96ED09E6E19DED5E3EE8134D14E62A6022A332D899E08E3493FF76FF`|
|Frozen driver|`D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D`|
