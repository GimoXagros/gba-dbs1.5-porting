# Pause probe r2: copied adapter execution guards

New source `tools/bizhawk_probe_evolution_music_pause_r2.lua` SHA256
`450AE932AA673C2C631A698EB597C48F566587BFCEC97E2A665C81DCE2E4DA51`.
New author checker `tools/check_evolution_music_pause_r2.py` SHA256
`13C76E99B0C56C6463777E8896441A10C60AAB476A957EB8F7A6A76584908DA6`.
Run `python tools/check_evolution_music_pause_r2.py --report <fresh.json>`.
Author report `build/evolution-music-pause-probe-20261116/author-report-r2.json`
passes ten actual-Lua54 policy scenarios and bounded alias-failure exercises.
Effective source SHA256:
`97198C5DBAD38D6F68F7475D6E48DF57C49B3740EDE834184E8A2A612FF26F2E`.

Original8ABD probe,9CAF checker and their record remain byte-identical. R2
changes only the telemetry banner to14 hooks/512 maximum event rows and
adds two read-only canonical IWRAM execution hooks. All input decisions,
deadlines and normal success criteria remain exactly those of8ABD.

Independent KO review identified a boot DMA copy of ROM0837B33C..0837B4FC
to IWRAM03000BF0..03000DB0, including the patched branch at03000D0C.
The new03000D00 hook logs/counts copied request entry and sets explicit
failure `failure:copied-request-entry-executed`. The03000D0C callback logs
the copied cache branch, writes/flushed/closes all music summary/counts,
writes/closes `result-done.txt` with
`failure:copied-cache-branch-executed`, then raises an error immediately.
The private host must treat either marker as failure and terminate its own
process; it must not wait for the next guest frame following that branch.

Both counters are emitted before the normal completion marker, including
zero counts. Absence covers these two canonical execution addresses only
during the bounded run; no universal absence or mirrored-address coverage
is claimed. The author scenarios exercise40 request entries with32 emitted
rows, then one cache-branch entry, summary-before-marker and error. No
emulator, ROM, host, main source or Git change was performed. Actual runtime
proof and independent review remain root-owned.
