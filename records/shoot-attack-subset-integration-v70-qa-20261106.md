# v70 combined attack and spatial-subset layer: independent final audit

Both completed fresh builds `build/repro-v70-20261106-a` and `-b` pass a complete independent inventory comparison: all **281 relative paths and SHA-256 hashes** match. The frozen main is `7364FDF6FF171080B6F84ED56C7201074B04668AAB4B546464D44F2B7ECDB326`; all nine reviewed source-tool pins remained unchanged throughout this audit. All three commercial input hashes and all **111 manifest asset/layer entries per build** were recomputed directly.

Independent complete report: `build/repro-v70-final-audit-20261106/audit.json`, SHA-256 **D87DBF8491B363F0DE75264E49F04DA750A1598B417F891A46F176129A920A7E**. The rerunnable audit script is beside it. It imports no production builder, parses frozen main constants independently, and rehashes both complete output directories after running the independent verifiers.

The exact actual chain is:

| Artifact | SHA-256 | Inverse to preceding row |
|---|---|---|
| v67 result layer | `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F` | Historical audited predecessor |
| Retained `shoot-caller.gba` | `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738` | Complete 96-byte resident spans |
| Retained `controller-bridge.gba` | `72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC` | Complete four-byte internal bridge |
| Retained `shoot-attack.gba` | `B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B` | Four-byte hook plus complete 1,824-byte payload |
| Final `current-candidate.gba` | `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717` | Four-byte subset hook plus complete 24-byte payload |

Each inverse compares the entire actual eight-megabyte ROM, including all declared padding. The four new spans from v69 total **1,856 declared / 1,402 changed bytes**. Including the prior internal bridge and resident callers, the complete ancestry from v67 totals **1,956 declared / 1,496 changed bytes** over seven spans. An outside-boundary corruption fails the four-span whole-ROM inverse independently of a final hash gate. The actual retained bridge is byte-identical to both previously audited v69 builds.

Common paths whose hashes changed relative to v69 are exactly `build-manifest.json`, `current-candidate.gba`, and `current-candidate.json`. The six added paths retain both intermediate ROM/manifest pairs and their two independent verification reports. Every common intermediate artifact outside those three paths is unchanged.

The frozen independent resident-caller, controller-adapter, attack-dispatch and spatial-subset verifiers were rerun against **both completed full builds**, and every resulting report is byte-identical to its frozen build counterpart:

| Check | Exact report SHA-256 |
|---|---|
| Resident callers | `B079E66FA7DE910679E6D83539F8EAABF2BD1642A4B65D98F7140D10B67062F5` |
| Internal bridge and closed external route | `ACCAA6312E68606199B35F5588BEE28C860F0AF6CD9C051636A02A61C4053525` |
| Source type-1A/1B attack consumers | `02E7819CC861561CC8E747683420294B7CB0F9A691AE2BEF4A355261F29368FD` |
| Source-normal spatial subset | `4F5A9EDA33FF91BE70A94DB5240814ADA94EAEBD2CE2F7E6B1FCF00E729543B9` |

The attack check executes 832 dispatch, 366 living/dead/full-metadata and 44 constructor cases, with 22 direct negatives. Its detailed independent source/ABI/service limits and frozen negative-label correction are in `records/shoot-child-attack-qa-20261106.md`. The subset verifier belongs to the terminal review and is independently rerun here without broadening its scope: **544 actual ARM cases and seven negatives**. The actual manifest retains **1,726,545,920 unresolved nonpattern input pairs** and false whole-domain/external-route flags. The retained domain artifact remains `OPEN_DOMAIN`, SHA-256 `5DBB2620877D5ADEE92338B87B285610914CA07F2C484077846A602EDA707B46`, explicitly tied to its v68 predecessor rather than presented as a new complete-domain proof.

The external retail case-5 allocation, progress branch and ordinary callback were compared directly with actual retail bytes. The external scene-route area remains blank. These internal repairs do not establish actual Shoot entry, complete reachable player X/Y or camera lifetime, or resolution of the historical ordinary-battle E5 failure.

The fresh ordinary-input Korean regression was independently reaudited against the actual full-A final ROM using frozen result verifier `C07BCAC2EBEF7803FEAB6B6ECC772273E1C101D281BC6B8E5BB547490716A0FD`. Capture `build/bizhawk-result-v70-20261106-a` passes all **61 captured files, eight full snapshots and 1,508 visible WIN-label pixels**, with five negative selfchecks. Independent `build/repro-v70-final-audit-20261106/ko-runtime-audit.json` is byte-identical to the root report: **D7B85F2D0606FB4D26B499CFC1388E45D358A7B3CE908B3B8A204102218B8DC0**. Launch is `33F7CC62BE562B590C4DBAB934CECBD6F91EA96D41687A9F98F21CE31F0E11FC`; trace is `A4EBD51481C82F002156FB5AAE451CC3BD6CB7B7E94B9DFCA0DA66D1D6F675C2`.

The current accepted-ROM guard was independently reviewed before capture verification: `build/shoot-attack-dispatch-qa-20261106/extended-capture-guard-audit.json`, SHA-256 **ABD11AB9567E507F222C4AE8ECE453123E0CFD8D5ADE459AE0292DC59472F8CE**. The entire actual inverse chain is required; five single-byte corruptions in both new hooks, both new payloads, and outside the spans reject before capture I/O.

The runtime coverage is natural Korean WIN and retained rendering. It does not cover actual Shoot gameplay, LAST CHANCE, DRAW, complete campaign, fresh-process language persistence or full localization. The independent reviewer launched no emulator, accessed no save content, wrote no guest state and modified no source ROM, production ROM, main builder or frozen production tool.
