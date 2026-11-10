# Original WSC audio capture without visible windows

The 2026-11-10 request adds the WSC arrangements of brave heart, Beat Hit!, EVO,
and One Vision to the port. Song extraction and native reconstruction are separate
from this infrastructure check; the boot recording does not establish song identity.

A fresh copied C415 WSC1.5 was booted for 960 emulated frames on the existing private
Windows desktop launcher. No supplied save, save state, controller injection, cheat,
or guest memory write was used. All save/data paths were isolated. Original and
copied ROM bytes were checked again after exit. Physical audio was disabled with
SoundEnabled=false, SoundEnabledNormal=false and both volume settings zero.

BizHawk 2.11.1 supports `--dump-type=wave --dump-name=... --dump-length=960
--dump-close`. The command completed normally before its 60-second host bound.
The output contains stereo, 44,100 Hz, signed 16-bit PCM: 560,952 frames,
697,882 nonzero channel samples, peak absolute value 8,951. This proves usable
headless core-audio export; it does not establish fidelity of the requested songs.

Source references at the exact installed version:
- [CLI arguments](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.Common/ArgParser.cs)
- [WAV writer](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.EmuHawk/AVOut/WavWriter.cs): wave writer, PCM16, no video.
- [MainForm](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.EmuHawk/MainForm.cs): an audio writer requests core sound even when live playback is disabled; AvFrameAdvance obtains generated samples before playback attenuation.

Local evidence remains under `build/bgm-wsc-audio-export-smoke-20261110-a`.

| Artifact | SHA256 |
|---|---|
| original ROM copy | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| boot.wav | `21BE3917310921D112FC77E54860602E075941389D05B4B78D517E2103741313` |
| report.json | `7FBEC790A1180C65855EA70878FC826F4C92A916A58CBB8C3DF4FBD9336FDB3C` |
| host | `A080D3D306BFDE5D655482D7047A50261EF9E1E20DB2C56E1E4E5269D8C45100` |

The pinned native and original music schedules, normal evolution consumers,
loop boundaries, envelopes and channel balance still need independent comparison.
Neither this recording nor the earlier muted visual regressions count as restored BGM.

## Ordinary boot request discovery

The new read-only `bizhawk_observe_bgm_boot.lua` observes requests and WSC
channel payload pointers, without changing game memory, inputs or save state.
The original 960-frame WSC boot with this observer produced the exact same
21BE3917 WAV as the earlier run without it. Request04/type4 is queued atframe1;
its payloads are0668/0676/0684/0692. Opening requestDC/type4 appears at520,
with payloads8A94/8C60/8FF4/9332 at521. Channel bytes also contain status flags;
the low two bits identify the hardware channel.

The isolated native r1 DD6D73B5 also boots and produces nonzero core audio
without physical playback:44100Hz/stereo/PCM16,708179 frames,peak26563.
Native request00/type4 is queued at532, then01/type4 at534. This proves only
ordinary boot and existing music playback on the expanded image: the appended
four evolution scores were not selected by this boot sequence.

These observed groups provide narrow table-only audio fixture targets for the
next comparison. Such fixtures must be labelled test ROMs, not normal gameplay.

| Discovery artifact | SHA256 |
|---|---|
| bgm-wsc-boot-discovery-20261110-a/music-requests.txt | `47B26B2B7A50D9D4329CBB7116330FA5BDC688FCC32DA1CA26A445949EAEEA04` |
| bgm-wsc-boot-discovery-20261110-a/report.json | `F70E832C1354EF2879D345DD15C6DBF7BA158896C2ACFF52E3C609CBEABA257E` |
| bgm-wsc-boot-discovery-20261110-a/boot.wav | `21BE3917310921D112FC77E54860602E075941389D05B4B78D517E2103741313` |
| bgm-gba-boot-discovery-20261110-a/music-requests.txt | `7A08C04540340A261BB2253E26ACF45B2054ECE463F40C1429C18BC00F9AA57F` |
| bgm-gba-boot-discovery-20261110-a/report.json | `EDE9009CD67F570CD8FBF015C52EE8404BA7AD8E86BEEC1A031BE657F9F766B4` |
| bgm-gba-boot-discovery-20261110-a/boot.wav | `FF8EAE18479520058338F0E9A1069F61FEC37C2156018131349B5EE753DBD073` |
