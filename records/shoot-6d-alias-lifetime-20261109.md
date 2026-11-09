# 6D static aliases: bounded facts and remaining pixel ownership

The next terminal-clear extension is **not approved**. The identified owners can share one logical blank mask, but clearing that mask alone cannot reproduce the source pixels after an alias reload. The corrected base49 component35D46BB3, its builder and ordering analyzer were not changed by this investigation.

## Positive owner and upload facts

| Owner | Source P0 | Native P0 | Fixed tile identities | Static descriptor |
| --- | --- | --- | --- | --- |
| Side1 companions, records15..29/45..59 | Actual character table P0s | Actual tables4A82D8/60B1E0 |109..144 overall|384..1152 bytes|
|93E7 child|3D44E0|085DB300|109..132|768 bytes,8 layouts|
|888B child|3D0CA0|085DB400|311..359|1568 bytes,18 layouts|

888B is positively bound to137hex, **not6D**: constructor74918B and initializer747CBF use137. Its pixels do not overlap the scoped clear tiles109..131. Constructor749CE7 and initializer747CA9 bind93E7 to6D. Both P0 flags are8 and both P1 header flags are0. Existing native adapters085C4500/4600 retain the exact P0 and tile-base arguments.

The source event setter7525FF..609, explicit-frame setter752796..7A0 and update752984..98D all skip graphics upload/task creation when presentation flag2 is clear.93E7 construction749D2C selects event0 and only ORs2000 into the presentation flags. Consequently creating this child or selecting its next static frame is not a restoration event. Its pixels come from the earlier standalone226E preload. The existing companion lineage likewise establishes static P0s and facing/priority-only flag changes.

Standalone226E performs a synchronous copy at752297..2A8 to `4000 + (tile_base << 5)` using descriptor0's exact byte length. A side1 companion preload therefore overwrites the same physical source interval beginning4DA0 as93E7. This is real shared memory, not merely equal numerical tile labels.

## Initial order and later restoration

The ordinary character2E74 constructor preloads companions at743867..3886. Shoot initialization selects SECOND065E and FIRST065C at747AD1..ADE. It then explicitly preloads93E7 at747CB7, followed by888B at747CCE. The optional reconstruction after747CF0 uses the retained FIRST actor and calls2E74 at747D0C; its companion is base49. It does not restore the side1 companion pixels that the93E7 preload just overwrote.

Thus a still-live side1 companion at Shoot entry can already read93E7 pixels in109..132; any companion payload tail above132 retains its preceding bytes. This establishes the overwrite order, not that such a companion actually remains live in a natural run.

The five direct2E74 callers and their scheduling are checked by the existing `analyze_shoot_companion_draw_order.py`: generic initialization, Shoot initialization, evolution/devolution completion and boss reconstruction. The boss path76BC32/37 positively selects SECOND; the two form-completion paths operate in existing actor tasks. Native preloads precede the battle6000 presentation-list consumer. The corrected current expiration hook already expires the base6D overlap using actual descriptor length, even though the current renderer intentionally recognizes onlybase49.

Every compared tile in the109..131 overlap differs between93E7 and each of the30 companion payloads. A later companion preload can therefore replace93E7 pixels with different data. The native renderer instead selects each presentation's immutable P0 descriptor and copies its own pixels into dynamic OAM staging. Unmasking93E7 after a companion preload would show93E7's original pixels, not the companion bytes now present in source memory.

## Exact side1 companion preload extents

Every range begins at logical109 / physical4DA0. Ends below are inclusive; full per-record P0/descriptor addresses and byte ranges are in the report.

| Bytes | Last tile | Character records |
| ---: | ---: | --- |
|384|120|50,52|
|448|122|54,55|
|512|124|51|
|768|132|20,22,25|
|896|136|21|
|960|138|15,18,27,47,53,57|
|1024|140|19,23,24,45|
|1056|141|48,49|
|1088|142|16|
|1120|143|26|
|1152|144|17,28,29,46,56,58,59|

Partial restoration matters. For example a384-byte companion reload restores109..120, leaving121..131 unchanged. With a clear atBX284, the four affected tiles are120..123: only120 is restored. A single last-writer label for the whole four-tile interval would not cover arbitrary sequences of shorter and longer alias uploads.

## Smallest justified next step

Recognizing base6D companions plus exact93E7 P0, using `presentation.base + layout.tile`, would extend blanking with no new RAM or queue. That is only a candidate. It must also either prove the relevant alias uploads/consumers cannot coexist after197A, or model the actual surviving source pixel writer for each restored tile. Blanket child expiry is not a substitute: the separate3030 HP writer leaves that lifetime exclusion unresolved. No speculative writer state, asset substitution, new renderer change or ROM extension was installed.

`tools/analyze_shoot_6d_alias_lifetime.py` checks the actual source constructors/preloads, initial owner identities/order, static event-upload gates, native bindings/descriptor consumer, all30 companion lengths and positive pixel differences. Seven in-memory mutations reject wrong93E7/888B bases, wrong side1 reload base, event/update upload gates, indexed child flags and native child identity. Input identities are originalC415 and corrected35D46BB3. Status is `STATIC_6D_ALIAS_FACTS_PASS`, with `extension_approved=false` and `full_source_pixel_alias_parity_proven=false`.

Analyzer SHA256: `DA8E07CA76C1F2A29C8DDB735126BF83409758315B56300B9FFE759A294DAC6E`.
Report `build/shoot-6d-alias-lifetime-20261109/final-proof.json` SHA256: `596246D42A7F9E999F10729CEA3D8B8C38ECF237ADABA48B83E292A04ACEF9A7`.

No blanket other-writer census, live Shoot observation, emulator/save access, main-build change or full terminal-clear closure is claimed.
