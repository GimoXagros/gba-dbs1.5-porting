# Four-score/display integration: narrow independent composition review

The frozen music and display components compose without overlapping writes.
Their exact16MiB union is
`C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346`.
This is a **provisional composition/preflight result**, not promotion of
C508. Root subsequently identified an actual production BGM cache range
problem for new IDs6C..6F and stopped the partial C508 builds. A separate
cache repair and final review are required. Existing C508 evidence stays
as a reproducible intermediate; no source builder or frozen report changed.

## Smallest reproducible order

Keep the existing main chain through exact46B3 owner-link. Build both
frozen components independently from that common8MiB predecessor:

1. Existing93BD display builder produces280D, now preserved as
   `shoot-display-epoch.gba/json`.
2. ExistingE477 music builder produces16MiB DD6D, preserved as
   `evolution-music.gba/json`.
3. New root composer1BFF overlays only four known display spans onto DD6D,
   producing C508/current-candidate.json. The old display packaging gate
   continues to check the separate exact280D intermediate.

Neither frozen builder accepts the other's changed input hash. Weakening
their exact input/size guards or running the eight-MiB display builder on
a16MiB image is unnecessary. Parallel common-predecessor construction
preserves their existing deterministic source/ownership gates.

## Exact affected sites and reservation boundaries

Display contributes only6FF6E8(4),6FF720(72),6FFDE8(4),6FFDEC(4):84 declared
bytes,69 actual changed bytes, no new RAM or stack allocation. Its unused
6FF768..6FF800 tail remainsFF.

Music changes exactly eleven old four-byte words:37C2A4/37C2D8/37C324/
37C378/37C3AC song-table consumers, D14A8/D14AC/D14B0 selector bases,
andD14C4/D14D0/D14D8 selector loads. The other31 writes occupy only the
erased extension reservationsD33000..D40000,D41000..D4B000,D74000..D7E000.
All42 music writes are mutually disjoint and disjoint from display;
104245 bytes are declared and104216 change relative to the FF extension.
All108 prior native song entries are exact. Existing M4A engine and normal
stop-call sites are outside these writes; that preservation did not prove
the new-ID pause/resume cache domain, hence the new blocker.

The independent production gate proves both complete inverse orders:
music inverse restores exact280D plus an entirelyFF eight-MiB extension;
display inverse restores exactDD6D. Removing both recovers exact46B3.
It verifies every payload against the frozen music manifestAC3BC1D7 and
the display manifestF8C53C3C. Newly supplied84 display bytes add no pointer
or ARM-branch encoding into the music reservations. The original music
builder's complete46B3 incoming-encoding scan is retained via its exact
fresh manifest; the gate does not claim a new universal Thumb/data census.
Eight meaningful inverse corruption controls include payload/header,
ordinary engine, display, final-extension and dropped-display cases.

## Capture-free gate and source handling

NEW `tools/verify_evolution_music_display_composition.py`, SHA256
`00612F8F332D8C4217F7C35DC3625D11AD212E5D0F82F175989CBE36F712F6A5`,
uses only explicit ROM/manifests and pinned source tools. It does not read
emulator captures, source saves, earlier reports or hardcoded build images.

```powershell
python -u -X utf8 tools/verify_evolution_music_display_composition.py --before <280D.gba> --audio <DD6D.gba> --after <C508.gba> --music-manifest <fresh-music.json> --display-manifest <fresh-display.json> --report <new-report.json>
```

Frozen report `build/evolution-music-display-composition-qa-20261110/report.json`
SHA256 isFAFF1A4105F0F9A555FAB4FA18B3599EBA27915B6796E51C19AF27F4A1A38FD0.
The root main now regenerates its input artifacts and pins that report.
WSC C415/native996D source identities remain exact; the music analyzer2ED6,
builderE477, display builder93BD, independent display packaging gateE82C
and composer1BFF are hash-bound. The original score/PCM/selector semantic
proof remains separate; no historical full suite was rerun here.

