# Independent QA: source-normal spatial subset

Accepted the isolated 28-byte extension over the damage-repaired B640 candidate. This expands native8EF3 to every coordinate pair that the exact source selects as a normal pattern. It does not establish reachable player coordinates or equivalence for the source's unrelated control transfers, and does not authorize external Shoot entry.

- Verifier: `tools/verify_shoot_spatial_subset.py`, SHA256 `0C394224C318F2F9249DE87F02F56C5570001152DB5AB657769FC1E1543FB76D`. No producer imports.
- Actual input: `B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B`.
- Actual c/d output: `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717`.
- Actual c/d manifest: `217370D61630F57EF9D3AE4A368D0C28D2184582BA03C90E25B8345D05013E67`.
- Independent reports `build/shoot-spatial-subset-qa-20261106/proof-b.json` and `proof-c.json` are byte-identical SHA256 `4F5A9EDA33FF91BE70A94DB5240814ADA94EAEBD2CE2F7E6B1FCF00E729543B9`.

The source loops at7497F3..749829 fall through after exhausting their declared counts; they do not reject immediately. I derived 34 disjoint signed-coordinate rectangles from the actual source thresholds and the extra record read after each exhausted loop. Their cardinalities cover exactly2^32 pairs. The normal-pattern population is2,568,421,376, including963,404,288 newly supported pairs. The remaining1,726,545,920 pairs dispatch to0A80/E59A/EB4C in source and remain an explicit open obligation; the retained native rejection is not asserted equivalent to those transfers.

For signedX>=1E00, sourceY<=1500 selects pattern1 and1500<sourceY<=1600 selects pattern0. The new six-instruction stub precisely implements these cases and retains rejection above1600. All old accepted inputs continue through unchanged native instructions and actual source-matching vector/Y/X data.

The verifier executes the actual complete native function for544 rectangle-corner and RNG cases. It checks signed16 loads, return acceptance, all saved registers, SP/LR, the original52-byte stack frame, exactly one RNG call for accepted cases, and exactly four16-bit actor writes at+A4/+A6/+A8/+AA. The zero pattern's unsigned X clamp remains the original source behavior, including negative signed X. The interpreter is local and strict; source assertions are independent of the component builder.

Seven direct controls reject shifted upper/selector boundaries, wrong vector, removed extension, changed signed branch, wrong zero destination and an outside-write mutation. The whole-ROM inverse allows only the conditional branch at5CC0F0 and24-byte stub at6FE000. The full32-byte reservation is FF with no inbound reference under all-byte pointer/mirror, ARM branch/literal/ADR, and Thumb branch/conditional/BL/BLX/literal/ADR scans. Four positive scanner fixtures exercise mirror pointers, ARM ADR, Thumb literals and Thumb branches.

No previous607 collision or5.46-million-state pursuit proof was rerun or treated as unconditional. No emulator, saves or guest-memory writes were used.

```powershell
python tools/verify_shoot_spatial_subset.py BEFORE.gba AFTER.gba SOURCE.wsc --manifest MANIFEST.json --output REPORT.json
```
