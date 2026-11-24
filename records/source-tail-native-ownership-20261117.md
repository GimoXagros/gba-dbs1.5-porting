# Extended source record: native ownership boundary

This is a bounded design record, not an installed save-format change. It uses the E212 Results candidate and the independently checked 36A12620 scene/eligibility composition.

The native statistic function `0833ED64..0833EE10` selects the local player's identity, multiplies it by four, and addresses record `03001120 + 8E + identity*4`. It increments the second halfword and, for a win, the first halfword, then calls the ordinary serializer with selector6. The source fifteen-character layout therefore cannot be restored merely by extending the native C0-byte checksum count:

- IDs0..11 occupy `8E..BD` and fit the existing statistic area.
- ID12 starts at `BE`, which is already a live retail progress flag. Actual loads/stores at `0808B574` and `0808B5D4` use its bit10 for the retained unlock path.
- IDs12..14 continue through `C9`; `C0..C3` already hold the native checksum and `C4..C7` are included in the native 25-block transfer.

The finite literal census finds the checksum pointer `030011E0` and the next distinct nearby literal `03001280`. It does **not** establish that the intervening RAM is free: computed aliases and indirect ownership have not been discharged. No RAM extension into that apparent gap is authorized by this record.

The implementation direction is a bounded stack snapshot of logical source `BE..E7` (42 bytes), leaving the native prefix and progress flag in place. Native statistics for IDs12..14 must use the snapshot; IDs0..11 retain their existing native addresses. Source tag/name/count readers and award producers can consume the same typed snapshot without a persistent RAM allocation. The source owner review confirms that the mode22 view copies its counters into scene-local state, its name renderer consumes the four bytes synchronously, and the award helper finishes its pointer use before return.

Canonical progress flags require an explicit split: source CA bit0 is represented by the exact block26 eligibility marker, while retained native BE owns the existing other progress bits. A serialized snapshot must not create a second independently persistent CA bit0. The proposed extension stores the remaining source fields in a versioned, integrity-checked envelope in blocks27..33; ordinary blocks0..24, Shoot25 and eligibility26 retain their owners. The earlier C0..E7/40-byte proposal omits ID12's first statistic and is superseded by the BE boundary.

Before installation, prove the complete live block-call census on the composed image; valid/fresh/legacy/corrupt/read-failure behavior; default reset; preservation of every unrelated block; and actual ID12..14 increments through native callers. Preserve 16-bit counter values even when ordinary awarded states are decimal digits. Do not claim recovery of old statistics overwritten by the former checksum collision. Device failure and power-loss semantics must be stated separately from modeled block operations.
