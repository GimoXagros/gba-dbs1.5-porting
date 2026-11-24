# Stage 11 terminal repair and persistent Impmon reward

The post-Shoot campaign uncovered a second reproducible stage 11 terminal path. Its boss received a real player hit at frame 212178. The scene reached terminal phase 085CD340 at 212446 and then stayed at 085CD510. The game continued to run frames, while the transition counter and scene stopped advancing.

## Cause and repair

At frame 214911 the actual display guard at 086FFBF0 compared the auxiliary actor's previous animation event 5 with zero and rejected the late display handler. The actor was already hidden, with kind/flags 0326 and callback 085BF600. Only the player remained in the render queue. The earlier successful encounter left event 0 in that same field.

Ver. 1.5 at 7486AF sets auxiliary actor+4 bit 20 hex and installs its final return callback 4090:7DD8. It preserves the previous animation event. Native 085BF414..428 sets the same bit and switches to the corresponding return-only callback. The repaired guard reads this hide flag. It retains the surrounding checks of the actor callback, resources, owner links, single rendered actor, hardware state and visible map rows.

`tools/apply_shoot_terminal_aux_visibility.py` changes three existing ARM instructions, 12 bytes including unchanged bytes. It verifies the original source, native hide producer, final callback and preceding guard. On input `2A7E8296DDD1DB3898CF3484E5849E623066A6249D3F70B090374956213CD083` it produces `6F7B7D942BCDE6F9EFC223150D54672D352606988C1C31471799EFD7C16FA116`. The independent instruction test executed 16,512 predicate cases spanning old/new images, hidden/visible actors, event values and initial NZCV. Report `build/mode11-terminal-hidden-aux-20261124-repro/verified.json` has SHA-256 `AD2481C897498182BF44E1C5D160CCAAD7BA72FB3CD62193DD202337C5604F48`.

## Later award and cold load

The next campaign came from the genuine last-turn Collection checkpoint. One normal player shot reproduced the seven-round win and set pending bit 10. The title, character selection and a new Ver. 1.5 campaign retained the bit. The gameplay run reached all eleven campaign progression entries. Its first stage 11 aim failed. The original terminal failure and repaired terminal were then observed from the same pre-encounter state. The controller inputs produced the same hit and early scene frames on both images. The repaired image accepted hidden event 5 at 213116, ran the final scene and cleanup at 213625, and reached mode 8 at 213627.

At frame 225115 native mode 11 queued roster ID 11, moved bit 10 from pending to permanent and updated record+12. Ordinary name confirmation went through the FF exit and returned to title mode at 225711. A fresh emulator process loaded a copy of the generated EEPROM, SHA-256 `00AA36346337A7788FCF0A302D350E31524A98CF5BCF00AA1FE83290ED351E56`. At cold frame 3190 the earned Collection menu was open, temporary bit 10 was clear, permanent bit 10 was set, and the entire 196-byte native record and checksum matched the previous session.

All emulator windows ran on isolated private desktops. The successful joined campaign used 42 approved score adjustments on ordinary stages and one boss HP adjustment each in stages 7 and 11. The game performed each reward, record and mode write. The checkpoint retry precedes stage 11 combat. The supplied save was not used.

The portable six-capture audit is `tools/verify_collection_promotion_capture.py`. `build/collection-promotion-final-20261124/report.json` has SHA-256 `3BA2D37C715CC469BB11702D7CCA8E8484C440348CB4914E880ABB585D612283`. It authenticates the shared checkpoint between the original and repaired encounters, the exact native guard refusal, the aid ledger, the pending and permanent transitions, award queue, and physical reboot record.

To reproduce the repaired image, run `python tools/apply_shoot_terminal_aux_visibility.py INPUT.gba SOURCE.wsc OUTPUT.gba MANIFEST.json`. For the retained local capture inputs, run `python tools/run_terminal_hidden_promotion_v91.py c`, then `python tools/run_collection_promotion_coldboot_v91.py c build/bizhawk-collection-hidden-aux-v91-20261124-c`. The launcher waits for the emulator to exit normally before taking the EEPROM. The first diagnostic attempt on the corrected image closed before SaveRAM flushed. The reported cold load uses the second, normally exited process.

The source checks for Extra Guilmon ID 12 separately at 77A193..77A1B0. The earlier native bit-20 hook can set that permanent bit without queuing its character. This record establishes the observed Impmon reward only. Main-build adoption and subsequent regression on the combined image are separate.
