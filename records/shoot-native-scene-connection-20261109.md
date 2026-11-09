# Reproducible native scene connection packaging

NEW `tools/build_shoot_native_scene_connection.py` SHA256
`2C73B081970F3466CEE1932AC15CAA876F3292CB6A2C59916C6AE2071D652E2E`
builds only from exact v73 6A1AEBDD, original USA GBA, original WSC1.5,
tracked frozen Python dependencies, and the tracked1394-interval ownership
ledger. It does not read historical ROMs, captures, or ignored manifests.
The CLI is `input gba source output --manifest PATH`.

The isolated build at `build/shoot-native-scene-connection-20261109` passes:
`component.gba` equals approved6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331.
Manifest SHA256 is
`242392FDE02B9DD6666578EE97E0F5F3EBA26E684F60BECABCC66EC1EBAC8639`.
It reproduces D0 entry,84D target repair,C8 alternate HUD branch, and8AA1
HUD intermediate identities internally. Ten disjoint ExpectedWrites declare
152 bytes. All24 component orders yield6D and invert completely to6A.
Fifteen output mutations reject;48 actual ARM selector joins pass.

Strict no-inbound scans cover full entry reservation6FF380..6FF400 on6A and
HUD6FF400..6FF410 on the derived84D predecessor, with zero exemptions.
Ownership includes the complete tracked ledger, full inherited IRQ
reservations6FF600..6FF800 and6FF9C0..6FFED0 (including erased tails), and
the IRQ/fatal hook words. The IRQ extents come from the pinned tracked IRQ
builder constants, replacing the old ignored component manifest dependency.

Source/code contracts reuse the frozen entry selector assembler, target
WRITES and pure source/helper proof, HUD source/caller proof, and nonfatal
resident/source proof. No capture-dependent build/check function is called.
This is identity-preserving packaging, not additional runtime acceptance.
The subsequent actual positive-hit trial on6D found a child-resource
pointer defect before a hit. Main integration remains held pending its
separate correction and runtime evidence. No main, existing builder, Git,
save, or emulator was changed by this component.
