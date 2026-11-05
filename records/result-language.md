# Approved native result labels — 2026-11-05

The isolated component now installs the independently reviewed artwork into
all four existing mode8 result-label routes. English retains native WINS and
DRAW. Japanese, Korean and Digicode reuse exact Japanese WIN/DRAW pixels.
Last chance uses source Japanese, the approved Korean26-part frame and the
revised Digicode27-part frame. This supersedes the old compact red-text draft;
it does not claim whole-game localization or normal runtime verification.

No main-pipeline, emulator, save or Git operation belongs to this worker.
The separate independent verifier passed this actual artifact:
`build/result-language-qa-20261105/independent-a.json`, SHA-256
`50351DA73917A2884CAAC4AFDAC40FFB6E1F42E8EE5B30D34B5B9EF064C5775F`.
It checks60 installed frames,703 negative controls,24,576 ABI transfer cases,
all389,162 joint states, allocation ownership and full-ROM inverse. See
`records/result-language-qa-20261105.md`. Main full-build/runtime validation
remains separate and is being completed by root.

## Input and reproducibility

The exact predecessor is the source-title candidate
`494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6`.
Retail GBA and WSC1.5 originals retain the existing pinned identities.
`build/result-language-approved-20261105-a` and `-b` contain four byte-identical
files, independently generated from originals and tracked code:

| File | SHA-256 |
| --- | --- |
| result.gba | A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F |
| manifest.json | 01CD887938DF6EADD155D61728279A6BB2C152EB6A5AEFEB3E2C2659213CC544 |
| generated-art.json | 8BFC3960335EDD29ECEBFA2DB7A673FDE586C6B5B79B0FDB47622BC601083074 |

The fourth file is the actual installed-resource preview, `preview.png`.
It was viewed: shared WIN/DRAW and complete Japanese/Korean/Digicode last
chance phrases retain their native checker texture, white outlines and
punctuation. It is a static decoded resource preview, not a game screenshot.

The fresh art path reads no prior build folder, ROM-derived pixel JSON, font,
large image, PNG mask, or supplied save. `build_result_pixel_art.art_data`
derives Japanese art/punctuation from originals, uses tracked `korean_mask`,
and calls the same pure `make_digicode` expansion as the reviewed revision.
The tracked Digicode catalog supplies the seven Japanese-reading identities.
The original user PNG remains review evidence, not a clean-build dependency.

Fresh generation asserts the exact approved complete palette-pixel hashes:
Japanese WIN8ECA7847…, DRAW D47B0B69…, Korean124F0000…, Digicode4F9B02D9….
All four frames recompose exactly from their native tiles. The generated
JSON differs from the reviewed875700A7… JSON only in production metadata;
approved pixel/part commitments bind both representations. The schema2
catalog retains the review-art hash as provenance, not as a required file.

## Resources and ownership

| Language | P0 raw | Packed bytes | Atlas tiles | WIN/DRAW/LAST parts |
| --- | --- | ---: | ---: | --- |
| English | B8210 | original |91 |35/20/28 |
| Japanese |651AE0 |5280 |145 |30/20/28 |
| Korean |6DA640 |5272 |145 |30/20/26 |
| Digicode |7DFC20 |5276 |145 |30/20/27 |

The old4336-byte Digicode assumption was discarded. Extending its old
6DD200 interval produced real conservative ARM-reference conflicts around
6DE3EC..6DE684. The complete new5276-byte reservation at7DFC20..7E10BC is
FF and passes all-alignment mirrored-pointer and ARM/Thumb reference scans
without waivers. Japanese651AE0..652F80, Korean6DA640..6DBAD8 and the existing
52-byte wrapper652FA0..652FD4 pass the same strict ownership checks.

Every new P0 begins with all91 original atlas tiles unchanged. All twelve
native digit/symbol layout arrays2..13 remain byte-for-byte identical.
New text tiles append/deduplicate after that prefix; all145 indices fit the
native8-bit domain. Every installed text frame is reconstructed and compared
to the source or approved indexed pixels. Original P0/P1/palette resources,
fighter/name resources, mode12 alias and its initializer remain unchanged.

