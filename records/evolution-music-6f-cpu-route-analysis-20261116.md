# v77 CPU Impmon route for the 6F evolution song

Static analysis of the exact C344 candidate identifies a native CPU
Impmon encounter before a player unlock. The ordinary single-player
opponent selector schedules this challenge once. This record binds
the code and its conditions. Achieving the route in gameplay remains
a separate test.

## Native challenge producer

The reader at 0808B4EC loads battle-state base 03002310. The native
stage setter at 0808B6D4 writes physical stage byte 0300231E and
calls the challenge producer at 0808B6D8.

| ARM site | Word | Effect |
| --- | --- | --- |
| 0808B4F0 | E1D581BA | Read run flags at battle base plus 0x1A, address 0300232A. |
| 0808B4F4–0808B504 | | Skip scheduling if run-flag bit 0 indicates continue or bit 0x40 indicates the challenge was already scheduled. |
| 0808B508–0808B510 | | Read difficulty at 0300231F and index ROM table 0808B4E0. Its first three values are 0, 1, 0. |
| 0808B514 | E5D5801E | Read campaign progress at battle base plus 0x1E, address 0300232E. |
| 0808B518–0808B520 | | The difficulty adjustment plus campaign progress must equal 4. |
| 0808B524 | E5D5800E | Read physical stage at battle base plus 0x0E, address 0300231E. |
| 0808B528–0808B52C | | The physical stage must differ from 2. |
| 0808B534 | E3988050 | Set run flags 0x10 and 0x40. |
| 0808B538 | E1C581BA | Publish the updated run flags to 0300232A. |

At the stated comparison, Normal uses difficulty 1 and campaign
progress 3. The ordinary Normal table gives physical stages
1, 3, 6, and 5 for progress 0 through 3. Before applying the
special challenge override, those four stages select CPU actor
IDs 1, 5, 3, and 4. Physical stage 5 passes the exclusion.
The challenge producer's code contains no score or unlock-byte read.

## Native CPU selection and song

The opponent setup at 0808B638 reads the same run flags. At
0808B650, word E3180010 tests scheduled bit 0x10. The challenge
branch clears 0x10 at 0808B678, sets 0x20 at 0808B684, and assigns
CPU actor 11 at 0808B690, word E3A0000B. The shared writer at
0808B6E8, word E5C4000C, commits it to 0300231C. Character selection
for P1 separately lives at 0300231A.

The source C415 and native C344 evolution category bytes agree for
all 16 IDs. Actor 11 is category 3. The current native selector
reads category table 08D33380 from literal 080D14A8 and selects
category's song from 08D33390, literal 080D14AC. The category 3
request becomes 6F and its M4A header is 08D782CC. The original
source request is 04F8. A valid gameplay capture still needs
the actual selector's entry and actor identity, native player-zero
6F start-return and cache, one pause and resume, and eligible
natural devolution followed by the actual stage-track start.

The clear evaluator and permanent unlock commit are separate.
The former reads progress bit 0x8000 from 0300232C for Impmon,
or no-continue highest-difficulty clear with at least 600 D-Spirits
for Extra Guilmon. The seven previously captured GBA Shoot routes
had 89 complete IWRAM snapshots. Each had zero pending unlocks,
permanent unlocks, and progress flags at 03002328, 03002329, and
0300232C. Those captures provide no evidence of an unlocked donor.
The CPU route avoids dependency on those unlock bits.

| Input or byte span | SHA-256 |
| --- | --- |
| C344 full native ROM | C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278 |
| C415 full source ROM | C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7 |
| C344 challenge producer raw 08B4E8–08B55C | 1CA9AAB33449B1BBAAC6A39676C4F9ECFC27469AD48EC2BC2E8AA632F4B8E6C4 |
| C344 opponent selector raw 08B638–08B728 | 4E89B150250F0261C4B64960440A1538675DECEF39EB5C89805BEB90EB82246B |
| C344 evolution selector raw 0D14BC–0D14FC | 13CA07F8021C7E2A8E8C11CABF6DF2039C66267E2EB164799CC69C9C20AB0D57 |

All byte spans exclude the ending offset. This analysis used the
ROMs and previously captured IWRAM. It made no emulator run,
guest-state changes, or save-file reads.
