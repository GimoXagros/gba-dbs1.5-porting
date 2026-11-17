# Shoot mode corruption: bounded native predecessor

This is a read-only structural review of frozen574FD261 following the reported whole-play mode write at core90753. The running whole-play capture is not treated as a finalized run or a complete failure audit. QA owns the new bounded producer witness; root owns private execution. No renderer clamp, ROM patch, game-state write or return-value substitution is proposed here.

The observed mode bus write changed03002310 from7 to77, with exposed PC086FEAF0 and LR02003BA0. The actual preceding writer is086FEAE8 `STRH r3,[r12]`, the generic per-part dynamic sprite renderer. The two independently typed destination pointers agree on slot477:

* OAM staging: `03001428 + 477*8 = 03002310`.
* Dynamic tile staging: `02000000 + 477*32 = 02003BA0`.

Therefore the mode word is reached by a sprite-staging overflow. It is not a mode pointer loaded by a mode-dispatch helper. Value77 is a sprite Y attribute at this instruction, not an intended scene transition. This establishes the writing consumer but does not yet establish the corrupt or oversized layout's producer.

Copied renderer086FEA50..60 loads the byte cursor030012CA and rejects entry when it is already>=127. It then sets R12 to OAM staging pluscursor*8 and LR to tile staging pluscursor*32. Per-part loop086FEAC8..FEBD0 tests Y/X visibility but does not retest capacity; successful parts increment R12 by8, LR by32 and R0 by1. The final cursor is stored as a byte only after the part loop. The retained commercial renderer08012C58..12DB8 has the same one-time entry capacity check and unbounded per-part loop, at12C68..6C and12CD4..12DA8. The new source-mask checks in the copied renderer do not account for the capacity behavior.

The typed metadata chain to capture is presentationR5: P0=[R5+48], command/A-record base=[R5+20] with16-byte index[R5+1A], layout table=[P0], layout indexWORD[R5+18], then countDWORD[layouttable+index*8] and part pointerDWORD[entry+4]. After086FEAA8, R2 is the remaining count and R10 is the part pointer. The observer should retain the presentation's80 bytes and these source pointer values before the first attempted staging slot127/128, rather than only the eventual mode word corruption. Entry086FEA50, metadata086FEAAC and first attempted store086FEAE8 are sufficient narrow sites; a bounded ring of prior presentation entries distinguishes an already oversized layout from aggregate cursor pressure.

No assertion about which event, layout row, actor or static-resource conversion caused this overflow is made before that producer witness. A later source-backed correction must address the actual producer/consumer contract rather than suppressing the mode write.

## Finalized first producer replay

Root's original private replay64438 exited0. New independent checker `tools/verify_sprite_mode_corruption_capture.py` SHA40EC74DA2B38401591DECCFA411D326535DAECFF613E3C8A7E32CDB363F90ABD produced `build/sprite-mode-replay-independent-20261117/actual.json` SHA7A064F85555F81EE946EDEA088638960432EADC9B4686F5912DB7F21361FA640. It binds finalized launch3F0281B85CC17DD1E1A02CB27C9AAE01C80F87F7AA532AB19A2BDBA2A520F631 and journal9905C022ABA18B75ECE431207CB2A73638C3035CE9BF46A3EBBCDF6FDED26C78, all files, current ROM574F and original checkpointCore43B2893A. The restored Core is **not byte-identical**:15 native serialized-core bytes differ, and the original report retains every offset/value difference. CPU bank, native extensions, managed suffix and five saved RAM domains match the verified source checkpoint. This is a loaded-state diagnostic with those explicit limits, not an exact full-Core replay claim.

At core90753, entry4407 loads presentation0201135C, child P1/P0=085B9000/085B9200, event6 and layout20hex. Initial OAM cursor is5; this is not aggregate ordinary sprite pressure. The native P0 layout table is085B9210, so layout32 reads085B9310 in the adjacent P2 palette. Its words03E00360/000067F9 become part count65,012,576 and an invalid low-memory part pointer. First outside staging write occurs at slot128; the same presentation subsequently reaches mode-owner slot477. Saved caller0837361C identifies the ordinary display consumer.

