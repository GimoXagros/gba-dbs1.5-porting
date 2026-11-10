# Independent original four-score reconstruction QA

PASS for isolated structural/source/native-data reconstruction of component
DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049.
This is not an audible-fidelity or song-title approval. The independent
verifier imports neither the author extractor nor builder nor author QA.

The16MiB component fully inverts to the exact46B3 eight MiB predecessor
plus an all-FF eight MiB extension. It contains42 disjoint declared writes,
104245 declared bytes and104216 changed bytes. Only eleven four-byte words
change in the original image; all existing M4A engine bytes and108 original
song-table entries remain intact. Independent byte-granular pointer and
aligned ARM-branch scans find no old-image references into the three new
bounded reservations. This does not establish arbitrary computed-pointer
or runtime caller-domain ownership.

The independent source decoder reads the original sixteen channel payloads
from the six-byte source directory. It reconstructs every command/state
and derives note onsets by a closed-form fractional-clock equation rather
than reusing the author accumulator loop. Four longest finite durations
are3309,2753,2972 and2089 source updates. Silent infinite rest channels are
explicitly distinguished from their immediate native FINE representation.

All1917 native pitched notes and22508 per-update control samples were
independently decoded from complete M4A byte streams and compared against
source note/duration/wave/noise, original divisor/octave pitch, delayed
vibrato, eight-bit envelope division and stereo ceilings. Maximum bend
quantization error under that declared model is0.780689464 cents. Tempo95
produces a relative rate error of+0.002426551, about+0.243%, which remains
explicit rather than being called exact timing.

Six original32-sample waveforms (IDs1,3,9,10,11,14) exactly supply signed
PCM voices, including native loop headers and guard samples. The full32767
mode0 noise sequence independently matches the XNOR recurrence. Its taps
and stereo nibble roles are consistent with the primary implementation in
[Beetle WonderSwan sound.c](https://raw.githubusercontent.com/libretro/beetle-wswan-libretro/master/mednafen/wswan/sound.c).
No retail instrument or guessed song title is substituted.

Actual ARM selector execution covers all16 canonical characters with
busy values0,1,123 andFFFF:64 cases preserve the retained ABI and busy
gate, request the appropriate four new song IDs/type4, and retain the
native cooldown. Native1770 versus source2220 uses different platform
clocks; the numerical difference alone is not evidence of an interruption
regression. Request override and lifetime parity still require runtime
evidence. The original first report's speculative early-interruption
wording was corrected in the separate qualified report; both are retained.

Remaining risks are material: this audio component is based on46B3, so it
must be composed with the later280D display repair without dropping that
repair. No actual M4A player/mixer was executed here. Global vibrato phase
zero, note-phase restart, pan/amplitude quantization, finite silent-channel
lifetime and update latency remain declared approximations. Sound capture,
listening comparison and the requested title mapping remain unverified.

Final qualified report:
`build/wsc-evolution-music-independent-qa-20261110/report-qualified.json`
SHA256 B8D1D7047565FCB2E2709324928E5B996363EF0401C270787CA80440A402D3FE.
It records the final verifier hash and source/builder identities. Initial
reportA31D489D remains preserved with its original wording.

No emulator, main/runtime edit, full build, old test suite or Git operation
was performed. Only new independent verifier, reports and this record were
created for audio QA.
