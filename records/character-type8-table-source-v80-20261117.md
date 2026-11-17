# Type8 reaction table overflow: source contract and isolated repair

The ordinary campaign capture on `933C9434…` observed the invalid producer
and its bus write at core8672, then stopped at boundary8673 before an invalid
collision dispatch was observed. This is a new
`8070` failure, distinct from the previously proved ID14 evolution-entry
`B054 → FFFFFFFF → E5` path. No previous E5, music, Shoot, or ID13 relaunch
gate was rerun or modified for this investigation.

## What the existing capture proves

`build/bizhawk-campaign-complete-v80-20261117-a/shoot-entry-first-failure.txt`
records CPU actor `02011828` using P1 `0861CF0C`. At core8671 it uses
event `0C`, commands `0861D3D4/0861D3E4`, and event B `0861DA1C`.
At core8672 it uses event `36`, count `FF05`, command `0001000C`, and
zero A/event-B pointers. The producer's actual B register is `E59F80D4`
and its actual type is `8070`.

The end-frame dump contains identity13, flags `actor+6=1001` and
`actor+8=C009`, resource record `actor+80=0860B380`, and P1 `0861CF0C`.
The callback is `0836A744`, with saved continuation `actor+84=0836AF64`.
The reaction fields agree with the first record at `0836C32C`:
event36, constructor `0836AE94`, duration metadata and the velocities
saved by the hitstop constructor. These observations are consistent with
the exact static chain below. The original capture did not hook the event
setter or its R1 action-record input. The root agent's later read-only
predecessor replay supplies that witness, as recorded below.

## Resource ownership and wrong selector

The resource itself is correct. WSC1.5 canonical record43 points to
P1 `3B37B0`, which has42 events `00..29`. Its converted counterpart is
`0861CF0C`, also with42 events. Base record13 is a different P1 at
source `370000` / native `086156B4`, with115 events.

| ID13 evolved event | Native row | Count | Command | A | B |
|---|---|---|---|---|---|
| `0C`, observed previous event | `0861CFD4` | 2 | `0861D3D4` | `0861D9D4` | `0861DA1C` |
| `16`, source evolved-air reaction | `0861D074` | 5 | `0861D5B4` | `0861D9D4` | `0861DA80` |
| `36`, outside table | `0861D274` | `000AFF05` | `0001000C` | 0 | 0 |

The last row is animation payload interpreted as an event descriptor.
Changing P1 ownership, extending its event domain, clamping event36, or
restoring the prior event would conceal the wrong reaction selection.

WSC1.5 `76060E..760632` selects four reaction views by airborne flag
`[di+6]&1` and evolved flag `[di+8]&4000`. The generic path at `760C05`
then indexes the selected table by fighter identity and its selected record
by the A-metadata variant. The native equivalents are `0836EC68..EC94`
and `0836F3B8`. The original tables were never extended with the other
three hit tables covered by `records/character-hit-routing.md`.

| View | Source table / record | Old native table / record | Retained native identities | Source identities |
|---|---|---|---:|---:|
| Base ground | `762FD2 / 763258` | `0836BE44 / 0836C12C` | 12 | 15 |
| Base air | `762FF0 / 7632D8` | `0836BE74 / 0836C1AC` | 12 | 15 |
| Evolved ground | `76300E / 763358` | `0836BEA4 / 0836C22C` | 12 | 15 |
| Evolved air | `76302C / 7633D8` | `0836BED4 / 0836C2AC` | 13 | 15 |

Every source row in each view selects the same corresponding record.
The first three old-source populations have12 rows; the fourth has13,
matching retail GBA. This exact fourth boundary was independently checked
and corrected during review; the first unsafe evolved-air identity is13.

For identity13, native `0836BED4 + 13*4 = 0836BF08`. This is the next
table's first pointer, `0836C32C`, whose event is36 and constructor is
`0836AE94`. The expected source table still chooses `7633D8`, paired with
native `0836C2AC`, whose event is16 and constructor is `0836AAC0`.
Native `083555D0` reads the action-record event at `R1+2` and calls
`08012874` at `0835561C`; this is the precise prospective emitter hook.

