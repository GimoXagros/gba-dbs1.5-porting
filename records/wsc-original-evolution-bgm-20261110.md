# Original evolution music: source extraction and isolated reconstruction

The requested names are **brave heart, Beat Hit!, EVO, One Vision**. The ROM
evidence establishes four original evolution score groups; it does not store
their names in the examined selector or scores. Names remain unassigned until
the original arrangements are identified by additional evidence or listening.
No external commercial recording was downloaded or substituted.

WSC1.5 `C415F227...` has the sixteen-character category table at `787267` and
the four `(sound ID, request type)` pairs at `787277`. The original USA GBA
selector `D14A8..D14F8` instead maps its three categories to the same `1C/04`.
Thus the current native evolution route collapses distinct source music.

| Category | Original four sound entries | Character IDs | Longest finite driver updates | New native song |
|---:|---|---|---:|---|
| 0 | `38..3B` | `5,6,7,8,13,14` | 3309 | `6C` |
| 1 | `3C..3F` | `3,4,9,10` | 2753 | `6D` |
| 2 | `40..43` | `0,1,2,15` | 2972 | `6E` |
| 3 | `F8..FB` | `11,12` | 2089 | `6F` |

The source bank starts at `3F0000`, with 268 six-byte entries containing the
channel-state offset, hardware channel, and payload offset. Each group starts
four channels at state offsets `A8,D2,FC,126`. Group F8 uses hardware order
`0,1,3,2`; the others use `0,1,2,3`. The finite scores end with `FFFF`.
The three unused channels have the exact zero-volume infinite-rest loop,
which is explicitly marked by the extractor.

The source interpreter establishes the four-byte header and two-byte commands:
`A0` amplitude, `A2` waveform/noise selection, `A3` delayed vibrato, `A4` noise
enable, `A5` separate stereo ceilings, and `C0..CF` envelope mode/period.
Header byte0 drives the fractional countdown skip at `75420A`; initialization
clears the accumulator and starts the first note immediately. Source times
are driver updates, never mislabeled as GBA frames. Pitch comes from the
actual divisor table `754837` with the source octave shift. The command
decoder rejects unknown instructions and unproved loops.

The isolated r1 component preserves all 108 existing native song entries and
the existing M4A engine. It adds four four-track songs using the original
32-sample waveforms and a full 32767-sample WSC mode0 noise sequence. The
noise recurrence/reset is corroborated by the [Beetle WonderSwan sound
implementation](https://github.com/libretro/beetle-wswan-libretro/blob/master/mednafen/wswan/sound.c).
It does not replace these tracks with retail melodies or retail timbre analogues.

The component expands the image from 8 to16MiB. Its declared new audio blocks
are `D33000..D40000`, `D41000..D4B000`, and `D74000..D7E000`. Every other
extension byte remains FF. The complete old8MiB pointer/ARM-encoding scan has
zero targets in these blocks; predecessor Thumb immediate branches cannot
reach them. A rejected `730000..760000` proposal and its 106 conservative
encodings remain in the manifest as diagnostics, not claims of real references.

Only eleven existing words change: the five song-table consumers, three
selector data literals, and three `SUB r8,pc,...` instructions replaced by
literal loads. There are 42 declared writes, 104245 declared bytes and 104216
changed bytes relative to the FF-extended predecessor. The complete inverse
restores the extension to FF and truncates to exact owner46B3. Main remains
unchanged. Native request cooldown `6EA` and occupied-request refusal remain
unchanged; the original WSC uses `8AC`.

| Frozen item | SHA-256 |
|---|---|
| `tools/analyze_wsc_evolution_music.py` | `2ED6FD43C11F636C11D38415AB07BA6B8FBE6E92531EB58890572BDCD09F8413` |
| `tools/build_wsc_evolution_music.py` | `E477925703C4DCD66A5239DCA1F0A806E208DAF02AD2FE95998C055330FC0077` |
| `tools/verify_wsc_evolution_music_author.py` | `E7AA94C393372062C9B526B3C5AF941553AA8013F0A8DA892CA99B71AAB330A9` |
| `build/wsc-evolution-music-20261110/component-r1.gba` | `DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049` |
| `component-r1.json` | `AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91` |
| `source-report-r1.json` | `B4DDA295E7FDE8AD5B2B63F75760881538A11968D6383489887D760F5D34E119` |
| `author-report-r1.json` | `D7B0A1E03B1AA25F7B627FF0CA316DF09364FEF12F6664FC7B17AEA3FF20B0FD` |

Author verification executes the actual native selector and request gate for
all sixteen IDs, both idle and busy: 32 cases. It decodes all sixteen emitted
M4A streams and checks all 1917 note keys, durations and voices against the
authored schedules. Three selector corruptions are rejected. This is author
validation, not independent QA or runtime evidence.

The reconstruction deliberately records its representation differences:
native tempo95 is 0.242655% faster than one source update per WSC frame;
native pitch bend has at most0.781cent quantization in these tracks; pan and
amplitude are quantized; global vibrato starts at a deterministic zero phase;
PCM note starts reset waveform phase; and the original silent infinite loops
become native FINE. Source-to-native update latency, stereo mixing, noise reset,
actual playback, song-name identity, and gameplay music restoration have not
yet been verified. The four requested songs are not claimed fully restored.
