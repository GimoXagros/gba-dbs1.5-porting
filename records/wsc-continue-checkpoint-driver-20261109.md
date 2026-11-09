# Normal Continue to a fresh boss checkpoint

The completed original checkpoint replay ended at core95185 in mode9/stage7,
with P1 HP0. Its genuine final state is reused through ordinary Continue;
no player HP, stage, register or score write is introduced. No intervention
module is loaded or rearmed. The earlier Shoot intro HP1 was temporary and
restored saved HP0 before activation, so a fresh jump was not its remedy.

New `tools/bizhawk_continue_wsc_checkpoint.lua` takes the same five arguments:
`output`, `checkpoint_dir`, `frames`, `source_sha256`, `callback_order`.
The launcher supplies copied/pinned `final.State`, `final-ram.bin`,
`final-sram.bin`, `replay.txt`, and the authorized cartridge copy in output.
Budget1..5000 is explicit. Strict unique boundaries reuse frozen2DE2171C's
loader through `save("restored")`, replacing only reference metadata/files,
the old recorded-input parser and the initial mode9/stage7 entry condition.
Full freshboot equality, single safe state load, userdata clear/rebind, exact
restored RAM/SRAM/frame, and fresh complete restored-state export remain.

All13 keys are released while the menu initializes. The actual menu owner is
an active slot header0014+n*0110 with callback7F20:05DA; its default choice
byte at header+10+C6 must be1. Once that owner exists and A was released, send
one physical A frame. All later frames release every key, with no directions,
combat B, Start or repeated confirmation. Hook77F993 observes the actual
positive Continue branch, binding DS0=0C00 and SI to that owner's choice byte.
The preceding exact source tests are pinned at77F977..77F992. Continue requests
mode6; this is not a transition to stage6. The source initializes fresh P1 HP8
and default hard boss HP44 through its normal constructors/intro.

Hook76B8AC follows the pinned76B880..76B8AB installation of active07FA/D0B
input/post tasks. The getready priority precedes input processing, so input
can run in that same frame. The driver captures at the following safe outer
boundary only when controls were released, the owned active FIRST/SECOND pair
has the expected types/indexes/links, P1 HP8, boss HP44, and player pending
damage **byte** +58 is0. It makes no claim that earlier non-HP collisions were
impossible. Any unhealthy first active boundary refuses a positive result.

Outputs are `fresh-boss.State`, full `fresh-boss-ram.bin`/`-sram.bin`, screenshot
and `fresh-boss.txt` with Continue-hook, activation-hook, capture-core and next
relative frame. The genuine state API is called only outside callbacks and
preserves the checked frame/RAM/SRAM. Every submitted input frame is logged.
Success marker is `fresh-boss-checkpoint-observed`; exhaustion exports the
actual final state and reports `continue-bounded-complete` explicitly.

Frozen driver SHA256:
`F1921C318C347B73B687025F60A357CE0F4BEB1CFEEF149911BA52DCC173E5A2`.
Author `build/wsc-shoot-boundary-20261109/continue-selfcheck.py` passed six
actual Lua54 cases using the new wrapper and composed frozen loader: ordinary
Continue/healthy capture, bounded missing menu, wrong choice, wrong HP,
pending damage and changed composition anchor. Both exact original source
spans match C415. Its first fixture incorrectly used a payload as slot header;
the real slot-grid guard rejected it, and the fixture was corrected without
changing the driver. No emulator or supplied save was accessed by this author
check. Independent QA and root-owned actual execution are separate evidence.