## Complete narrow change

`tools/build_character_type8_tables.py` creates four15-row views and
redirects all five encoded native aliases. No reaction record, callback,
P1 resource, state flag, or RAM owner changes.

| Old table | New table | Literal readers redirected |
|---|---|---|
| `0836BE44` | `08D3FD04` | `0836F7AC` (`0836EC70`) |
| `0836BE74` | `08D3FD40` | `0836F7B0` (`0836EC74`) |
| `0836BEA4` | `08D3FD7C` | `0836F7B4` (`0836EC8C`) |
| `0836BED4` | `08D3FE90` | `0836F7B8` (`0836EC90`), `0836CAA8` (`0836CA40`) |

The second evolved-air reader has the source counterpart `7622FE`, which
also loads this same table. Both use a byte at their presentation register
plus11 for indexing. Redirecting the shared table preserves this ABI;
this work does not claim that byte is always a fighter identity, nor prove
that reader's complete runtime lifetime.

Allocation is `D3FD04..D3FDB8` and `D3FE90..D3FECC`, inside the existing
`D33000..D40000` reservation. All five preceding owner manifests and
their actual retained writes were checked. Both intervals are entirely FF
in933C and have zero incoming references under the pinned conservative
pointer/ARM/Thumb scanner. An earlier contiguous proposal was rejected by
that scanner; no mode exemption was introduced to make it pass.

There are nine declared write ranges,260 bytes total,255 actually changed.
Restoring precisely those ranges reconstructs the complete933C predecessor.
The source domain checks cover30 canonical resources and all selected base
events32/33/34 and evolved events14/15/16 (hexadecimal).

The builder executes the actual native selector and generic action reader
for3840 cases:15 identities, both forms, ground/air, four metadata variants,
and all16 NZCV states. It compares full registers, flags, memory, writes,
action record and event against the predecessor for3136 retained cases:
all original12 identities plus identity12 in evolved-air. All passed.
The independent verifier and actual replay are separate evidence.

## Actual predecessor witness

The root-owned `build/bizhawk-type8-provenance-v80-20261117-a` replay now
records the actual transition in `type8-event-provenance.txt`:

- Core8671, seq5368: `0836EC90` has NE true, victim `02011828`,
  flags6 `1001`, flags8 `C008`, and literal `0836BED4`.
- Seq5369..5371: the table reader indexes ID13 to `0836C32C`, subtype0;
  the generic metadata reader receives that exact R1, actor `02011828`,
  presentation `020118D4`, and caller LR `0836F3E0`.
- Seq5372..5373: setter caller LR `08355620` supplies event36 and the
  actual event store reads row `000AFF05,0001000C,00000000,00000000`.
- Core8672, seq5374..5375: callback `0836AE94` executes, then installs
  hitstop duration10 and continuation `0836AF64` for that same actor.

Thus the previously conditional source chain has an actual native emitter
witness. The original invalid-producer bus write at seq39001 and subsequent
same-frame writes are not described as prevented. See
[predecessor observation](type8-event-provenance-20261117.md) for the
observer contract. Independent capture QA was still pending when this
source report was updated; the repaired runtime is a different test.

## Frozen isolated artifacts

Final isolated directory: `build/character-type8-tables-r2-20261117`.

- Builder SHA-256: `5CCB654D5DFE62F3791BF11E3F82B4176CBD271E5CFE55A64B09811D49AEF46C`.
- `component.gba`: `75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F`.
- `component.json`: `06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230`.
- Predecessor: `933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775`.

The first isolated directory remains unchanged; its ROM is byte-identical
but its manifest predates the added fourth-table identity12 preservation
case. Use the r2 manifest above. Main build files, Git, original ROMs,
frozen builds and emulator state were not modified by this worker.

No full-campaign completion or actual repaired runtime outcome is claimed
by this source/isolated-layer report. The new8070 corruption and its native
event selector chain are observed; independent replay QA and the repaired
runtime outcome remain separate evidence.
