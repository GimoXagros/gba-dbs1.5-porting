# Source CPU AI table closure after the Waterfall exception

Date: 2026-11-17. Isolated component over frozen75BD; no main integration,
emulator execution or Git operation by this author. The foreground overlap
is independently source-correct for its sampled frame; see
`waterfall-foreground-source-parity-20261117.md`. The fault here is a distinct
AI data dependency.

## Actual old producer and the complete dependency

Root's read-only run `build/bizhawk-ai-provenance-v82-20261117-a` finalized
at core20166 with original host exit0. Its `ai-producer-provenance.txt` is
`2CE8A5CD5FC9F9F2BC7D07E1E127417A3FC713C512519AF25E8D081B7D02108A`.
The journal directly records CPU14 at stage9/progress2:

- Core19961, seq1..5: native CPU14 remains effective14, multiplies by17,
  reads parameter address080C6D6A inside ARM instructions, and copiesE92D
  to AI owner03004D88+2. The retained table080C6C7C has only eight17-byte rows.
- Core20165, seq29: the actual halfword-copy instruction at080110EC, with
  LR080C69B8, writes selector000F to03003D50. The copy's action offset is
  0011FFEE, exactlyFFFF*18. R4=081E4FB4 is the postincremented source pointer;
  the18-byte record starts081E4FB2, not081E4FB4.
- Seq31..32: selector15 reads080C6630=E3A00000 from the data after the
  twelve-handler table080C65F4 and uses it as the BX target. The observer
  sees the bad target; it does not assign a replacement target.

The independent native reviewer reconstructed the preceding behavior address
080C554A from captured raw identity offset1500, group128 and RNG cell10.
That halfword isFFFF; the actual copied18 bytes equal ROM001E4FB2. Thus
the parameter and behavior tables both need the source identity correction;
the bad action copy is established by actual execution, not inferred from
the final undefined-mode registers alone. The native review owns the detailed
capture reconstruction and its independent report.

## Source table and identity contract

Source identities are not the same as physical AI row indices. Original
782B34..782B63 reads config+0C, maps identity11 to7, subtracts5 from identities
at least13, and otherwise retains the value. It pushes the normalized index
at782B5B before multiplying by17. At782D23..782D28 it pops the same normalized
index and multiplies it by384 for the behavior-block offset at source0696.

The native initializer already handles11→7 at080C6D60/64, but lacks the
13→8/14→9 mapping before its saved push at080C6D68. It consequently corrupts
both indexing paths. The new32-byte helper replaces that push with a branch,
preserves R8 and CPSR flags, applies the source >=13 subtraction, restores
R8/flags, performs the original push of normalized R0, and returns to080C6D6C.
No config byte or actor identity is rewritten.

| View | WSC1.5 range | Old source/native population | Completed population |
|---|---|---|---|
| Parameters | 782970..782A1A | 8 rows,17 bytes each | 10 rows |
| Behavior choices | 74EB2A..74FA2A | 8 blocks,384 bytes each | 10 blocks |
| Actions | 74D89A..74EB2A | 258 records,18 bytes each | 264 records |

The eight old parameter rows are byte-identical across WSC1.0 at3C3250,
WSC1.5 at782970 and USA native080C6C7C. The eight old behavior blocks are
byte-identical between WSC1.0 at3AB1EE and native080C3FC0. WSC1.5 changes
23 existing behavior halfwords:1 in block0,17 in block2,5 in block3, then
adds blocks8 and9. It is therefore insufficient to append two blocks while
retaining all old choices. Source block9 includes action262.

Source behavior consumer74D45E..74D469 adds0696 and its local index, then
reads CS:[BX+183A]. CS base74D2F0 identifies74EB2A. Native080C64D4..080C64E8
does the corresponding +0A/local-index read through literal080C658C.
All1920 source choices are at most262. Source action reader74D66D..74D6F2
copies nine halfwords from CS+5AA, identifying74D89A; its continuation comes
from+5B8. Every one of264 source continuation indices is below264, maximum261.

Across retained258 actions, WSC1.5 changes only record12's state5→7 and
record148's state8→7. Six new records258..263 extend the existing opcode
semantics. The low state bytes across all264 records are exactly
0,1,2,3,5,6,7,8,9,10. State15 is not a newly required source handler.
The native twelve-handler dispatch remains unchanged.

