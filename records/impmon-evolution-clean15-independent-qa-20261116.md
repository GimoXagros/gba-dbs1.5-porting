# Impmon collector and 6F campaign preflight

Independent preflight passes for the isolated 8C72 candidate and
the private 6F campaign wrapper. This record covers the source
comparison, the native collector change and the launch boundary.

## Source collector

The original source WSC 1.0 first checks for actor 11 at raw
3927F2 and takes a special collector path. C344 retains that
identity-only gate at native 083546F8–08354700.

Source WSC 1.5 adds an ES:0073 mask 0x01 test at raw 742AD2.
With the bit clear, the branch at 742AD8 enters the ordinary
collector route at 742B00 even for actor 11. That route still
excludes boss sentinel 15 and installs the ordinary evolution
callback for the other identities. The 1.5 startup at 74FC0D–74FC4A
sets DS to 1000, initializes game base 004E, and clears byte
004E+25. The same bit conditions the source roster at
7787F3, 778808 and 778826. A separate source table-driven lifecycle
can write that byte at 780B36, so the flag-set route remains a
distinct source condition.

The numeric C344 offset 03002335 does not establish a native owner.
In four completed ordinary C344 capture groups, all 23 full IWRAM
snapshots hold zero there. A candidate native writer at 080C6DF8
resolves through its actual preceding literal to 03004DAD, a
different address. The isolated change implements the existing
flag-clear 1.5 mode scope without inventing an owner.

## Native component

The little-endian ARM word at 08354700 changes from 1A00000C to
EA00000C, making its existing branch to 08354738 unconditional.
Only raw byte 354703 differs. The whole 16 MiB inverse equals
C344. The independent audit decoded the actual branch words for
64 combinations of actor ID and object kind. Only kind-8 actor 11
changes path. Other kinds retain their original branch, and boss
15 retains the guard. The ordinary path stores fighter callback
0835A0F8 and links the collectible to that fighter.

The retained loader's group-1 actor 11 row resolves P0, P1,
both palette selectors and typed P4. Its pointers are unchanged;
the author exercised the existing source record 41 resource
checks separately. The independent audit did not repeat that suite.

## Campaign launch review

The frozen score-assisted candidate uses P1 actor 0 in Normal
difficulty and observes the native CPU 11 selection decision.
The scope permits a single write kind, the 16-bit live P1 score
at actor plus 0x66 to 999, up to 512 changes. The 337E observer
corrects the CPU kind guard to match the live type 1 confirmed
from earlier frozen IWRAM/EWRAM. Independent Lua 5.4 cases verify
authorization, writer address/width/value, no second write at
999, and refusal for wrong kind, dead CPU and menu state.

The 049D wrapper adds two close calls to the through-line
campaign script. Independent Lua 5.4 tests covered the exact
nested composition, normal completion ordering, the canonical
alias failure ordering, the separate alignment observation's
failure ordering, and missing/duplicate anchors. Score, music,
and alignment journals close before the marker on normal
completion and on the copied-cache branch failure. The
alignment witness has its own terminal failure marker.

| Evidence | SHA-256 |
| --- | --- |
| Isolated component | 8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8 |
| Independent isolated audit | 495B06A0E386D84D8B7506E6DDA8B9208F301F15885C2C1DA9BBDE200ADF2A51 |
| Private 6F launcher | 3C86C6FB7DA03671ED2A9CB0E30A30ACFFC3AC5F0FE01EA5F02D14F042315712 |
| 049D composed effective Lua | B4EF29CA3F0AC9470002A79A8C0EC32FF0F086FCB7408A56DA69198B00D8576A |

The preflight concerns the isolated flag-clear collector and
score-assisted launch. Actual native CPU 11 emergence, Calumon
contact, song 6F pause and resume, and the stage return require
the completed gameplay record.

## Deterministic integration gate

The standalone verifier tools/verify_impmon_evolution_gate.py
uses the exact C344 and 8C72 images, commercial 996D GBA,
original 5822 WSC 1.0, and C415 WSC 1.5 images. Its arguments are
--before, --after, --gba, --wsc10, --wsc15 and --report. It runs
without the authoring builder, emulator, or old test suites.

The verifier SHA-256 is
8AD86CF8A65D2D46612399907BA9DB44E21ABE1975087B8AF106570753193705.
The path-independent gate report
build/impmon-evolution-clean15-independent-qa-20261116/gate.json
has SHA-256
D727C5DC1D35E2C743F8C3B8E6D24BC096AFFACBE45172FE078DD5196A250661.
