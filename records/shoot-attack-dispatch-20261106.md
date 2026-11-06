# Shoot attack types 1A and 1B: isolated native consumer repair

The actual converted Shoot children contain attack types `1A` and `1B`. The retained native dispatcher has eighteen executable entries for `08..19`; the next two words are the unrelated RAM literals `03004D28` and `03004D20`. Dispatching the new types therefore interpreted RAM addresses as code. This is a source-to-native consumer mismatch, not a demonstrated cause of the earlier E5 capture.

## Artifact and scope

- Builder: `tools/build_shoot_attack_dispatch.py`, SHA256 `51DFDA6EBDDD4F67AF909DAAD4749B18D0AE179278BD4D351DA6407DAB7B4A79`.
- Exact predecessor: v69 `72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC`.
- Isolated output: `build/shoot-attack-dispatch-20261106-b/attack.gba`, SHA256 `B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B`.
- Manifest: `build/shoot-attack-dispatch-20261106-b/attack.json`, SHA256 `20B71A90BB1D745EF9DB48537121869E2CB535BF175C3E5A22906B9625A9F352`.
- Only declared writes: raw `36EB9C..36EBA0` (4 bytes) and `6FD000..6FD720` (1824 bytes), with 1375 bytes actually changed. The complete reservation `6FD000..6FD800` was FF and had no conservatively decoded inbound references, including unaligned pointers, ROM mirrors, ARM branches/literals/ADR and Thumb branches/literals/ADR/BL/BLX. The unused reservation tail remains FF.
- External Shoot entry remains closed. This does not approve the incomplete player coordinate domain, terminal camera ownership, actual Shoot entry/exit, or runtime behavior. No emulator, save, or guest-memory access was used.

## Dispatch and calling convention

The single replaced instruction is native `0836EB9C ADD r8,pc,#4`. Its new tail branch reaches `086FD000`. The shim preserves r0, ip, SP, LR and CPSR flags. Existing r1 values take the exact original load/BX path at `0836EBA0`, with r8 restored to the old table address `0836EBA8`. The eighteen old entries and the following literal pool are unchanged. The earlier evolved-form remapping is also unchanged.

The two new cases use already-produced r1 values `24` and `26`, corresponding to `2*(type-8)`. At this boundary r4 is the attacker, r5 is the victim, and fp is the existing native guest base. New handlers use signed HP at victim+64. Dead victims set attack metadata byte `03004D26` to zero and tail into the existing normal dead reaction at `0836ECF4`.

The alive handlers reproduce source `760B59` (type1A) and `760BD1` (type1B): set victim+8 bit8000, create the existing impact effect through `0835972C` using native collision point `030048C0` and flags8002, then clear victim+8 bits00E0. Type1A also plays the existing source8F/native33 sound. Five complete fifteen-character views reproduce source tables30F2,3110,303E,305C,312E. The existing generic descriptor consumer `0836F3B8` performs the normal read and common reaction tail.

## Exact existing record and callback oracles

| New source records | Original source records | Retail native records | Rows |
|---|---|---|---:|
| 763658 | 3A6FCE | 0836C12C | 4 |
| 7636D8 | 3A704E | 0836C1AC | 4 |
| 763758 | 3A724E | 0836C3AC | 3 |

Each pair has identical flags, event and all 24 metadata bytes. The builder copies the existing retail-converted native records and changes only their callback pointers. No new timing or velocity conversion is inferred. The two evolved type1A views retain the existing normal records at `0836C22C` and `0836C2AC`.

The new source constructors17DF,1905,19B6 each call source `4090:3030` before their shared reaction initialization. The retained native equivalent is `08341034`; it performs HP reduction and orb effects and is called once by each new wrapper. These effects are not omitted. Source caller76128A..76129C and native0836AD50..0836AD68 positively establish the helper and field correspondence; native helper plus pool341034..34136C remains byte-identical to retail.

The constructors deliberately omit the normal hitstop/freeze service because the new source callbacks install their continuations directly. Each wrapper saves LR, calls08341034, copies the exact local-branch-only native initialization body, stores the existing equivalent continuation callback, restores LR and returns.

| Wrapper | Copied native body | Installed continuation | Source continuation correspondence |
|---|---|---|---|
| 086FD280 | 0836A838..0836A880 | 0836A8AC | 7617E7..7618D5 vs760FF1..7610DF, 71 instructions |
| 086FD300 | 0836AAC4..0836AAEC | 0836AB18 | 7618FB..761986 vs761143..7611CE, 43 instructions |
| 086FD380 | 0836AE98..0836AF38 | 0836AF64 | 7619F3..761DD3 vs7613CF..7617AF, 336 instructions |

The source continuations match after internal branch/callback relocation; external callees remain the same. The existing native continuation graph retains previously repaired character follow-up tables. The builder pins the actual v69 dependency bytes rather than overwriting those repairs with retail code.

## Validation

Two isolated builds produced byte-identical ROMs. The final manifest extends the helper dependency through its last literal at341368; historical-a retains the earlier manifest.

The builder checks all four input identities, exact source table populations, all eleven source/retail record correspondences, exact constructor prefixes and shared source bodies, retained native services, complete free-space ownership, and whole-ROM inverse. Independent `tools/verify_shoot_attack_dispatch.py` is frozen at SHA256 `695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698`. Its actual-b and repeat reports are byte-identical SHA256 `02E7819CC861561CC8E747683420294B7CB0F9A691AE2BEF4A355261F29368FD`: 832 dispatch cases, 366 handler/metadata cases, 44 constructor cases and 22 direct negatives pass, including the corrected full helper literal pool. See `records/shoot-child-attack-qa-20261106.md`.

Reproduction:

```powershell
python tools/build_shoot_attack_dispatch.py BEFORE.gba RETAIL.gba OLD.wsc SOURCE.wsc OUTPUT.gba --manifest OUTPUT.json
```

All original inputs must match the pinned identities. The builder refuses to overwrite an input ROM.
