"""Check source roster gates, native capacity, portrait indices and saved award masks."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_mode22_stats_bridge import Device, encode_snapshot
from verify_mode23_completion_save import CONFIG, BUFFER, Machine, dump


class RosterDevice(Device):
    def __init__(self, image, record, scan, **kwargs):
        super().__init__(image, record, **kwargs)
        self.scan = scan

    def run(self, start, stops, max_steps=22000):
        while True:
            pc = super().run(start, set(stops) | {self.scan}, max_steps)
            if pc in stops:
                return pc
            assert self.get(pc) == 0xE0D320B2  # LDRH R2,[R3],#2
            self.r[2] = self.get(self.r[3], 2)
            self.r[3] += 2
            start = pc + 4


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def eligibility(image, symbols):
    offset = symbols["roster_clear_tags"] - 0x08000000
    scan = image.index(struct.pack("<I",0xE0D320B2),offset,offset+128) + 0x08000000
    testcases = [(k, v, p, c) for k in range(11) for v in (0, 1, 65535) for p in (0, 16, 32, 48) for c in (0, 1)]
    for index, value, permanent, continued in testcases:
        data = bytearray(42)
        struct.pack_into("<H", data, 0x12 + index * 2, value)
        m = RosterDevice(image, encode_snapshot(data), scan)
        m.put(CONFIG + 0x18, 2, 1)
        m.put(CONFIG + 0x19, permanent, 1)
        m.put(CONFIG + 0x1A, continued, 2)
        m.put(CONFIG + 0x20, 0x20, 1)
        m.put(CONFIG + 0x22, 999, 2)
        regs = m.r[:]
        stops = {0x0808B368}
        pc = m.drive(0x0808B364, stops)
        assert pc in stops and m.r[:14] == regs[:14]
        tags = (0x30 if index >= 8 else 0x10 if index >= 4 else 0) if value and not continued else 0
        assert m.get(CONFIG+0x18,1) == (2 | (tags & ~permanent)) and m.get(CONFIG+0x19,1) == permanent
        written = [block for direction, block in m.events if direction == "write"]
        assert written == list(range(25)) * tags.bit_count()
        if tags:
            assert int.from_bytes(m.blocks[0x12:0x14], "little") == permanent
            assert sum(m.blocks[:192]) == int.from_bytes(m.blocks[192:196], "little")
        assert m.blocks[216:272] == encode_snapshot(data)
    for corruption in ("blank", "crc", "io"):
        data = bytearray(42)
        data[0x22] = 1
        record = bytearray(encode_snapshot(data))
        faults = []
        if corruption == "blank": record[:] = b"\xff" * 56
        elif corruption == "crc": record[-1] ^= 1
        else: faults = [("read", 30, 1)]
        m = RosterDevice(image, record, scan, faults=faults)
        m.drive(0x0808B364, {0x0808B368})
        assert m.get(CONFIG+0x18,1) == 0 and not any(direction == "write" for direction, _ in m.events)
    return len(testcases) + 3


def queue(image):
    count = 0
    for initial in range(256):
        for perm in (0, 16, 32, 48, 255):
            for occupied in range(3):
                m = Machine(image, seed=occupied, flags=31)
                m.r[1] = CONFIG
                m.put(CONFIG+0x18, initial, 1)
                m.put(CONFIG+0x19, perm, 1)
                m.put(0x03003CF0, 0xBBBB, 2)
                m.put(0x03003CF2, 0xCCCC, 2)
                m.put(0x03003CF4, occupied, 2)
                m.put(0x03003CF6, 0xDDDD, 2)
                m.put(BUFFER+0x12, perm, 2)
                gate = m.run(0x080BF4C0, {0x080BF91C, 0x080BF6D4})
                filtered = initial & 0x30
                candidates = filtered & ~perm
                accepted = [(11, 16), (12, 32)]
                selected = [(i,b) for i,b in accepted if b & candidates][:2-occupied]
                expected = [0xBBBB, 0xCCCC]
                for pos, (roster_id, _) in enumerate(selected, occupied): expected[pos] = roster_id
                mask = sum(b for _,b in selected)
                assert gate == (0x080BF6D4 if candidates else 0x080BF91C)
                assert [m.get(0x03003CF0+j*2,2) for j in range(2)] == expected
                assert m.get(0x03003CF4,2) == occupied + len(selected) and m.get(0x03003CF6,2) == 0xDDDD
                assert (m.get(CONFIG+0x18,1), m.get(CONFIG+0x19,1), m.get(BUFFER+0x12,2)) == (filtered & ~mask, perm | mask, perm | mask)
                count += 1
    for roster_id in (11,12):
        for slot in (0,1):
            m = Machine(image, seed=slot, flags=31)
            m.r[0] = slot
            m.put(0x03003CF0 + slot*2, roster_id, 2)
            assert m.run(0x080BF710, {0x080BF754}) == 0x080BF754
            record = 0x084A80F8 + roster_id*32
            assert m.r[5] == record and (m.r[2],m.r[3]) == ((0xA4,0) if slot == 0 else (0xEC,1))
            assert all(0x08000000 <= m.get(record+i) < 0x09000000 for i in (0,4,8))
    return count


def verify(source, native, installed, owner):
    src, image, old = source.read_bytes(), installed.read_bytes(), native.read_bytes()
    parent = json.loads(owner.read_bytes())
    assert sha(src) == "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
    assert sha(old) == parent["input_sha256"] and sha(image) == parent["output_sha256"]
    assert src[0x77A155:0x77A15D] == bytes.fromhex("8A47182430884718")
    assert src[0x77A193:0x77A197] == bytes.fromhex("A820741E")
    assert b"\xC7\x05\x0C\x00" in src[0x77A19F:0x77A1B0]
    inverse = bytearray(image)
    for row in parent["writes"]:
        i, n = row["offset"], row["size"]
        assert sha(old[i:i+n]) == row["before_sha256"] and sha(image[i:i+n]) == row["after_sha256"]
        inverse[i:i+n] = old[i:i+n]
    assert inverse == old
    return dict(status="PASS", image=sha(image), eligibility=eligibility(image,parent["symbols"]),
                queue=queue(image), portrait_slot_cases=4, whole_image_inverse=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("source","native","installed","owner","report"): p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    result=verify(a.source,a.native,a.installed,a.owner)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8",newline="\n")
    print(result,sha(a.report.read_bytes()))
