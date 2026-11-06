# Source-defined 8EF3 pattern extension

The isolated component extends native8EF3 to every16-bit X/Y pair for which the source selector reaches its ordinary spatial-pattern bodies. It preserves previously accepted behavior. It does **not** claim to emulate the source's unrelated control transfers or authorize external Shoot entry.

`tools/build_shoot_spatial_subset.py` consumes exact sourceC415 and predecessorB64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B. Output is `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717`. The new writes comprise24bytes at086FE000 plus the4byte BGE target at085CC0F0;27 bytes actually differ. The full inverse reconstructs exactB640. The32byte reservation was entirelyFF and had no existing unaligned pointer or ARM branch reference.

Source8EF3 reads CS code/table words, not the collision grid. Its X loops advance the pointer before LOOP expires and then use the following entry. Consequently signedX>=1E00 with signedY<=1500 selects pattern1; Y1501..1600 selects pattern0. Both are ordinary existing source bodies. The old native guard rejected these cases.

The new stub receives the already signed capturedY inr1 and X>=1E00 inr2. It executes:

```
cmp r1, #0x1600
bgt 0x085CC1C0
cmp r1, #0x1500
bgt 0x085CC188
mov r1, #1
b 0x085CC150
```

These branches enter the retained rejection epilogue, zero-pattern body, or vector1 body. Existing saved registers, object stores, unsigned zero-pattern X bounds, one RNG call, result flag and caller continuation remain in the existing8EF3 implementation. Inputs accepted before this change never take the modified branch.

The source analyzer partitions all65,536 signed Y values into six table-owner intervals and enumerates all65,536 X values per interval. Weighting those exact outcomes covers2^32 pairs:

| Population | Pairs |
|---|---:|
| Previously accepted normal patterns | 1,605,017,088 |
| Newly accepted normal patterns | 963,404,288 |
| All source-normal patterns | 2,568,421,376 |
| Source nonpattern transfers, still open | 1,726,545,920 |

The maximal normal-pattern domain is signedY<=1600 with any16-bit X, or1600<signedY<=1B00 with signedX<1E00. The remaining inputs read selectors0032,3A20 orC08E and jump to4090:0A80, E59A orEB4C. The latter two addresses contain data interpreted as instructions. The first enters the middle of an input routine with inherited registers and stack. Copying adjacent bytes into a native pattern table or clamping coordinates would not preserve those effects. Native rejection for these cases remains unchanged and is not claimed source-equivalent.

Final fresh isolated c/d builds produce identical ROM/report bytes; report SHA256 is `217370D61630F57EF9D3AE4A368D0C28D2184582BA03C90E25B8345D05013E67`. Builder SHA256 is `5D12C8DBDD2A2AA010FDC4388AA278600AE7A117712B758610B333DF7098BC3F`. The final ownership check uses the frozen `7CDD6E52...` resident verifier's full conservative census, rebound with a private globals dictionary for the32byte reservation. It covers mirrored pointers, ARM branches/literals/ADR and Thumb references, with four positive scanner fixtures. No imported module globals are modified.

Eight direct mutations reject changes to every new instruction, the entry branch, and an outside write. `terminal_path` owns independent actual-code/source/ABI verification; self-checks here are not labeled independent QA. No emulator, save or guest memory was used, and no frozen builder or main file was changed.
