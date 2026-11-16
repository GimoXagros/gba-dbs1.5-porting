# ID14 evolution event-table retest

Both retests ran through the native Korean menu with P1 actor 14, CPU actor 1, guest writes disabled, and no imported save or state. They used the same read-only observer, SHA-256 `A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA`. The ordinary controls held A for 20 frames on each of two approaches after the first attempt's four-frame pulses failed to reach Calumon. The native jump callback prepares for 16 frames and latches the short jump parameter when A is released during preparation. The two retests had identical input through the first ID14 event at core 8322. The retest host substituted only the ROM path and hash.

## Original event tables

In `build/bizhawk-id14-evolution-20261116-b`, isolated ROM `8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8` selected event `B054` for P1 ID14 at core 8322. That halfword came from `0835A22C`, past the original 11-entry table at `0835A210`. The resulting event row at `086C89E8` contained four `FFFFFFFF` words. The same presentation actor then reached the native event-initializer request at LR `08012918`, which accepted type-one song `04` on the same core. Player zero installed header `083820A8` at 8323.

ID14 still made its actual evolution request at 8382 and player zero started `6C` at 8383. At the selector, the previously observed stage `15` was ineligible for pause admission because the active cache and header contained song `04`. No Start pause or resume occurred. The original ground table returned event 25 at 9612 and stage `15` returned without a pause at 9672. The probe reached its bounded end at 12210 with exit code 1 and `failure:pause-target-not-completed`.

## Extended event tables

In `build/bizhawk-id14-evolution-20261116-c`, ROM `C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1` selected the source ID14 event 115 at core 8322 from `08D3F000`. No watched song `04` request replaced stage `15` during this lifecycle. The actual P1 selector at 8382 queued `6C` against active stage cache `15` and header `08385D14`. Player zero started `6C` at 8383 using header `08D43CAC`.

The controller delivered four frames of Start, 30 neutral frames, and four more frames of Start. Native matching-header comparisons led to MPlay Stop at 8384 and Continue at 8419. The cache and header stayed on `6C` at stopped boundaries 8388 and 8417 and running boundary 8422. The source ground ending event 25 used the relocated ground table at 9647. The same actor naturally devolved at 9706 and player zero restored the original stage `15` at 9707. The final Korean battle snapshot at 9708 retained the restored native cache and header. The host exited 0 with `evolution-pause-resume-stage-return`.

## Independent capture scope

The verifier rehashed all 72 baseline and 44 retest flat artifacts. Both runs observed seven collision metadata reads and seven dispatches with zero odd addresses and zero E5 entries. The two watched IWRAM alias counts were also zero in both runs. These are bounded observations of the inspected execution sites. The historical E5 mechanism remains unresolved. Audio output was disabled during these captures.

| Evidence | SHA-256 |
| --- | --- |
| `tools/verify_evolution_id14_held_jump_capture.py` | `CE00E6B329E35FEB792FDCC24EC40D157E20A123A0AE3CC65EC8D2E4D5EAC98D` |
| `build/evolution-id14-independent-qa-20261116/attempt-b.json` | `9A98FE7F767E731A5A95F797797AFA525B5AA47DDBE95FEF239B5C8291446BE5` |
| `build/evolution-id14-independent-qa-20261116/attempt-c.json` | `C21553F056B12C5DA6D4AECE53702520C1804BD5405937D99ADBEB8E6A7A2B8E` |
