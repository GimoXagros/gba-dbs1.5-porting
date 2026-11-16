# Ordinary P1 ID14 evolution capture QA

The ordinary Korean-language attempt used isolated ROM SHA-256 `8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8` and read-only probe `DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B`. The host ran with a fresh private configuration and no guest writes or state injection. The audit verified the host and all probe layers, the loaded ROM identity, 72 capture files, and nine frame-boundary snapshots with six captured memory regions and a screenshot apiece.

Battle-entry memory at core 4390 identified P1 as actor 14 and the CPU as actor 1. The only evolution selector belonged to CPU actor 1 at core 8539, followed by player-zero song `6E` at core 8540. No P1 ID14 evolution or target pause/resume sequence occurred. The run reached the result at core 11910 and its bounded end at 12210, with exit code 1 and marker `failure:pause-target-not-completed`. This attempt establishes target absence.

Both watched IWRAM aliases registered zero executions. The event journal counted 228 accepted queue observations, zero extended-ID selections, and zero watched tick-path song-04 requests. The collision journal counted 14 metadata observations and 14 dispatches with zero odd addresses, zero confirmed alignment observations, and zero E5 entries. Those counts cover this attempt. The historical E5 chain and ID14 runtime behavior at evolution remain unverified by this capture.

The retained capture is in `build/bizhawk-id14-evolution-20261116-a`. Its independent report, `build/evolution-id14-independent-qa-20261116/attempt-a.json`, has SHA-256 `C4121C7F39C27D708344042CEA842BFE62696C093FB0657DBD674A206F7DCF92`.
