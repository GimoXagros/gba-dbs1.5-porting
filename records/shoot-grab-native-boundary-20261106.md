# Conditional native grab presentation boundary

Read-only inspection of actual v68 `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738` found a concrete source/native distinction if P1's generic grab of the Shoot upper actor is admitted. Reachability remains open, as documented in `shoot-grab-call-domain-20261106.md`.

The retained native grab branch selects grabber event52 at `08354F98..FA0`, then victim event48 at `08354FB0..FB8`. Both use native `08012874`. Its reader loads the presentation pointer at `+44`, loads the table pointer, adds `event<<4` at `0801288C`, reads the frame pointer at `080128A4`, and dereferences it at `080128BC`. It has no event-count guard.

The installed upper presentation starts at `085D0000`, table `085D0008`. Event48 indexes `085D0488`, inside the adjoining converted rules resource, and reads four words `[0x10,0,0,0x8FF03]`. Its frame pointer is zero. Source upper event48 instead reads `[0,0x1A8,0xFF03,4]` through the 16-bit source indexer. Consequently this path would not preserve the source's out-of-table bytes or subsequent accesses. This is a conditional mismatch, not a demonstrated runtime failure.

The actionable boundary is the generic victim-event selection. If an actual permitted grab is established, the fix needs a source-derived resource/consumer contract for events48/49 and the throw continuation; silently mapping them to an idle event or claiming the ordinary six-event hitbox remains active is unsupported. Without that reachability and resource contract, keep this path OPEN and keep the external Shoot route closed. No ROM change was made for this hypothetical path. The independently confirmed native attack1A/1B consumer repair is separate and can proceed.