One pre-existing commercial difference is deliberately retained: action42
field+0C isFF7E in both WSC originals but007E in USA. It is the only byte
difference between the258 old source/native action records. Fifteen other
FF7E fields and22 FFBF fields remain identical between source and native,
so this is not a generic sign or mask conversion. The independent reviewer
confirmed080C67F0 reads the full halfword and080C6820 ANDs it into actor+2C.
The high byte can affect behavior. This component preserves007E and does
not claim complete source parity for that historical commercial exception.

## Domain and boss bypass

Ordinary campaign CPU identities from the source route are0..6,11,13,14;
identity7 is also an existing ordinary AI row. These map into the ten-row
domain. Raw8 and9 also map to valid row indices but are not asserted to be
reachable ordinary campaign opponents. Raw10 and12 remain outside that
table, as does boss15 after source normalization15→10. No fabricated row,
clamp, or assertion that all15 identities are valid initializer inputs is
introduced.

Boss15 does not take this initializer on the campaign path. Source740C97
reads game kind1000:0050;740C9A tests stage1000:005C=7 and740CAD adds2.
The table at740CD2 contains03D8/0416/046E relative to CS740900. Normal kind0
enters740CD8 and calls the AI wrapper at740D0B. Boss kind2 enters740D6E,
constructs actor kind3/identity15 at740D7A/740D7E, then reaches740D8C without
the AI initializer. Native080D1830..080D1850 has the same stage7/add2 test;
dispatch080D1888 selects normal080D18B8→08375E60→080C6D04 or boss080D19AC
which constructs kind3 and reaches080D19F0 without that call. This is static
caller evidence; no boss replay was performed for this record.

## Isolated writes and allocation

Builder `tools/build_character_ai_tables.py` is frozen at
`3F8613A6697E2CFFB0112F1C699415A793EACDA7242790C8D30C6C9662691EC0`.

The new reservation isD88800..D8AB00, whollyFF in the pinned predecessor,
disjoint from all six supplied prior owner manifests and their reservations.
All113 prior writes remain byte/hash-identical. The frozen conservative
scanner finds zero incoming encoded references into the whole reservation,
including padding, across pointers in all alignments, ARM branches/literals/
ADR and Thumb branches/literals/ADR. No data/interior exception is granted.

| New native raw range | Purpose |
|---|---|
| D88800..D888AA | ten parameter rows |
| D888AC..D888CC |32-byte identity helper |
| D88900..D89800 | ten behavior blocks |
| D89800..D8AA90 |264 action records |

The other24 writes are the four-byte hook080C6D68 and23 pointer redirects.
Parameters have15 literal readers:C7140,C714C,C7154,C715C,C7164,C716C,C7174,
C717C,C7184,C718C,C7194,C719C,C71A4,C71AC,C71B4. Behaviors have one:C658C.
Actions have seven:C6A2C(+0E),C6A3C(+0),C6B2C(+0),C6B34(+0),C6BB4(+10),
C6BB8(+11),C6BBC(+10). Each interior offset is preserved. A whole-ROM
all-alignment pointer census establishes those complete alias sets.

There are28 disjoint writes,8890 declared bytes and8128 changed bytes.
Reversing every declared write restores the complete75BD predecessor,
including all padding and unchanged code. The layer allocates zero RAM.

## Artifacts and author checks

`build/character-ai-tables-v82-20261117/component.gba`:
`DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98`.

`build/character-ai-tables-v82-20261117/component.json`:
`2645FA80910F747BEB4A07239645449536BCFA51652194D191749CF03DF063B3`.

Author actual-ARM checks pass4096 helper cases (all256 byte inputs ×16NZCV
patterns), preserving registers and flags while saving the normalized index.
507 full initializer executions cover13 test identities ×3 difficulty values
×13 progression indices. Raw8/9 are synthetic tests of physical rows8/9,
not claimed campaign opponents.351 of these compare complete register,
CPSR and memory state against the predecessor for retained identities0..7/11.
The helper's temporary stack write is overwritten by the original saved-R0
slot; it introduces no surviving stack memory difference in those cases.

Build command accepts `--before`, `--gba`, `--old`, `--source`, six `--owners`
(evolution-music, evolution-transition, id13-air-relaunch, campaign-stage-
progression, campaign-progress-consumers, and prior type8 current-candidate
manifests), plus fresh `--output` and `--manifest` paths. It refuses existing
outputs, pins all four ROM inputs and all six owner manifests, and writes
only the new requested component/manifest after all checks pass.

Independent native consumer/source/negative-control review is separate and
pending at this record's author freeze. A positive live run of DEEE, complete
campaign behavior, and the unexecuted type8 evolved-air event16 witness are
not established here. The actual75BD failure does not become a positive
runtime result merely because its static dependency is repaired.
