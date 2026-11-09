# Experimental native entry probe independent QA — 2026-11-09

PASS for separate development probe D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C over approved main6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7. This permits bounded development observation only. Complete external entry, scene completion and release approval remain false. No emulator or save was opened.

The two writes are the four-byte nonlinking33FD04 hook and104-byte selector at6FF380. All108 declared bytes change. Their exact whole-ROM inverse recovers6A1A, retaining its fatal hook, initializer, scene bodies, main build and B9E68 progression producer. No progression, mode or HP forcing is added by this selector. Existing resident scene code retains its own source-defined state changes; this is not a claim that running the scene leaves gameplay state unchanged.

The originally proposed5C9900 cave was rejected by the stronger scanner because it had an unaligned mirrored pointer and a Thumb inbound encoding. The approved128-byte6FF380..6FF400 cave is entirely erased, has no pointer/ARM/Thumb inbound encoding at any checked alignment or mirror, and uses no ownership exemption. The independent1394-interval ledger plus original4MiB ROM, both approved IRQ reservations and fatal-hook overlays are disjoint from the cave, including erased live tails.

Reconstructing only selector word+76 at the former5C9900 address yields the reviewed104-byte profile9408A3EE46D6FE57F025611FD9C5BDDA2D92A51341F2382B33A3DBD8F51A39E7. All other selector bytes are identical. The default is the existing source0653 router086FC300; the selected source EEA scene is085C8000. The only relocated instruction is the tail branch back to original33FD08.

Actual source771F84..771FA1 proves stage!=11 && (difficulty==3 || (difficulty!=0 && !(progress&0400))). All3072 actual selector cases pass: every256 difficulty byte, stage classes0/7/11/255 and progress0/0400/FFFF. The selected R8 callback is correct; every other live register, SP, LR and CPSR is preserved. Writes are limited to the selector's own16-byte stack frame.

Four additional joins execute the real retained native allocator08011AC4 through original33FD18. Each begins with two typed active tasks, allocates exactly one0FF0 task, advances the count2→3, and stores the selected callback in its real header. The allocator does not forge CURRENT or progression. The actual0801201C getter resolves the new task header to payload+18 when supplied by the scheduler fixture. This is a constructor/current-task ABI test, not execution of the whole scene or initializer.

The real initializer08629800 remains the reviewed140-byte8FEDEC3D profile, and the existing later scene call at085C853C still targets it. Scene entry085C8000 still resolves CURRENT through0801201C. Existing callee and scene suites were reused rather than rerun. The actual native fatal hook remains unchanged.

Eight controls independently reject loss of stage11 exclusion, difficulty3 exception, zero-difficulty exclusion, progress polarity, condition-flag restoration, a changed progression producer, changed unused cave tail and changed initializer. Semantic predicate controls execute behavior checks before any output-hash rejection.

| Artifact | SHA-256 |
|---|---|
| tools/verify_shoot_runtime_entry_probe.py | FBC762178FE59DB9797B2272B5776C429608FC48747AFDC16A3ACAB91C37A05F |
| build/shoot-runtime-entry-probe-qa-20261109/report.json | 6F242A0EDF5574917E040B263B34D4EC2D66989F1D3AF25D68809174F0352081 |
| build/shoot-runtime-entry-probe-20261109/experimental.json | DF4EB38EA39F845B936A08CE0923B966BE8ECC729B697AD5FDEED16F3A08E746 |
| Source builder | 027FD5849411535D0C367B2C35E5978DECA381628744D62F0F868EDFDF3518E2 |

The new verifier/report are LF and import only frozen independent QA primitives. They do not import the production builder. Reproduce from repository root:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u -X utf8 tools/verify_shoot_runtime_entry_probe.py build/shoot-runtime-entry-probe-20261109/experimental.gba build/shoot-fatal-callback-route-20261109/component.gba 'C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba' 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --manifest build/shoot-runtime-entry-probe-20261109/experimental.json --layout records/shoot-guarded-transition-layout-20261109.json --output build/shoot-runtime-entry-probe-qa-20261109/report.json
~~~

The documented generic upper-victim event48 risk,8EF3 residual nonpattern domains, stationary-only transition coverage and native/source stage11 HUD skip difference remain outside this patch. See [source probe contract](shoot-runtime-entry-probe-20261109.md). No actual scene arrival, campaign completion or final gameplay QA is claimed.

