# Independent presentation receiver-lifetime QA — 2026-11-09

PASS for the isolated component
`84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B`
over frozen D0 experimental ROM. The actual stalled presentation's target now
survives the existing angle/trig calls. No emulator was started and no savestate
was loaded by this reviewer. Main, D0, the author files and Git were unchanged.
This is a bounded component/actual-capture instruction proof, not completion
of the hidden replay, whole scene or game.

The independent verifier imports no production builder. It reconstructs the
five instruction words at5C9108/910C/9120/9174/91A4: the first loads target
into r6; the four dereferences use r6 as base. The complete outer callback
already saves/restores r6. Exactly20 bytes are declared, five bytes change,
and replacing only those five words recovers the complete D0 predecessor.
No new code, cave, hook, task, RAM or event-forcing write is introduced.

Actual source7735D4 stores the receiver in BX;773611/773624 reuse that same
receiver after angle/trig. The original native translation used r1, but both
division arms in126A4 assign r1 before their native division thunk call.
All instructions in the closed12560→12650→126A4 and1233C/12348 helper bodies
were independently decoded; none writes r6. The exact original ARM bodies
and thunk bytes remain retail-identical.

The verifier executes the real ARM angle, trig, thunk and3524C4/352AF8/11E7C
release instructions. Two exact native non-S MUL instructions and the exact
trig register-offset signed-halfword read extend the existing strict ARM
runner. The Thumb SWI6 arithmetic boundary alone is modeled: quotient,
remainder and absolute quotient outputs, with r6 preserved. The pinned
[mGBA primary implementation](https://raw.githubusercontent.com/mgba-emu/mgba/9660a668f2093cb4aba5983f52bebf8878dc5b8b/src/gba/bios.c)
supports this register contract: its Div implementation assigns r0/r1/r3.
That reference supports the explicit service model; it does not identify or
execute the installed core's BIOS implementation. No divide-by-zero result,
hardware timing or BIOS machine-code equivalence is claimed.

The readonly completed b capture is pinned exactly:

| Capture | SHA-256 |
| --- | --- |
| Final EWRAM | `64F86BFA9A8EE96086998E2FF7294BDB1D4212457E2F7263EBAE3674B8EF5ACB` |
| Final IWRAM | `BC10319BFC772FCE8D379D02E78061B9D2C00E21116EA19A47EBE9DCA3929B12` |

The sparse readonly fixture uses those complete memory images and binds the
isolated callback's ordinary argument r4 to the captured presentation020112B0.
Its actual receiver02011828 and positions13A1/0CFB versus13A1/0D2B are inside
the inclusive +/-0100 box. The original callback executes the actual helper
path and reaches9174 with r1=0. It stops before that invalid receiver access;
the verifier does not invent BIOS memory to manufacture an original outcome.
The repaired callback reaches the same boundary with r6 still02011828 and
identical velocity writes, then naturally writes4508 from0002 to0012 and
executes real pool release on the actual presentation/header. All incoming
r0-r12, SP and LR are restored by its real enclosing frame. Intermediate CPSR
identity is not asserted.

This captured pose passes all16 incoming NZCV patterns. Another168 cases
cover inside/outside arrival bounds in all quadrants, including exact +/-0100
and one unit beyond, plus varying flags. Twenty-eight direct angle cases
cover quadrant, zero single-axis and4000 scale-branch partitions. Both actual
division arms and actual sine/cosine table reads execute. Release occurs only
for true target arrival, and every case restores the complete outer frame.

The verifier then runs the actual waiting scene5C8400 with its ordinary current
task getter bound to the captured scene header020121E8. With the original
absent event, it returns and timer6 stays6. After the repaired callback's
natural completion, the same scene consumes bit0010, decrements6→5 and reaches
the existing next-spawn entry5C8E00. No guest flag is forced to establish that
result. The next allocation/spawn body is an explicit boundary, not a claim
that the remaining scene or initializer has executed.

Twelve controls reject each omitted register substitution, off-target event/
angle/entry writes, semantic reintroduction of either postcall scratch read,
missing completion signal and loss of the outer r6/frame restore. The four
semantic controls execute before expected-byte/hash validation.

| Frozen artifact | SHA-256 |
| --- | --- |
| `tools/verify_shoot_presentation_target_lifetime.py` | `F384BDBDEDF0F10AF62AC3CE968599BA4C8BB6E3BA3A31D32DFCAE3F3C8888EC` |
| `build/shoot-presentation-target-lifetime-qa-20261109/report.json` | `3728B6B7CAE8D116B5D32FDAFD4C4205BDA8AC41415545977016B6AFE95929BE` |
| Source builder | `8C099EAD5CCA7AFD86482DC810AD15FE90DA09F429D30C86AEE95F5A9EA3C783` |
| Component manifest | `148A6143330E73A3439ABCD5A66A16DC805393392DEEA38D950F39C91F2BF31C` |

Reproduce from the repository root with a fresh output report path:

~~~powershell
python -u -X utf8 tools/verify_shoot_presentation_target_lifetime.py build/shoot-presentation-target-lifetime-20261109/component.gba build/shoot-runtime-entry-probe-20261109/experimental.gba 'C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba' 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --capture build/bizhawk-gba-shoot-entry-20261109-b --manifest build/shoot-presentation-target-lifetime-20261109/component.json --output build/shoot-presentation-target-lifetime-qa-20261109/new-report.json
~~~

Actual restored-core replay, healthy activation and any later blocker remain
root-owned runtime/capture gates. Unrelated prior suites were not rerun. The
separate nonfatal-verifier draft remains unexecuted and is not approved here.
