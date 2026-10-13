# Shoot controller components, 2026-10-13

This is a bounded native-code continuation from exact static v50. It adds
neither a complete controller nor gameplay/runtime evidence. No emulator or
supplied save was opened. The existing `0x085C0A00` `BX LR` boundary is unchanged.

## Source decision and native consumers

WSC Ver. 1.5 raw `74A208..74A345` contains `4090:9908`, its complete 64-word
dispatch table and action tails. SHA-256 is
`25FB35105253832BDC2377094FE7EDFB3B75F459026B4D4473913C7EE773CEF4`.

- Current object `+62 != 0` immediately selects `9A0E` without consuming RNG.
- Otherwise, linked target `+14` supplies unsigned X/Y fields `+26/+28`.
  X in inclusive `[0500,0900]` selects the paired action when `RNG & 3 == 0`;
  otherwise Y `>=0C00` selects `9A0E`, and lower Y selects `9A1B`.
- Outside that X band, signed byte `ES:005D` is clamped to `0..3`, then its
  sixteen-entry row is indexed by `RNG & 15`. All 64 source targets are retained:
  `99EF` 18, `99F1` 10, `9A0E` 20 and `9A1B` 16.
- `9A1B` assigns parent `9083` when Shoot flag `ES:03D8 & 40 == 0`, or selects
  auxiliary `8CDD` when that bit is set.

These native fields come from paired consumers, not a uniform-offset guess:

| Source | Native | Evidence |
|---|---|---|
| Object `+62` | `+76` | WSC 1.0 raw `394B4F/394B6A/394B72`, GBA `083701A4/083701D4/083701DC..E4` |
| Target link `+14` | `+18` | Commercial generator raw `3963AE`, GBA `08372760` |
| Linked object `+1C` | `+28` | Commercial generator raw `39639C`, GBA `08372740` |
| X/Y `+26/+28` | `+34/+36` | Same generator's immediately following coordinate reads |
| HP `+50` | `+64` | WSC 1.0 raw `3948AD`, GBA `0836FD44` |
| Scratch `+8C` | `+A2` | Paired angle-result stores raw `39604E`, GBA `083721B4` |
| Difficulty `ES:005D` | `0300231F` | Paired player HP consumers raw `3948B0`, GBA `0836FD2C..34` |

Source RNG `4FFF:1CB5`, raw `751CA5..751CC4`, and native `08012600..08012634`
update the same two-halfword recurrence with increment `3711` and byte-swap the
result. Stored halfwords and the consumed low four return bits agree. The native
32-bit return can contain high carry bits; unrestricted return identity is not
claimed. Native RNG clobbers only `r0/r8/r9` and uses `03001420..03001424`.

## Resident implementation and call contract

`tools/build_shoot_rules.py` adds three Expected Writes, 320 placed bytes and
318 changed bytes, inside the exact owned interval `5C6000..5C6500`:

| Native entry/data | Bytes | Contract |
|---|---:|---|
| `085C6000` SELECT | 180 | `r4=current object`; returns `r0=action`, preserves `r1..r12/SP`; CPSR scratch |
| `085C6200` APPLY | 76 | `r0=action`, `r1=810D callback`, `r2=8AB8 callback`, `r3=8CDD callback`, `r4=current object`; preserves `r0..r12/SP`; CPSR scratch |
| `085C6400` action table | 64 | Invertible token representation of every source dispatch target |

Actions are `0=idle`, `1=810D + 8AB8`, `2=8CDD`, `3=9083`. Action 1 assigns the
current object's callback, copies its unsigned HP halfword `+64` to `+A2`, and
assigns the linked auxiliary callback. Actions 2 and 3 assign only the linked
callback. Action 3 uses already resident parent `085BA800`.

SELECT's sole persistent side effect is zero RNG advances on the forced path,
or exactly one advance on every other path. APPLY does not call RNG. There is
no adapter between them yet: a future adapter must supply actual implemented
native callback addresses and call both with the same object/link/HP/flags
snapshot, without any intervening game update or object mutation. No address
of an absent family is embedded in this ROM, and no externally reachable entry
calls either component. The native callback live-ins are an explicit unmet
integration prerequisite, not fallback behavior.

The initial reservation `5C6000..5D0000` was only a planning budget. A scan
found ten aligned words outside the new code whose ARM branch encodings target
its unused tail `5C7B88..5CFE70`. The implementation does not dismiss those
words or claim the entire budget is free. Its narrower `5C6000..5C6500` interval
is all `FF` and has zero pre-existing aligned pointers or ARM B/BL encodings.
Any later use of the unused tail requires a new ownership audit.

## Independent static verification

`tools/verify_shoot_rules.py` imports no generator. It decodes every final
instruction and independently checks branch conditions, branch/call targets,
access widths, native field/global consumers, source table inverse, literal
roles, return registers, Expected Write containment and external references.
The builder separately round-trips all 60 ARM7TDMI instructions, with the
16 literal bytes excluded from code. The only pointer into the owned interval
is the selector's internal action-table literal.

A finite specification comparison covers 262,144 branch-partition cases:
all 256 difficulty bytes, all sixteen consumed RNG-bit outcomes, both forced
countdown states, X boundary/interior representatives, both Y partitions and
both relevant Shoot-bit states. This is static specification comparison, not
execution of either CPU or the game. Twelve meaningful altered-code/table
cases are rejected, including signedness, threshold inclusivity, RNG target,
linked-object field, callback argument, HP source, adjacent-field overwrite and
wrong parent/table targets.

- Input v50: `C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
- Rules component output: `FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C`.
- Independent report: `7F4DFF7CB239B0C90A80A2168FC1D9BF5F9F05605E7953084A8203C2C8FC7678`.
- Standalone evidence: ignored `build/shoot-rules-20261013/`.

Standalone command interfaces:

```text
py -3 tools/build_shoot_rules.py <v50> <USA-GBA> <WSC-1.0> <WSC-1.5> <rules-output> --manifest <build-json>
py -3 tools/verify_shoot_rules.py <v50> <rules-output> <USA-GBA> <WSC-1.0> <WSC-1.5> --output <verification-json>
```

## Remaining finite graph and spatial-table boundary

The pre-existing source graph remains 43 entries, 6,096 code bytes and three
resolved indirect tables. This layer implements only the controller decision
and assignment components. Lower families `810D/8AB8/8CDD`, their dependencies,
the complete controller adapter, reward/win/loss/menu/exit and external entry
remain open. Family `8AB8` requests uninstalled sound `CF` and writes `ES:0720`;
constructor `933B` additionally requests `D1`. Those sounds are not substituted
with equal-numbered native sounds.

Spatial helper `8EF3` is fully bounded at source level, but is not emitted here.
Its five Y rows at `8FEF`, X threshold lists, ten-target dispatch at `8FDB` and
nine parameter rows at `8F93` select native-object data later consumed by
constructor `933B`. The loops can read beyond the intended table population
when signed captured Y exceeds `1B00`, or signed X reaches/exceeds the final
`1E00` threshold. An upstream range/lifetime proof is needed before a bounded
native rewrite; adding an unproved clamp would change source behavior. This is
an identified input-contract gap, not proof that normal source play overreads.
