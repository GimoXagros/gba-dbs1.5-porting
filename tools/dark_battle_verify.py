"""Independent CPU checks of the original D-Project validator and the port's retry gate.

Install Unicorn 2.1.4 for these isolated function tests. They never drive an
emulator's link port. Add --dp-bytes/--bs-bytes to check an observed two-core
wire transcript against the native HP and five-turn rules.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_16, UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R6, UC_ARM_REG_R10
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_EFLAGS, UC_X86_REG_SP

BASE = 0x08000000
CTX = 0x02010018


def words(bs_pattern, dp_winners):
    reply = [0xc20f | bs_pattern << 4, 0x058f, 0x080f | (31 ^ dp_winners) << 4]
    total = sum((v >> n) & 15 for v in reply for n in (4, 8, 12))
    return (*reply, 15 | ((-total) & 15) << 12)


class ProjectValidator:
    def __init__(self, data):
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_16)
        self.cpu.mem_map(0, 0x30000)
        self.cpu.mem_write(0x20000, bytes(data[0x320000:0x330000]))
        self.cpu.reg_write(UC_X86_REG_CS, 0x2000)
        self.cpu.mem_write(0x1f71, bytes([3]))

    def accepts(self, reply):
        c = self.cpu
        c.mem_write(0x1f7e, struct.pack('<4H', *reply))
        c.mem_write(0x1f96, bytes(1))
        for at in (0, 2, 4, 6):
            c.mem_write(0x1f75, bytes([at]))
            c.reg_write(UC_X86_REG_SP, 0x7000)
            c.mem_write(0x7000, struct.pack('<H', 0x6000))
            c.emu_start(0x27bea, 0x26000, count=140)
            if c.reg_read(UC_X86_REG_EFLAGS) & 1:
                assert c.mem_read(0x1f96, 1)[0] & 8
                return False
        return True


def branch_target(data, at):
    op = struct.unpack_from('<I', data, at)[0]
    assert op & 0x0f000000 == 0x0a000000
    relative = op & 0xffffff
    if relative & 0x800000:
        relative -= 0x1000000
    return BASE + at + 8 + relative*4


class PortGate:
    def __init__(self, data):
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.cpu.mem_map(BASE, len(data))
        self.cpu.mem_write(BASE, bytes(data))
        self.cpu.mem_map(0x02000000, 0x40000)
        at = data.index(bytes.fromhex('b804cae1 080054e3'), 0x900000) + 4
        self.start = BASE + at
        self.no_battle = branch_target(data, at + 4)
        self.battle = branch_target(data, at + 56)
        assert self.battle != self.no_battle
        self.stop = None
        for addr in (self.no_battle, self.battle):
            self.cpu.hook_add(UC_HOOK_CODE, self.stop_at, begin=addr, end=addr)

    def stop_at(self, cpu, address, size, data):
        self.stop = address
        cpu.emu_stop()

    def accepts(self, request, reply):
        c = self.cpu
        self.stop = None
        c.mem_write(CTX+0x50, struct.pack('<H',request))
        c.mem_write(CTX+0x58, bytes([8, 99]))
        c.mem_write(CTX+0x48, bytes([177, 1]))
        c.reg_write(UC_ARM_REG_R10, CTX)
        c.reg_write(UC_ARM_REG_R4, 8)
        c.reg_write(UC_ARM_REG_R6, reply[3] >> 8)
        c.emu_start(self.start, 0, count=50)
        assert self.stop in (self.battle,self.no_battle)
        if self.stop == self.no_battle:
            assert bytes(c.mem_read(CTX+0x58, 2)) == bytes(2)
            assert bytes(c.mem_read(CTX+0x48, 2)) == bytes(2)
        return self.stop == self.battle


def stats(word, table, bonus):
    row = (word >> 8 & 15) * 4
    return table[row]+bonus[0], table[row+1+(word>>12 & 3)]+bonus[1]


def transcript(dp_bytes, bs_bytes, project, battle, validator):
    incoming, outgoing = (struct.unpack('<4H', bytes.fromhex(s)) for s in (dp_bytes,bs_bytes))
    dp_turns = incoming[2] >> 4 & 31
    assert outgoing == words(outgoing[0] >> 4 & 31, dp_turns), 'Battle Spirit response words'
    accepted = validator.accepts(outgoing)
    if not accepted:
        return dict(accepted=False, reason='D-Project type-3 checksum')
    wsc_table = battle[0x751494:0x751494+96]
    dp_table = project[0x3270c0:0x327100]
    assert wsc_table[:64] == dp_table
    bonus = (incoming[2] >> 12) * 2
    player_hp, player_attack = stats(outgoing[1], wsc_table, (0,0))
    remote_hp, remote_attack = stats(incoming[1],wsc_table,wsc_table[64+bonus:66+bonus])
    dp_hp, dp_attack = stats(incoming[1],dp_table,(0,0))
    opponent_hp, opponent_attack = stats(outgoing[1],dp_table,(0,0))
    history = []
    for tick in range(256):
        bit = 1 << (tick % 5)
        if dp_turns & bit:
            player_hp -= remote_attack + bool(incoming[0] >> 4 & bit)
        else:
            remote_hp -= player_attack + bool(outgoing[0] >> 4 & bit)
        if dp_turns & bit:
            opponent_hp -= dp_attack + bool(incoming[0] >> 4 & bit)
        else:
            dp_hp -= opponent_attack + bool(outgoing[0] >> 4 & bit)
        assert (player_hp,remote_hp) == (opponent_hp,dp_hp), 'HP disagreement between source cartridges'
        history.append([player_hp, remote_hp])
        if min(history[-1]) <= 0:
            return dict(accepted=True, battle_spirit_won=remote_hp<=0, hitpoint_history=history)
    raise ValueError('Neither source combatant reached its result')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('gba','wsc','jp','kr'):
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--trace-json',type=Path,help='Actual two-core GBA/D-Project trace and read-only HP history')
    p.add_argument('--dp-bytes')
    p.add_argument('--bs-bytes')
    a=p.parse_args()
    gba,ws,jp,kr=(getattr(a,n).read_bytes() for n in ('gba','wsc','jp','kr'))
    for start,end in [(0x326b9f,0x326ed5),(0x326f02,0x327100),(0x327a48,0x327cf0),(0x3cd00b,0x3cd2f3)]:
        assert jp[start:end] == kr[start:end], 'Translated cartridge changes a protocol/result routine'
    assert jp[0x3270c0:0x327100] == ws[0x751494:0x7514d4]
    gate, dp = PortGate(gba), ProjectValidator(jp)
    counts=[0,0]
    for special in ws[0x751484:0x751494]:
        for winners in range(32):
            reply=words(special,winners)
            approved=dp.accepts(reply)
            assert approved == gate.accepts(0x020f,reply)
            assert approved == (reply[3] != 15)
            counts[int(approved)] += 1
    # The same installed context can immediately accept a valid retry after rejection.
    edge = next(words(0,w) for w in range(32) if words(0,w)[3]==15)
    ok = next(words(0,w) for w in range(32) if words(0,w)[3]!=15)
    assert not gate.accepts(0x020f,edge) and gate.accepts(0x020f,ok)
    assert not gate.accepts(0,ok) and not gate.accepts(0x0e0f,ok)
    result=dict(gba_sha256=hashlib.sha256(gba).hexdigest(),source_cases=sum(counts),
                checksum_retry=counts[0],accepted=counts[1],context_retry=True)
    if a.trace_json:
        trace=json.loads(a.trace_json.read_text(encoding='utf-8-sig'))
        assert trace['gba_sha256'] == result['gba_sha256']
        peer = jp if hashlib.sha256(jp).hexdigest()==trace['dproject_sha256'] else kr
        assert hashlib.sha256(peer).hexdigest()==trace['dproject_sha256']
        assert trace['gba_overruns']==trace['wsc_uart']['overrun']==0
        assert trace['completed_gba_bytes']==trace['completed_wsc_bytes']==8
        def stream(owner):
            return bytes(row[2] for row in trace['trace'] if row[1]==owner).hex()
        observed=transcript(stream('WSC'),stream('GBA'),peer,ws,ProjectValidator(peer))
        assert observed['accepted']
        history = observed['hitpoint_history']
        signed = lambda v: (v+128)%256-128
        assert history == [[signed(x) for x in row[1:]] for row in trace['gba_hp'][1:]]
        assert history == [[signed(x) for x in reversed(row[1:])] for row in trace['dproject_hp'][1:]]
        assert (trace['gba_result'],trace['dproject_result']) == (
            ('win','loss') if observed['battle_spirit_won'] else ('loss','win'))
        assert trace['returned_to_title'] and trace['dproject_returned']
        result['observed'] = observed
    if a.dp_bytes or a.bs_bytes:
        if not (a.dp_bytes and a.bs_bytes):
            p.error('Both observed eight-byte streams are required')
        result['observed']=transcript(a.dp_bytes,a.bs_bytes,jp,ws,dp)
    print(json.dumps(result))

if __name__=='__main__':
    main()
