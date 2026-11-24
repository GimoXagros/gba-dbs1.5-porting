# Bounded mode23 completion save compatibility

The proposed completion adapter and its two sanitizer changes pass the bounded native save contract on candidate5284435A. They do not require expanding the native EEPROM record. This is approval of the mode23 completion transaction, not equivalence of the whole WSC1.5 save format or proof of physical persistence.

Independent verifier `tools/verify_mode23_completion_save.py` SHA256 `D5DBFAF77571E8ADD6A4F81329CCDCAF3ABEFB73D2B07B0E2E05B402F9844232` produced `build/mode23-completion-save-independent-r2-20261117/report.json` SHA256 `7802F8AED365F52CB2918B316C45CA22E5C4FB12F5006B79754056C20337745D`, exit0. It binds module `tools/mode23_completion_save.py` SHA256 `0741223598DF038EE4DE569B600A90B731A687CDAC892FBE4FB00E9396D6D196`. The earlier report0B1F remains separately preserved. No production ROM, shared interpreter, main builder, emulator, save file or Git state was changed.

## Exact completion behavior

Source74B959..74B981 sets configuration pending-byte18 to `pending | (10 & ~permanent19)` and invokes85DE:02EF with selector2 and operation0. It does not immediately make bit10 permanent. Source7860CF calls sanitizer785FE1 and the three-row descending score sorter77B588, then selector2 at786126 copies configuration19 to record392C+12. Finally it copies E8 bytes to the source SRAM mirror1000:0076. This specific path does not read or mutate source record fields beyond the common sanitizer/sorter domain14..65.

The new native adapter follows that order: pending update, actual0801FA98 sanitizer, actual080C12EC sorter, byte19 zero-extended to native record03001120+12, then actual0801FC5C checksum writer. Calling native0801FBD0 with selector2 alone would be insufficient: the retail wrapper has only the selector1 copy from config1C to record10. The new adapter deliberately performs the source selector2 copy after normalization. It preserves R0..R12 and SP and returns to the incoming LR via POP PC. R14 itself retains the final call's return address; flags are native scratch.

The two proposed shared changes are narrow:1FAB8 becomes `AND r8,r8,#3F` for permanent unlock bits, while the count field64 continues to use1F;1FB08 changes the accepted score fighter maximum from0C to0E. Source785FF9 and786022 establish those exact domains. Native1FA98 has a retained register-reuse detail: the next score row's first-byte mask depends on the preceding score path. Source DX has the same reuse, so the independent model retains it. The source and commercial native malformed-name fallback spellings differ; valid three-character names are the tested contract, and this adapter does not repair that unrelated discrepancy.

## Native persistence and consumers

The native writer/checksum/reader instructions execute in the independent test. Only the low-level eight-byte device API is modeled in memory; native sorter DMA3 transfers are modeled at their actual MMIO writes, rather than replacing the sorter. Six direct sanitizer cases prove that bit5 survives the shared mask and field64 keeps1F. Sixty-four complete permanent-bit combinations cover all16 initial NZCV states, source-shaped payload normalization, three-row sorting, completion ABI, checksum creation,25 native block writes,25 native block reads and the actual boot copy at15948..15958. A mutated payload is rejected by the actual checksum reader. Twenty-five additional cases inject the first write failure at each block0..24 and verify the native early stop.

Payload remains C0 bytes; checksum is the four-byte sum atC0..C3. Transfer remains25 eight-byte blocks0..24, withC4..C7 retained. Block25 and all later bytes remain unchanged in every case. Expanding to sourceE8 would overlap the separately adopted Shoot block25; this review does not authorize it. The device fixture does not prove EEPROM hardware, retry timing, atomicity or recovery after power loss.

Native read0801FCA8 checks the C0 checksum after loading. The boot copy15954/15958 transfers record12 to config19 without a five-bit mask. Therefore bit5 survives a valid read; the changed shared sanitizer prevents later ordinary commits from deleting it. The unlock-menu consumerBF6BC..BF6D0 already ORs config19 into record12 before calling the shared serializer. High-score text reads only name/score; its portrait path1D0DC→1F3A8 indexes the already relocated resource table084A80F8. Current rows13/14 contain valid native resource pointers, so accepting these two identities does not introduce a portrait table overrun. The finite encoded record-consumer inventory previously established by `analyze_language_consumers.py` remains useful; it is not a proof against arbitrary computed aliases.

The completion wrapper restores incoming R0 and does not expose a failed EEPROM write. That preserves the source-shaped callback interface but does not establish a successful save on failure. The test explicitly covers this limitation; no new error UI or persistence guarantee is implied.

## Source tail is live and remains outside this transaction

The source E8 record is not C0 plus unused padding:

| Source record offset | Positive owner evidence |
|---|---|
| 8E..C9 | Fifteen four-byte per-fighter statistics pairs;76CFDA..76D010 indexes identity times4 and updates fields90/8E. The portionC0..C9 lies past the native payload. |
| CA..CB | Progress flag set at778553 and read at780E76. |
| CC..CF | Four-byte value at39F8 written774BB5..774BC5 and passed to the service784F1B..784F26. |
| D0..E5 | Eleven counters rooted39FC;784980 copies the first ten,7850F2 scans eleven backwards,785199 decrements an indexed counter. Unlock checks77857F/77863C inspect this population. |
| E6..E7 | Additional displayed counter read780326 and clamped to999. |

Thus the native prefix is not globally interchangeable with the source record: for example the source extends per-fighter statistics where the retail native record already has other fields/checksum. Native33ED64 still computes `8E + identity*4` for its statistic pair; IDs12..14 can address C0 or later. That is a separate existing statistics compatibility issue, not a new effect of allowing high-score identities13/14, and is not repaired or declared safe here.

Mode23 B059 itself does not use any of those tail owners. Its pending bit and permanent-copy transaction are entirely within shared config18/19 and record12, plus the common sanitizer/score sorter. It is therefore sound to preserve the native record allocation for this bounded completion save, while retaining the tail/statistics mismatch as a separate compatibility limit. Final scene integration must bind this exact module and two changed words, preserve the existing EEPROM/IRQ initialization and exclusive task lifetime, and separately prove the mode23 terminal reaches this callback.

Run with a fresh output path:

```powershell
python tools/verify_mode23_completion_save.py --source "C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc" --native build/shoot-child-contact-20261117/component.gba --report build/mode23-completion-save-independent-r2-20261117/report.json
```
