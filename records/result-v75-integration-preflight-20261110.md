# v75 narrow integration preflight

PASS for the frozen main wiring, runtime inverse and private KO host.
`tools/verify_result_v75_integration.py` reuses the v74 verifier's four small
read/assert/hash/pre-capture helpers; it does not run the prior verifier or
repeat the old semantic suites.

The six affected builder/verifier calls use fresh output and manifest paths:
native scene → `shoot-child-rectangle.gba` (1477) →
`shoot-palette-calls.gba` (FF3A) → `current-candidate.gba` (46B3).
Each production report is freshly produced in the same output's intermediate
directory and checked against BAD282D7 /94F9FD0F /8CE38E62. The two new
manifest claims match their bounded changes and retain final-port limits.

The runtime auditor differs from frozen DFDD1752 by exactly13 added lines:
whole-ROM inverse46B3→FF3A→1477. Removing those two branches restores every
prior byte. Actual component comparison confirms five four-byte spans,
20 declared bytes and13 changed bytes, with exact whole-ROM inverses at
both joins. All other ROM bytes remain identical to1477.

The actual runtime auditor, with its first capture read intercepted, accepts
each of46B3/FF3A/1477 up to `launch.json`. It rejects32 byte corruptions
(every byte of all five words, their adjacent bytes, one retained prior
rectangle byte and the image's final byte), plus an extended image, before
any capture read. Three source mutations additionally prove rejection of a
wrong owner restoration word, an omitted palette call, and a wrong palette
restoration word. No capture files were opened.

The private KO host is byte-for-byte the prior v74 host with only
`v74-20261109`→`v75-20261110` and1477→46B3 replacements. Its existing private
desktop, input, sound, autoload/save-RAM and no-guest-write settings therefore
remain intact. It was parsed, not launched.

| Frozen item | SHA256 |
|---|---|
| Main | `F5CDCE4F4D51FAA2D95BE30BB2C93C819494F3B1EDDE3B660E39ACFDDE5FD1C0` |
| Runtime auditor | `C31719BAE4C6D1BBD6B92A6BA8C0AB04C1494339EEEDF6D0D61435CBD4279A67` |
| v75 KO host | `B006A842802BF90241538D9CCE744F75ED58889E2B14468745183C065B97120F` |
| New preflight verifier | `B50AD2678D664CC7CEFF7E3ED188B3F8BB9170D54D68C027124EAE245FDA8F97` |
| `build/result-v75-integration-preflight-20261110/report.json` | `85F385028FD750034D64D65D7A5F79835735E2251ECC7C0C515A502A371359F1` |

Run with the existing bundled Python and a new report path:

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u -X utf8 tools/verify_result_v75_integration.py --report <fresh-report.json>
```

The system Python lacked Pillow and stopped during import before checks;
the bundled environment completed without dependency changes. No main,
runtime auditor, host, ROM, capture or Git mutation occurred here. Fresh
full-build reproducibility and actual runtime regression remain root-owned
gates. This pass does not establish terminal IRQ acceptance, mode8,
historical E5 closure or final-port completion.