## Sixteen-MiB observer and actual-host preparation

The existing ordinary result observer has one hardcoded8MiB ROM dump.
NEW `tools/bizhawk_probe_result_languages_16m.lua` reads the unchanged9281
observer and replaces only that unique dump extent with16MiB. Its SHA256
is5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF;
whole effective body is904909A5AA5A5FA2316FA185D5D2D3F2142657CD821274ED52E29C451E1FA987.
The complete input/label/EEPROM/300-frame behavior is otherwise identical.
The actual host must pin both5D62 wrapper and transitive9281 source before
and after execution. Root's corrected6286 host does so and records the
wrapped source identity. The older1C2 host stays unexecuted.

NEW `tools/check_result_16m_wrapper.py` SHA256
47D81D520D89A746B5A2A932FF0E467D6436B7B56BDFFD18092C725D78FE625A
executes six composition/binding cases and three controls with actual
Lua54, including complete composed syntax. It does not rerun the ordinary
game flow. Report `build/result-16m-wrapper-qa-20261110/report.json` SHA256
is6867C97688CB770E0DB18E4685461F35BFD7326F58CD25AFD0552F577D439580.

## Main/runtime/host narrow source review

The provisional5794 main,3E71 shared runtime and actual6286 host pass
NEW `tools/verify_music_display_v77_wiring.py` SHA256
06C2B3B76788FADA73B7D3AFB00BEB9404465D559E4786957690D25A8A367FFD.
Removing only reviewed changes reconstructs the **entire** frozen v76
DE4B main,665A runtime and4321 host byte-for-byte. Main source CRLF is
preserved; no capture byte is normalized. Read-only Git HEAD3ed126e was
used only to resolve the prior source text during review.

The source changes are the two intermediate paths/layers, frozen parallel
builder/composer calls, separate music author/production gate calls and
pins, bounded music metadata, C508→280D inverse and correct observer/launch
identity. All earlier production callers/gates/metadata bytes are retained.
The final physics slice check remains valid for16MiB because it compares
the same unchanged low-ROM range. Complete loaded-ROM validation remains
full-image equality; it cannot pass by truncating to the old8MiB prefix.

Actual audit-prefix calls accept C508 with5D62 and legacy280D with9281 up
to the first capture read only. Wrong8MiB observer, six mutated ROM sites
and truncation reject before capture access. The report is
`build/music-display-v77-wiring-qa-20261110/report.json`, SHA256
D30DCEA94BB501CDCBF8D17AD154B36D4845B970D2E27658777D1068C7225A7D.

## Fresh inventory and subsequent cache-layer handoff

For the provisional C508 chain, v76's310-file inventory gains exactly six
paths: two intermediate ROMs, two manifests and two new intermediate gate
reports. Predicted totals are316 files and122 manifest closure entries;
these are structural expectations, **not completed-build observations**.
All prior shared files should remain exact except current-candidate.gba,
current-candidate.json and build-manifest.json. Root stopped the partial
A/B builds before accepting those expectations.

A dedicated cache-fix layer can retain C508/FAFF as an intermediate, then
add its own exact final hash, whole inverse, source gate and final manifest.
Runtime inversion should remove that new layer first, then recover C508,
then280D and the unchanged legacy chain. Final main/runtime/host pins and
inventory counts must be reviewed again after the root's final freeze.

The later ordinary KO audit must keep the complete16MiB loaded image and
compare native graphics/trace with v76. Relocated table pointers may remain
in raw IWRAM/EWRAM stacks; every byte/word difference must be retained and
source/consumer qualified rather than normalized away or blindly asserted
equal. Actual four-score audio capture/listening/title evidence is separate
from this composition gate; root reports its fixtures separately.

Only new independent gate/wrapper/checker/review files and reports were
written. No old observer, ROM, main, host, capture or Git file was edited,
and no emulator or full build was run by this reviewer.
