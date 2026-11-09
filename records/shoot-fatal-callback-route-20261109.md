# Source stage11 fatal callback connection

The isolated layer connects the already resident `085CD960` fatal selector at
the real lethal callback-selection site. It changes exactly four bytes at raw
`36E5EC`: `0500A0E1` (`MOV r0,r5`) becomes `DB7C09EA` (`B 085CD960`).
Both resident selector branches execute the displaced operation. No new code,
reservation, RAM field, task, external scene entry, or damage rule is added.

Source `760197..760204` first tests stage byte `ES:005C` against 11. Its taken
branch `76019D -> 7601EC` preserves the victim in AX, installs upper callback
`4090:7AB1`, follows victim `+1C`, installs `4090:7D8D`, and joins the common
cleanup. Difficulty and progression tests occur only on the non11 branch.
The existing resident selector implements that stage11 pair with native
`085BDD00` and `085BF204`; its 64-byte body remains byte-identical, SHA256
`49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246`.

The native hook is after the existing evolved-damage adjustment, signed HP
subtraction and store, and positive-HP branch at `0836E5C8..0836E5E8`.
Stage11 selects the repaired pair and joins `0836E604`. Non11 rejoins the
unchanged retail callback-selection sequence at `0836E5F0`, retaining its
`08371E74` / `08370BF0` pair. The complete source non11 difficulty table is
outside this layer's scope. Common cleanup at `0836E604..0836E630` remains
unchanged, including both `+76` clears, parent `+94`, and global `03004D40`.

The selector's stage comparison changes flags. A bounded per-NZCV consumer
analysis follows the actual common cleanup and all 14 attacker dispatch entries.
It deliberately does not treat unshifted TST/ORRS as killing C or V. Shared
returns reach the sole collision caller `08353FEC`, whose continuation has
`08353FF0 ADD` followed by `08353FF4 SUBS` before `08353FF8 BGT`. The only
import reached while old flag bits remain live is the typed freeze prefix
`0836F6FC -> 0836A69C`, whose `0836A6A8 CMP` kills them. Every path kills
incoming bits before reading them. This is a local flag-lifetime proof, not a
whole-program control-flow claim.

The author tool checks the exact originals and pinned existing consumer bytes,
the affected entry/interior direct branches and exact pointer references, and
the frozen resident adapter. Its actual ARM interpreter checks 768 adapter
joins and 160 HP/common-cleanup cases, comparing registers and ordered writes.
Eight mutations are rejected, including loss of the return caller's flag kill
and of the freeze-prefix flag kill. Inverting the sole four-byte write restores
the predecessor byte-for-byte. No free-space allocation requires a new blank
ownership proof; all resident code remains in place.

Frozen artifacts:

- Predecessor: `build/shoot-guarded-transition-20261109/component-c.gba`, SHA256
  `18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1`.
- Output: `build/shoot-fatal-callback-route-20261109/component.gba`, SHA256
  `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7`.
- Manifest: `build/shoot-fatal-callback-route-20261109/component.json`, SHA256
  `69D9E5140216D8479124DD230A5F1ED19676491FA10686D61542FD3DA28F5EE8`.
- Builder: `tools/build_shoot_fatal_callback_route.py`, SHA256
  `46A731B89D2EF9E41DF818C71C23BE8F939A14DFCDBF3263DF1DA73BC4D05A5E`.
- Contract: `tools/analyze_shoot_fatal_callback_contract.py`, SHA256
  `310DC0A39AA5055B29BCE81C3033D75B5A13AEC385F56C713739EF1391755395`.

Independent verification belongs to the separate reviewer. This layer does not
open external Shoot entry or establish a cause or repair for historical type E5.
