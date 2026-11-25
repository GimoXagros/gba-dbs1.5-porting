"""Join controller-only single-player and cold save evidence for the release review."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
CANDIDATE = "AA6BB1EB93027464F842D6EB0CC69A68959F26B38460FAF1B0C63BDD5FFA4BB1"
V94 = "EF8BBC67DB243A8CCAFA25744EFB371CC097C323F45D25060419B33B577B75BA"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ROSTER = "AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D"
MIXED_SAVE = "4925052F85A6542074C03F5375D7BC6129C346EE84ABF9029A67D78F5E6A57C8"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_report(name, trace="events.txt"):
    folder = BUILD / name
    path = folder / "report.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data["exact_rom"] and data["visible"] is False and data["guest_writes"] == [], name)
    require(digest(folder / "loaded.bin") == data["rom"], f"{name} loaded ROM")
    require(digest(folder / "controller.lua") == data.get("controller", data.get("script")), f"{name} controller")
    require(digest(folder / trace) == data.get("events", data.get("trace")), f"{name} trace")
    if trace == "events.txt":
        require(data["result"] == "PASS", name)
    return data, (folder / trace).read_text(encoding="utf-8"), {"folder": name, "rom": data["rom"], "report_sha256": digest(path)}


def frame(text, pattern):
    match = re.search(r"^(\d+) " + pattern, text, re.MULTILINE)
    require(match is not None, pattern)
    return int(match[1])


def characters():
    variants = ["b", "b", "d", "d", "b", "b", "d", "d", "b", "b", "b", "c", "a", "a", "c"]
    proofs, sounds = [], {}
    for player, version in enumerate(variants):
        data, text, proof = load_report(f"flow-release-fighter-{player}-{version}")
        require(data["rom"] == (CANDIDATE if version in ("c", "d") else V94), str(player))
        require(data["source_save"] == data["final_save"] == ROSTER and data["player"] == player, str(player))
        roster_order = [*range(11), 13, 14, 11, 12]
        stages = [frame(text, f"selected {roster_order.index(player)} id {player}$"),
                  frame(text, r"mode 6 stage"), frame(text, r"mode 7 stage"),
                  frame(text, "player resource group 0"), frame(text, f"player active {player} "),
                  frame(text, "result damage"), frame(text, "next VS")]
        require(stages == sorted(stages), f"selection to return {player}")
        proof.update(player=player, frames=stages)
        if player >= 11:
            events = re.findall(r"^\d+ evolved event (\d+) at (-?\d+),(-?\d+)", text, re.MULTILINE)
            end = frame(text, "ordinary devolution")
            first = frame(text, "player resource group 1")
            require(frame(text, "collectible at") < first <= frame(text, f"evolution music selector {player}") < end < stages[-2],
                    f"Calumon and devolution {player}")
            require(len({e[0] for e in events}) >= 3 and len({e[1:] for e in events}) > 1
                    and f"{end} player resource group 0" in text.splitlines(),
                    f"evolved actions and reloaded base {player}")
            require(re.search(r"attack-input frames [1-9]\d*", text), f"evolved attacks {player}")
            proof.update(evolved_frames=[first, end], events=[int(e[0]) for e in events])
        if player in (11, 14):
            for at, cue, caller, own, own_event, enemy, enemy_event in re.findall(
                    r"^(\d+) accepted sound ([\dA-F]+) caller=([\dA-F]+) player=(\d+) event=(\d+) enemy=(\d+) event=(\d+)", text, re.MULTILINE):
                sounds.setdefault(cue, []).append([player, int(at), caller, int(own), int(own_event), int(enemy), int(enemy_event)])
        proofs.append(proof)
    require(set(sounds) == {"5F", "60", "61", "62", "63"}, "five real sound admissions")
    return proofs, sounds


def archived_owners(candidate):
    rom = candidate.read_bytes()
    result = {}
    for capture, owners in [
        ("bizhawk-roster-name-v91-20261124-c", ["ending-roster", "tag-release/id12"]),
        ("final-cold-campaign-20261124", ["collection-native/viewer", "collection-native/storage"]),
        ("bizhawk-vs-record-f824-20261124", ["collection-native/vs", "collection-native/stats"]),
    ]:
        path = BUILD / capture / "loaded-rom.bin"
        previous = path.read_bytes()
        for owner in owners:
            manifest = BUILD / "v94-original-a/intermediate" / owner / "manifest.json"
            writes = json.loads(manifest.read_text(encoding="utf-8"))["writes"]
            for item in writes:
                offset, size = (item["offset"], item["size"]) if isinstance(item, dict) else item
                require(0 <= offset < offset + size <= min(len(rom), len(previous))
                        and rom[offset:offset + size] == previous[offset:offset + size], owner)
            result[owner] = {"writes_checked": len(writes), "capture": capture,
                             "loaded_sha256": digest(path), "manifest_sha256": digest(manifest)}
    return result


def verify(candidate):
    require(digest(candidate) == CANDIDATE, "unreviewed candidate")
    fighters, sounds = characters()
    win, success, wp = load_report("flow-release-shoot-win-a", "collection-trace.txt")
    loss, defeat, lp = load_report("flow-release-shoot-loss-a", "collection-trace.txt")
    require(win["rom"] == loss["rom"] == CANDIDATE and win["seven_round_win"] and loss["actual_defeat"]
            and win["save_out"] == loss["save_in"] == loss["save_out"] and loss["state"] is None, "Shoot cold chain")
    turns = [len(re.findall(rf"round={i} turn=", success)) for i in range(7)]
    require(turns == [2, 2, 5, 5, 7, 9, 3], "rounds")
    for trace, markers in [(success, ["mode=4", "scene-playing", "final-round-cleared", "completion-save", "success-exit"]),
                           (defeat, ["mode=4", "scene-playing", "failure-exit"])]:
        order = [frame(trace, mark) for mark in markers] + [frame(trace, "mode=20"), int(trace.splitlines()[-1].split()[0])]
        require(order == sorted(order) and trace.splitlines()[-1].endswith("mode=3"), "Shoot round trip")

    train, original, tp = load_report("flow-release-source-train-a")
    require(train["rom"] == WSC and "init pc=68f7:2508" in original and "update pc=68f7:195d" in original
            and "result init=1 update=9376 shake=0" in original, "original Train observation")
    data, record, rp = load_report("flow-release-mixed-stats-c")
    require(data["rom"] == CANDIDATE and data["source_save"] == MIXED_SAVE, "record provenance")
    rows = [(int(i), int(w), int(p)) for i,w,p in re.findall(r"^\d+ row (\d+) (\d+) (\d+)$", record, re.MULTILINE)]
    require(len(rows) == 15 and sorted(rows) == [(0,3,6), *[(i,0,0) for i in range(1,15)]], "all displayed match values")
    require(frame(record, "exit 1 mode 20") < frame(record, "entry 2") < frame(record, "pressed A") <
            frame(record, "exit 2 mode 20") < frame(record, "title after cancellation"), "record return and cancel")
    evidence = []
    previous = None
    for name in ["v94-final-assist-campaign", "v94-final-post-ending-restart"]:
        folder = BUILD / name
        path = folder / "report.json"
        r = json.loads(path.read_text(encoding="utf-8"))
        require(r["outcome"] == "PASS" and r["rom"] == digest(folder / "loaded-rom.bin") == V94
                and r["trace"] == digest(folder / "play.txt") and r["visible"] is False and r["guest_writes"] == [], name)
        if previous:
            require(previous["save_out"] == r["save_in"] == r["save_out"], "campaign -> cold save")
        else:
            trace = (folder/"play.txt").read_text()
            require(frame(trace, "real hit 7") < frame(trace, "real hit 11") < frame(trace, "ending")
                    < frame(trace, "campaign sampled 72010 native score writes 27"), "assisted campaign")
        previous = r
        evidence.append({"folder":name, "report_sha256":digest(path)})
    return {"candidate": CANDIDATE, "fighters": fighters, "sound_requests": sounds,
            "collection_shoot": {"win": wp, "loss": lp, "turns_per_round": turns, "save":win["save_out"]},
            "original_train": tp, "mixed_record_display": {**rp,"rows":rows,"physical_eeprom":MIXED_SAVE},
            "assisted_campaign": evidence, "archived_owner_ranges": archived_owners(candidate)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

