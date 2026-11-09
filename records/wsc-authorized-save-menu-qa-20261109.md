# Original WSC authorized-save-copy menu observation: independent QA

The completed original-only `build/bizhawk-wsc-saved-20261109-menu3` observation passes independent audit. The224×144 screenshots show the Battle Spirit Ver.1.5 title, followed by Single Battle, Link Battle, Options, D-ARK and Collection. This is an original reference observation using the user-authorized development copy, not GBA final QA, a migration test, an unlock-completeness claim or actual Shoot entry.

## Evidence and exact save handling

| Artifact | SHA256 |
| --- | --- |
| Independent audit, `build/wsc-saved-menu-qa-20261109/audit.json` | `E28DD2E2878ECB0F03A8B193CB657DCBC870A4891B75E49DA5AB305F64A1C169` |
| Rerunnable audit, `build/wsc-saved-menu-qa-20261109/audit.py` | `834CDF7F467CADBDB7A6D4B8200C0922AF7A919B92158921E36180B644FE37B2` |
| Completed menu3 launch | `E58E4C8E3FD04CF4958516C8DF570E1DCD2A09E409F397E5D4E4F36C142E28F8` |
| Original loaded ROM | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| Authorized archived32K cartridge copy | `051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F` |
| Native33,792-byte SaveRAM wrapper | `D855BBDEED1F058B9769A11D6EDFB9AF8F863A22A7F2658F3F8141A641622185` |
| Actual initial cartridge SRAM | `0C338228153BBEAD2048EBD6730F8364055D787D86C1F3C1B1CB82AF03F36448` |

The audit and report use LF. Reproduction uses the pinned Python runtime and `build/wsc-saved-menu-qa-20261109/audit.py`, from the repository. The audit opens only the authorized archived copy and run artifacts; it never opens the original `.sav` path. The original-preserved flag is the launcher's attestation, while the independent check confirms the archived copy still has its pinned hash.

Calibration was a separate fresh boot without staging the supplied cartridge save. Its1,024-byte internal EEPROM dump exactly prefixes the unchanged32,768-byte cartridge copy. The resulting wrapper has no extra cartridge EEPROM bytes, exactly33,792 bytes, and matches the actual file used by menu3. Archived BizHawk2.11.1 source `build/wsc-user-save-copy-20261109/system.cpp:235..265` checks total size and loads internal EEPROM, cartridge EEPROM, then SRAM; `WonderSwan.ISaveRam.cs` passes the full buffer length and rejects failed native loads. Their archive hashes are recorded in the audit.

The initial live SRAM equals the entire authorized copy after exactly two expected startup changes:004E04→01 and007302→00. All other32,766 bytes match. These are exact expected values, not ignored offsets. The loaded original's actual DS1000/zero-AX setup and stores at74FC1F/74FC4A are checked directly. Five mutations at both changed bytes and three neighboring/last bytes are rejected by full-buffer equality.

## Actual input, snapshots and isolation

The final recursive inventories match all calibration8, failed-menu1 eight and completed-menu3 sixteen files. Exact emulator/core/script pins, full8MB loaded ROM, native wrapper, disabled autoloads, private desktop and isolated writable paths pass. Lua is `D6797F4B...`; corrected launcher is `AC5A4936...`. Both preserve the old calibration observer37CC87AF and original launcherDD571494.

| Observation | Relative frame | Core frame | Mode / stage |
| --- | ---: | ---: | --- |
| Initial live SRAM check |0|1|Startup|
| Start pressed; title snapshot before the next advance |3900|3901|3 /0|
| Start released |3904|3905|—|
| Menu snapshot |4200|4201|3 /0|

These are actual core-frame timestamps, not independently logged host wall-clock timings. Both complete64K RAM/32K SRAM snapshots and both native-size screenshots are verified. The observer contains no RAM/register/savestate write API; the authorized copy is loaded through the frontend's native SaveRAM interface before ordinary input.

## Preserved failed observations

Menu1 failed its original strict copy-equality guard at initial core1, before the observer's first ordinary input. Its only trace row is the initial phase line; it has no screenshot or completion marker. The captured SRAM differs only at the two source startup changes above. It is not a successful menu observation.

Menu2 failed before emulator creation because Windows-generated backslash keys were deleted/looked up using a slash-separated string. It retains exactly four staging files and no launch record, trace, loaded-ROM dump or completion marker. The independent review initially missed this separator mismatch.

The pre-fix source was not archived before that attempt. Reversing only the three documented directory/path-normalization substitutions reconstructs exact prelaunch-sampled hash `8B9E03A760C49DDCF2ECA6DD19BB264A63322801152F7A52E88BD2A13B463580`. The audit reproduces its KeyError using Windows path keys without launching an emulator. Corrected menu3 uses `as_posix()` and normalizes the old calibration report's keys. Thus these were two distinct diagnosed failures followed by a corrected observation, not successful or identical retries.

No emulator, save write, core edit, guest-state injection or original-save read was performed by this independent auditor. The GBA v72 component/runtime QA remains separate; Shoot and historical E5 remain unresolved.
