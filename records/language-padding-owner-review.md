# Independent language-byte ownership review, 2026-10-21

The proposed byte `0300112F`, native record `03001120+0F`, is approved as a
bounded owner for strictly tagged values `A0..A3`. This approves the byte
allocation and commit contract below; it does not claim a completed language
selector, Digicode assets, or persistence under power loss.

The current inspected candidate is
`AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF`.
Rerunning `tools/analyze_language_consumers.py` gave
`build/language-owner-review-20261021/analysis.json`, SHA-256
`9B0E4A7C563C5F9497F02FAAFAADB5314D6CEDF5A00C6314AA62A11C24E9AD21`.
The original native record region `1F894..1FD30` is unchanged, SHA-256
`A29BE760B3E28AE415F2C617E2EA53FE820BF625D63C7E17857377BA8E1247E0`.
The native EEPROM read/write/retry routines and the wrapper's score sorter
were also compared with the pinned commercial GBA image before their actual
instructions were reviewed.

The finite inventory contains 25 commercial and26 candidate byte-aligned
encoded pointers into the record, with no header-interior pointer at
`+01..0F`; both images have the same17 aligned ARM literal loads of its base.
The native observed consumers assign semantics at `+10` and later. Header
operations are the first-eight-byte signature check, bulk initialization,
checksum, and block transfer. The normalizer at `0801FA98` leaves the header
alone. This reuses the inspected-consumer evidence in
`records/language-consumers.md` after validating its live identities; it
does not prove the absence of arbitrary computed aliases.

The first15 header bytes must remain
`44494D505320566572302E37322020`. Decode only the four exact language tags;
legacy `20`, other invalid values, and a language whose assets are not yet
implemented must have an explicit supported fallback. English is the
approved legacy/default behavior. A getter must not eagerly rewrite an old
record merely because its tag is legacy or invalid.

Native reset `0801F894` copies the original16-byte header and therefore puts
`20` at `+0F`; it intentionally resets the language to English under this
contract. A checksum mismatch clears the payload in `0801FBD0`, after which
the boot signature test resets the record. The checksum mismatch status is
communicated by flags internally, not reliably by a nonzero `r0`; a new
getter should consume the already initialized RAM record instead of
inventing another EEPROM read path. The low-level native reader's explicit
nonzero error is an out-of-range block index; normal indices0..24 fit the
configured64-block capacity.

For a language-only commit, direct native writer `0801FC5C` is appropriate.
It requires no register or stack arguments: it reloads `03001120`, computes
the unsigned sum across `C0` payload bytes, writes that sum to `+C0`, and
initializes its own block index/count. Native boot must have initialized
EEPROM and the RAM record, and the language edit must preserve the other
payload bytes. Wrapper `0801FBD0` is unnecessary for this edit: in addition
to optional unlock synchronization it normalizes record fields and sorts
the first three high-score entries via `080C12EC`.

The writer returns `r0=0` only after25 successful eight-byte writes, each
using the native retry/readback routine. A nonzero first failure returns
immediately. It preserves LR, but its caller must protect live registers
according to the actual native callback ABI; `r0..r3`, high scratch
registers, and flags cannot be assumed preserved. Check the returned `r0`
before restoring a saved caller `r0`. The reset helper is unsuitable as a
language commit API because its epilogue restores incoming `r0` and hides
the writer status. Several existing progress callers also ignore status;
they are not evidence of a reusable safe error UI.

The writer is sequential and has no rollback. A concrete counterexample to
RAM-only rollback is an `A0` to `A1` change where block1 succeeds and block2
fails. The physical header now has `A1`, but checksum block24 is still old.
Restoring the old language byte and checksum in RAM leaves physical EEPROM
invalid; a subsequent boot can reset the whole record. A localized error
and retained Options task are therefore necessary after a failed commit.
Retry may write the intended new record. If Cancel/Return is to discard
after an attempted write, it must successfully write the restored old
record before clearing the pending error. Ordinary cancellation before any
attempt needs no write. Neither approach guarantees power-failure atomicity
or recovery from permanently failed storage.

The guarded native-order model covers success and first failure at every
block0..24. With a failed block assumed unchanged, failures2..24 leave the
new header with the old checksum; this is a valid counterexample, not a
prediction that every device failure has those exact effects. It is
recorded in `build/language-owner-review-20261021/ownership-review.json`,
SHA-256 `89B0D70CB810F7766E904E711384055BB1DFE87D29BAB7E58A93475806A54D75`.
This model is static evidence, not runtime fault injection. No save file
was opened and no emulator was launched by this review.
