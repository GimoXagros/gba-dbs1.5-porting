# Terminal guard: reciprocal auxiliary owner correction

The completed FF3A palette repair trial reaches terminal `085CD510`, then
records `native-guard-aux18-not-upper` at core69932. This is an observed
owner-predicate failure after the earlier palette self-loop was removed,
not a new scheduler stall. The capture integrity and progression are already
audited in `shoot-native-terminal-palette-capture-qa-20261109.md`; that audit
and the historical source/lifetime proofs are reused here.

## Source and native ownership

The auxiliary actor has distinct opponent and owner fields. Source WSC1.5
initializer `[747A68,747E72)` and death path `[74868D,7486D9)` are pinned by
the frozen builder. The source image SHA256 is
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The native constructor loads SECOND from `030048A0` and FIRST from
`0300489C`. Its positive stores establish:

| Native instruction | Meaning |
|---|---|
| `085BC29C E5846028` | auxiliary+28 = SECOND, its owning upper actor |
| `085BC2A8 E5847018` | auxiliary+18 = FIRST, its opponent |
| `085BC380 E5864028` | SECOND+28 = auxiliary, the reciprocal link |

The retained fatal adapter `085CD960..085CD99F`, auxiliary death callbacks
`085BF204`, `085BF400`, final `085BF600`, and same-update transition
`085CDA70..085CDA83` do not relink those fields. Their complete bounded
bodies and the constructor are pinned in `component.json`. This reuses
the established constructor/fatal/death proof rather than repeating the
full lifetime audit or assuming a terminal-only link transition.

The actual core69932 capture agrees: auxiliary+18 is FIRST `02011710`,
auxiliary+28 is SECOND `02011828`; SECOND+28 points back to the auxiliary.
Upper/auxiliary final callbacks are `085BF200`/`085BF600`. Requiring
auxiliary+18 to equal SECOND confuses the opponent with the owner.

## Frozen minimal component

`tools/build_shoot_terminal_owner_link.py` changes only ROM offset
`6FFC00`: `E5960018` (`LDR r0,[r6,#18]`) becomes `E5960028`
(`LDR r0,[r6,#28]`). The guard therefore checks
`SECOND+28 == AUX && AUX+28 == SECOND`. The valid opponent link stays
unchanged; no extra opponent predicate is added. All other guard tests,
callbacks, queues, storage and RAM ownership remain unchanged.

This is four declared bytes with one changed byte, with an exact whole-ROM
inverse to FF3A. Production `build(before, source)` requires the complete
predecessor/source hashes, pinned bodies and exact constructor words. It
does not read a runtime capture. Optional author checks consume an explicitly
named completed fixture separately.

| Frozen artifact | SHA256 |
|---|---|
| Builder | `6C57D65740F27CFA64CC5EFE892F7FAC80BDB778D3128F6BF8BED0B5DCBC930C` |
| Input FF3A | `FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8` |
| `build/shoot-terminal-owner-link-20261109/component.gba` | `46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B` |
| `component.json` in that directory | `D6D66777FCA9BD4A6979F960DEAFBCDDF38D0CB2D3A112C3EF222B67AA2061FD` |
| `author-report.json` in that directory | `440107DD71DC3F3BC5CA52B1DBDB816DB24F9030F9A626D66BBB49C81B45892E` |

## What the existing author checks establish

Executing the old guard against final core71927 RAM reproduces the owner
refusal. The repaired guard passes that owner check but still refuses the
final outer display mapping: BG1CNT is `1F03`, while the required masked
value is `1E00`. This is preserved refusal, not proof of another actual
instruction-time failure in the repaired ROM.

The author model substitutes only BG1CNT `1E03`, observed at the earlier
core69932 guard entry, into final core71927 RAM/VRAM. That explicitly
**mixed-epoch model** reaches the accept branch with stack-only writes.
It is not an actual same-epoch guard acceptance. Eight negative controls
reject wrong reverse/forward owner, inactive auxiliary, wrong resource,
moving FIRST, bad BG velocity, extra renderer and wrong final callback;
five inverse mutation controls reject altered patch/outside bytes. These
are the frozen author results, not a newly repeated independent audit.

Actual acceptance, copied-queue substitution, IRQ execution, cleanup and
mode8 require root's controlled headless 46B3 trial and separate capture
review. The existing one-shot approved SECOND HP1 intervention and genuine
healthy checkpoint remain the runtime contract; no new source replay or
provided save is needed. Source-DI identity, general moving lifetimes,
historical E5 and final-port completion remain open.

This record was added without changing the frozen builder/component,
main build, runtime evidence or Git state. Independent ROM and observer
verification are owned separately. The next source investigation should
start from a new actual runtime failure, if one occurs.
