"""Bind naturally earned Shoot pending, later mode 11 award, and a cold-loaded save."""
import argparse
import json
import re
import struct
from pathlib import Path

from verify_collection_route_capture import sha


BASE = "2A7E8296DDD1DB3898CF3484E5849E623066A6249D3F70B090374956213CD083"
FIXED = "6F7B7D942BCDE6F9EFC223150D54672D352606988C1C31471799EFD7C16FA116"


def capture(folder, outcome, rom):
    report = json.loads((folder / "launch.json").read_bytes())
    assert report["outcome"] == outcome and report["rom_sha256"] == rom
    assert report["loaded_rom_exact"] and report["script_unchanged"]
    assert not report["visible"] and not report["physical_background_input"] and not report["supplied_save_used"]
    assert sha(folder / "loaded-rom.bin") == rom
    for name, digest in report["files"].items():
        assert sha(folder / name) == digest, name
    return report


def verify(entry, campaign, baseline, refusal, later, cold):
    opening = capture(entry, "retained-at-new-campaign", BASE)
    capture(campaign, "failure", BASE)
    capture(baseline, "failure", BASE)
    capture(refusal, "ordinary-refusal", BASE)
    completed = capture(later, "permanent-award-title", FIXED)
    assert completed["natural_process_exit"]
    reboot = capture(cold, "cold-collection-loaded", FIXED)
    assert opening["guest_writes"] == reboot["guest_writes"] == []
    assert sha(entry / "new-campaign.State") == sha(campaign / "campaign.State")
    assert sha(campaign / "campaign-stage-11.State") == sha(baseline / "campaign.State") == sha(later / "campaign.State")
    assert sha(baseline / "idle-sample.State") == sha(refusal / "ordinary-clear-title.State")
    for name in ("postvictory", "new-campaign"):
        iw = (entry / (name + "-IWRAM.bin")).read_bytes()
        assert iw[0x2328:0x232A] == bytes([16, 0])
    entry_trace = (entry / "trace.txt").read_text().splitlines()
    assert any("config-write prior=0000 incoming=00000010 pc=08DB3520" in row for row in entry_trace)
    battles = []
    for row in (campaign / "promotion-trace.txt").read_text().splitlines():
        if match := re.match(r"(\d+) mode=7 stage=(\d+) flags=(\d+) progression=(\d+)$", row):
            battles.append([int(match[1]), int(match[2]), int(match[3]), int(match[4])])
    assert battles[0][3] == 0 and battles[-1][1] == 11
    assert set(x[3] for x in battles) == set(range(11))
    assert all(x[2] & 16 for x in battles)
    prior = (baseline / "promotion-trace.txt").read_text()
    refusal_rows = (refusal / "trace.txt").read_text().splitlines()
    assert any("event-comparison R0=00000005 R1=00000000" in s for s in refusal_rows)
    assert any("guard-reject R0=00000005 R1=00000000" in s for s in refusal_rows)
    log = (later / "promotion-trace.txt").read_text().splitlines()
    for text in ("212178 real-P1-hit P2-before=1 after=0", "212178 root5", "212179 terminal-entry", "212446 terminal-middle"):
        assert text in prior and text in log
    assert "terminal-final" not in prior and "213625 terminal-final" in log
    assert any("guard-hidden event=5 auxKind=0326 R0=00000020 queue=1" in s for s in log)
    src_rom = (baseline / "loaded-rom.bin").read_bytes()
    mod_rom = (later / "loaded-rom.bin").read_bytes()
    assert len(src_rom) == len(mod_rom) and src_rom[:0x6FFBE4] == mod_rom[:0x6FFBE4] and src_rom[0x6FFBF0:] == mod_rom[0x6FFBF0:]
    assert struct.unpack_from("<4I", mod_rom, 0x6FFBE4) == (0xE1D600B4, 0xE2000020, 0xE3500020, 0x1A000051)
    state = {}
    for row in log:
        if match := re.match(r"(\d+) ([\w-]+) pending=([\dA-F]{2}) permanent=([\dA-F]{2}) saved=([\dA-F]{2}) R0=([\dA-F]{8})", row):
            state[match[2]] = [int(match[1]), *[int(match[k], 16) for k in range(3, 7)]]
    before = state["pending-probe"]
    accept = state["selected-mask-commit"]
    gain = state["after-permanent-commit"]
    retire = state["record-or"]
    assert before[1] & 16 and before[2] & 16 == 0
    assert accept[4] & 0x1000 and gain[2] & 16
    assert retire[1] & 16 == 0 and retire[2] & 16
    assert before[0] <= accept[0] <= gain[0] <= retire[0] <= state["name-accepted"][0] <= state["ff-bypass"][0]
    assert any("address=03002329" in row and "pc=085B1120" in row for row in log)
    assert any("address=03002328" in row and "pc=080BF6C0" in row for row in log)
    award_iw = (later / "permanent-award-IWRAM.bin").read_bytes()
    queued_count = struct.unpack_from("<H", award_iw, 0x3CF4)[0]
    assert 1 <= queued_count <= 2
    roster_ids = list(struct.unpack_from(f"<{queued_count}H", award_iw, 0x3CF0))
    assert 11 in roster_ids
    assists = (campaign / "assist-ledger.txt").read_text().splitlines() + (later / "assist-ledger.txt").read_text().splitlines()
    score, bosses = 0, []
    for row in assists:
        fields = dict(field.split("=", 1) for field in row.split())
        assert fields["bytes"] == "2" and fields["verified"] == "true"
        addr = int(fields["address"], 16)
        if fields["kind"] == "score":
            assert addr == int(fields["FIRST"], 16) + 0x66 and fields["requested"] == "999"
            score += 1
        else:
            assert fields["kind"] == "boss" and fields["requested"] == "1" and addr == int(fields["SECOND"], 16) + 0x64
            bosses.append(int(fields["stage"]))
    assert score > 0 and bosses == [7, 11]
    raw_path = later / "data/104/probe.SaveRAM"
    assert sha(raw_path) == reboot["copied_genuine_completion_save"] == sha(cold / "data/104/probe.SaveRAM")
    raw = raw_path.read_bytes()
    logical = b"".join(raw[i:i + 8][::-1] for i in range(0, 216, 8))
    assert logical[18] & 16 and struct.unpack_from("<I", logical, 192)[0] == sum(logical[:192])
    assert logical[208:216] == b"BS15M23\x01"
    for iw in [(later / "permanent-title-IWRAM.bin").read_bytes(), (cold / "cold-iwram.bin").read_bytes()]:
        assert iw[0x2329] & 16 and not iw[0x2328] & 16
        assert iw[0x1120:0x11E4] == logical[:196]
    cold_start, cold_menu = map(int, (cold / "frames.txt").read_text().split())
    assert cold_start <= 2 and cold_menu > cold_start
    return dict(status="PASS", rom=FIXED, original=BASE, entry_launch=sha(entry / "launch.json"), campaign_launch=sha(campaign / "launch.json"),
                original_terminal_launch=sha(baseline / "launch.json"), real_guard_refusal=sha(refusal / "launch.json"), repaired_terminal_launch=sha(later / "launch.json"),
                cold_launch=sha(cold / "launch.json"), award_frame=retire[0], progress_records=battles,
                normal_score_writes=score, boss_hp_adjustments=bosses, awarded_roster_ids=roster_ids,
                saved_record_byte_18=logical[18], eeprom=sha(raw_path), fresh_core=cold_start, fresh_collection_menu=cold_menu)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("entry", "campaign", "baseline", "refusal", "later", "cold", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = verify(args.entry, args.campaign, args.baseline, args.refusal, args.later, args.cold)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS", sha(args.report))
