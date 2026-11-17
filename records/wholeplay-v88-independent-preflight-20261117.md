# Independent v88 full-run preflight

The new full-run host and Lua passed independent preflight against both written E212 build outputs. This is a static and recorded-input check before the root-owned emulator run. It does not depend on an imported save or checkpoint.

| Artifact | SHA-256 |
| --- | --- |
| `build/run_wholeplay_v88_20261117.py` | `42940495A768F9F6B5C6630EE6895E139F2BA18B310D33D0F17E718A8C8E5D3F` |
| `tools/bizhawk_probe_campaign_wholeplay_v88.lua` | `27E274E9AE6C845748FE8037FE1269992A196D604CBA7D16371236FF79DA90C6` |
| `build/wholeplay-v88-reviewed-pins-20261117.json` | `B33913F5C9A105A5A789598B2855C49DB5FFF84C4C6C0373F585260F8E9E4E0A` |
| `build/wholeplay-v88-qa-20261117/author.json` | `153CB97BBE7C507F02B5EC1CE153135890F519C62B59567A055E9C81181DCA08` |
| `build/repro-v88-20261117-{a,b}/current-candidate.gba` | `E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C` |

Reversing the host version, exact ROM pin, and one extra Lua pin reproduces every normalized byte of the previously reviewed v86 launcher. Its frame budget remains 120000, the private desktop deadline remains 1800 seconds, fresh per-run data directories are used, and the score and two stage-boss authorization tokens remain as approved. Eleven Lua pins are identical to the prior reviewed set. The additional pin matches the v88 wrapper.

Reversing the wrapper's four unique source substitutions reproduces the normalized v86 Lua exactly. They repin the ROM, replace the Shoot aim controller, insert four read-only interstitial observations, and require the actual mode 13 exit request before acknowledging the ending constructor. The interstitial observations exactly match those bound to the checkpoint replay. All 29 terminal and interstitial instruction pins match both bit-identical main build ROMs. The newly added Lua introduces no guest write, frame-advance, save/load, or bus-write registration API.

Independently applying the new predicate to all 65 recorded aimed frames reproduced every Left, Right, and qualified B decision through core 89469. On that frame the 15-frame mirrored forward lead is 547 and the vertical lead is −146. The existing actor, phase, target, attack, and one-write acceptance guards remain in control. During modes 12 and 13 the controller leaves all buttons released. The six-case author fixture verifies the expanded Lua's nested execution and counterexamples.

The new stage 11 Results main inventory checker at SHA-256 `16FC0767909B49744A057BD606DBFB8D9BAD9DD1681AED2440D0EBD47384343B` reverses the entire main builder to the reviewed v87 SHA-256 `7B293379F8EA36BC9AE8264561F7F2A59660F7A03A78857FA9D4C44FD7C54F3E`. The independent recursive import walk found 13 local modules and no missing pins across the new and retained dependency lists. The replay preflight does not substitute for polling original build exits or for the two-build inventory check.

The revised checker at SHA-256 `3609503BC5B1F61500812F83F6AFA6E8E0C91FB03C1F449AB82D1B2EEF916E45` also verifies the exact isolated E212 component, its manifest, and the portable F12C verification report. It retains the reviewed inverse and selects the same main verification gate.
