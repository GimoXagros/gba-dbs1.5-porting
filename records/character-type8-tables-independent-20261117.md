# Independent type8 reaction-table repair review

The source-backed four-table correction is independently PASS. The frozen
result is `75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F`.
The verification report is
`build/type8-tables-independent-final-20261117/report.json`, SHA-256
`0A5EB8355D74AF38C61A90C74ECAD636BDCF6250066C786119DC4EC2513C8896`.
The verifier `tools/verify_character_type8_tables.py` is frozen at
`3269953041EE9FB57C210CA01206630BFFFC781B77F1477C47F6E0E851867648`.
It imports the existing strict ARM interpreter and reference scanner, never
the production builder or its expected-result functions.

## Actual predecessor

The fresh933C replay journal
`build/bizhawk-type8-provenance-v80-20261117-a/type8-event-provenance.txt`
(`1B3C05A0A1AA43C0242DD1F5772D21305267579EB57C52DDADAB263DB07AE7AC`)
shows the missing causal chain, before the reported invalid collision:

- Core8671 seq5368: selector `0836EC90` actually executes NE with victim
  `02011828`, flags6=`1001`, flags8=`C008`, and literal `0836BED4`.
- Seq5369–5370: ID13 selects `0836C32C`; scratch subtype0 leaves it unchanged.
- Seq5371: the generic metadata reader receives that record from LR=`0836F3E0`.
- Seq5372–5373: event setter caller LR=`08355620` selects and stores event36;
  the indexed P1 row reads `000AFF05,0001000C,0,0`.
- Core8672 seq5374–5375: constructor `0836AE94` installs hitstop continuation
  `0836AF64` with duration10. The existing collision probe then rejects8070.

This is an observed wrong table row, not an inferred effect of the final
hitstop callback. Input/capture preservation is separately checked by the
[provenance QA](type8-event-provenance-20261117.md); no emulator was launched
by this reviewer.

## Exact correction and checks

| Native old table | Original rows | Source1.5 table | Native record | New table |
|---|---:|---|---|---|
| 0836BE44 | 12 | 762FD2 | 0836C12C | 08D3FD04 |
| 0836BE74 | 12 | 762FF0 | 0836C1AC | 08D3FD40 |
| 0836BEA4 | 12 | 76300E | 0836C22C | 08D3FD7C |
| 0836BED4 | 13 | 76302C | 0836C2AC | 08D3FE90 |

Each source table contains15 identical record offsets. The native event
groups, in hexadecimal, are `[32,33,32,32]`, `[34,34,34,34]`,
`[14,15,14,14]`, `[16,16,16,16]`. Thus the failing evolved-air reaction must
use event16 from `0836C2AC`, not event36 from the following table's record.
The fourth old table has13 rows; this independent boundary finding was also
incorporated into the author's frozen r2 contract.

Only five existing pointer words (`36F7AC/B0/B4/B8` and `36CAA8`) and four
new60-byte tables change: nine declared spans,260 bytes,255 actual differences.
An independently constructed expected image equals the entire output, so all
other ROM bytes—including existing code, records, P1 resources and native
tables—are preserved. There is no event clamp or added RAM/instruction.

The new allocations `D3FD04..D3FDB8` and `D3FE90..D3FECC` are blank, contained
in the existing `D33000..D40000` reservation, and have no encoded inbound
references under the existing conservative scanner. All104 prior manifest
writes are disjoint; all42 prior writes inside the enclosing reservation
retain their actual bytes and hashes.

The verifier checks all60 source rows, commercial record lineage, all five
native aliases, and source/native populations plus selected-event command
counts for30 P1 resources. It executes the actual selector, generic metadata
reader and event setter up to the first command read in480 cases. This covers
IDs0..14, both resource groups, ground/air, four record variants and two
opposing initial NZCV patterns. All392 original-valid full machine states,
RAM and writes remain equal, including the fourth table's original ID12.
The old933C exact event36/countFF05/command1000C failure is independently
reproduced at the last safe instruction. Nine redirect/table mutations are
rejected by the whole-image expected-content check.

The second consumer at `0836CA40` is tested for15 byte indices through its
actual R5+11 load and metadata-reader call. This does not assert the runtime
owner lifetime of R5 there; its existing ABI is unchanged.

## Reproduction

Run the verifier with `--before`933C, `--after`75BD, `--source`original WSC1.5,
`--old`original WSC1.0, `--gba`original retail GBA, and a fresh `--report` path.
`--owners` takes five manifests in order: evolution-music, evolution-transition,
id13-air-relaunch, campaign-stage-progression, and the933C campaign-consumer
manifest. Paths are not embedded in the deterministic report.

The r2 component is `build/character-type8-tables-r2-20261117/component.gba`.
Main integration, corrected gameplay continuation and full campaign completion
remain separate gates; this bounded pass does not establish a finished port.