Original source child P1 at3D1E30 has exactly three event rows0..2, with command counts6/8/6. Its leading payload relative28 minus the12-byte header/trailer framing yields two further table rows. The native rows preserve that population. Event5 instead interprets command bytes as `(0000FF03,00000002,0,0)`; event6 interprets `(0001FF03,00000003,0,0)`. Thus event6 is an invalid event selection, not an omitted source layout32.

The finalized actor still has callback0837247C. The retained retail chain begins083723E0, selects event5 at0837240C, then installs08372428. That callback selects event6 at08372464 and installs0837247C. The sole literal083723E0 at36F88C is loaded by36F77C and installed at36F780. The source counterpart positively distinguishes stage11: raw760E4B..760E95 SHA256BC0EB46ABB9510987E1543E7F4472337ACCE2D706202F0581FCF910599E30582 reads actual stage, chooses ordinary4090:67DF otherwise, and chooses4090:966A for stage11. The stage11 path also follows the parent and its+1C owner before writing cooldown+62, unlike the ordinary direct parent write.

Source966A beginsraw749F6A and leads96E6 then973E; it selects valid event1 then2, sets target flags and Shoot state, and performs its own completion. The original child translation stopped its captured source interval at749F6A, excluding this distinct collision completion path. This identifies the missing semantic branch statically; the new event observer will confirm its actual setter/callback caller rather than changing the event index in the renderer.

The private sprite host was independently checked as an exact15-group inverse of frozenDDC1 host by `tools/check_sprite_mode_replay_host.py`; report18858DA5 bindsA19E and all seven checkpoint artifacts. New child observer `tools/bizhawk_probe_child_event_producer.lua` B01A4F35 observes12874 entry arguments,12884 event store,12920 layout store,36F77C/780 callback selection and fixed observed child callback/event bus writes. It retains ordinary0/1/2 chronology and the first unsupported event, then snapshots at the next outer frame boundary. Its new hostC8EE is an exact six-group inverse ofA19E. Author Lua fixtureDC1991F8 demonstrates the expected0/1/2→5 chain, bounded completion and wrong-state refusal with no guest write API; actual caller evidence remains a separate root replay.

## Finalized event writer replay

Root's original child-event replay exited0. New `tools/verify_child_event_producer_capture.py` SHA2567DEF33BDC53A094C41D83A7756508632787DED650D2B21B49BD91770EDE477BF independently binds finalized launch342902F8918978C3D6A37EA259110D2CA8C80E86187921543ABB604D947A1144, traceC77F666BE72A7AAB8C85852D95FEB1B35D8CF48946CB42038610B946C4486061 and the original stage11 branch bytes. Report `build/child-event-producer-independent-20261117/actual.json` SHA25664B03A497EEDD4AD933734C98875F859BA42407E6E5EBFEDABF9D3C8C11C4581 passes this bounded source-caller proof:

| Core | Observed event/callback ownership |
|---|---|
|89587|New child020112B0 with P1/P0 child resources receives event0 from085B955C and callback085B9800.|
|89610|Child receives valid event1 from085B98D8 and callback085B9C00.|
|89627|Actual generic collision route0836F77C/780 replaces085B9C00 with retail083723E0; bus write to child callback confirms the assignment.|
|89628|Retail callback invokes08012874 from LR08372410 with requested event5; actual08012884 store writes event owner0201136A from1 to5.|
|89629|Diagnostic returns at the next outer frame boundary, mode remains7.|

The source event2 is valid but was not reached before this stop. The initial constructor observes stale event5 left in the reused presentation and explicitly replaces it with0 before the child executes; that initial stale value is not the erroneous later selection. The callback chain and current P1 remain the same child's ownership throughout. The new capture therefore confirms the missing stage11-specific callback route, not a slot-reuse explanation.

The restored Core again differs in the same15 byte positions and values as the sprite replay; the report includes the complete difference list and retains the same CPU/extension/suffix/five-RAM qualification. This diagnostic stops at the first unsupported event5; the later event6 and mode-word overflow are established by the separate sprite replay. Corrected source callbacks and successful corrected gameplay remain later work.