## Consumer, ABI and correlated budget

The six existing initializer calls089988/0899EC/089BFC/089C60/089D9C/089F34
route through the same52-byte wrapper. It selects the existing language tag,
substitutes only the P0 argument, restores registers/LR/SP/CPSR and tail-enters
080127E4. Invalid tags still fall back to English. All8192 tag/flag ABI cases
pass; the wrapper's16 stack bytes occupy the same depth as the original
initializer push. It adds no persistent RAM, task or presentation.

The obsolete DBB whole-ROM seven-span inverse was removed. The new gate
pins the exact title predecessor and positively checks every retained native
code/resource/pose dependency before rerunning the complete current budget.
No font-draft count or earlier budget manifest supplies the new text counts.
All225 fighter pairs and389162 correlated joint states are recomputed,
including phase2 loops/holds. English's actual bound remains127parts/4064
staging bytes; each other language is122parts/3904bytes. Independent maxima
would incorrectly estimate128 English parts, so the correlated proof is
retained. Ordinary-draw bounds are116/116/114/115, respectively. No offscreen,
transparent or overlapping parts are omitted, and no clamp is installed.

Ten disjoint writes declare15904 bytes and change15897 bytes. Full-ROM
inverse restoration reproduces the exact input; complete packed-resource
inverse checks preserve the native digit prefix and all approved text pixels.
Sixteen builder mutation checks reject changed declared spans and undeclared
resource, getter, alias and gap writes. The completed independent artifact
verification adds703 separate negative controls and confirms all60 frames.
The Korean source art passed `independent-art-qa-final.json` (B125AEB3…);
Digicode v2 passed `digicode-large-v2-data.json` (9796301A…), as recorded in
`records/result-pixel-qa-20261105.md` and
`records/result-digicode-large-qa-20261105.md`.

## Reproduction

```powershell
python tools/build_result_pixel_art.py --generate-data GBA WSC15 localization/digicode-reference.json OUT/generated-art.json
python tools/build_result_language.py TITLE GBA WSC15 OUT/generated-art.json OUT/result.gba --manifest OUT/manifest.json --preview OUT/preview.png
```

GBA/WSC15/TITLE denote the pinned files above. The optional standalone
read-only budget command is `analyze_result_language_budget.py --approved-art
TITLE GBA WSC15 OUT/generated-art.json OUT/budget.json`; the builder already
includes that complete correlated calculation in its manifest.

Main-pipeline wiring now invokes the fresh generator, result builder and
independent verifier; root has completed both current268-file full builds
and the independent audit. Normal result runtime remains separate. The result
runtime plan is `records/result-language-runtime-plan-20261105.md` and uses
ordinary Options commit, title re-entry and a natural battle result.


The completed full-build comparison is
`build/repro-v67-20261105-comparison.json`, SHA-256
`249B3B2E997E8C2B289D53B0C7BD46A17B029AE5F020BB215BEAF96386BF5AD3`.
Independent recomputation is
`build/repro-v67-final-audit-20261105/audit.json`, SHA-256
`2006A629A9F8334ADDF771ED8C104A06CFE758A12DFFCDF789C49805973BD155`.
It verifies both complete268-file inventories, exact component reports and
the whole final-to-v65 inverse chain. This does not replace result runtime.

Root subsequently completed four fresh hidden ordinary-input routes on exact A4CB: KO-b, DG-c, EN-d and JA-e. Each observed native commit, battle and actual WIN resource drawing through result+300; aggregate D4903EBFB0B8D78548AA7044CFCB6F305A9435E7D88EA144BAE211EC0860636B. See records/title-result-integration-v67.md and the separate runtime QA record.

Skipped: actual DRAW/last-chance occurrence, hardware testing and other language consumers. Risk: ordinary WIN coverage does not establish every result event.
