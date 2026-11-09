#!/usr/bin/env python3
"""Positive SECOND kind gate and separate introduction-task reload ownership."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from analyze_shoot_terminal_bx import exact, need, SOURCE
from analyze_shoot_opponent_controls import (
    contracts as control_contracts, callback_graph, borrowed_graph,
    imported_effects, kind3_damage,
    Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM, CS_OP_MEM,
)
from analyze_shoot_rule_callback_graph import verified_indirect_dispatches

INTRO = 0x76B4A0
ROOT = Path(__file__).resolve().parents[1]


def composition(s):
    # Reuse the source-checked43-callback artifact instead of another graph walker.
    path = ROOT/'build/shoot-rule-graph-v2.json'
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest().upper() ==
         '37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281',
         'frozen lower graph artifact; regenerate with analyze_shoot_rule_callback_graph.py')
    lower = json.loads(raw)
    need(len(lower['callback_entries']) == 43 and
         lower['reachable_instruction_starts'] == 2051, 'complete retained lower graph')
    tables = verified_indirect_dispatches(s[0x740900:0x750900])
    need(all(0x2E74 not in x['targets'] for x in tables.values()) and
         0x2E74 not in lower['callback_entries'], 'no2E74 bounded indirect/callback target')
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    kind_writes = []
    for span in lower['reachable_ranges']:
        lo, hi = 0x740900+span['start'], 0x740900+span['end']
        need(hashlib.sha256(s[lo:hi]).hexdigest().upper() == span['sha256'].upper(),
             'lower graph live source bytes')
        for i in decoder.disasm(s[lo:hi], lo):
            if i.operands and i.operands[0].type == CS_OP_MEM and \
                    i.operands[0].access & 2 and i.operands[0].mem.disp == 4:
                if i.address == 0x7420BC:
                    continue  # Existing allocator writes the newly selected child slot.
                need(i.operands[1].type == CS_OP_IMM and
                     i.mnemonic in ('and', 'or', 'xor'), 'typed lower actor flag store')
                value = i.operands[1].imm
                need((3 & value if i.mnemonic == 'and' else
                      3 | value if i.mnemonic == 'or' else 3 ^ value) & 15 == 3,
                     'lower callbacks preserve lowkind3')
                kind_writes.append(f'{i.address:06X}')
    expected_imports = {0xBA4, 0xBC7, 0x19A8, 0x19BF, 0x1BD9,
                        0x1CB5, 0x23F4, 0x24CB, 0x26CB, 0x2862}
    need({(x['segment'], x['offset']) for x in lower['imports']} ==
         {(0x4FFF, x) for x in expected_imports}, 'exact typed lower imports')
    exact(s, 0x742093, ['push 0x4090', 'push 0x1899', 'push ds',
        'push di', 'lcall 0x4fff, 0xbc7'])
    exact(s, 0x742156, ['push 0x4090', 'push 0x1bc4', 'push 0xc00',
        'push word ptr es:[di]', 'lcall 0x4fff, 0xbc7'])
    for at in (0x74912D, 0x749C52):
        exact(s, at, ['push 0', 'push 1', 'push 0x4104', 'push 0',
            'push 0', 'push 0x1000', 'push 0x724', 'lcall 0x4090, 0x172a'])
    # The borrowed cross-overlay callback changes the linked auxiliary, not SECOND.
    exact(s, 0x762D71, ['mov bx, word ptr [si + 0x1c]',
        'mov word ptr [bx], 0x2a7', 'mov word ptr [bx + 2], 0x8653'])
    exact(s, 0x7867D7, ['mov word ptr [si + 0x80], 0xe1',
        'mov word ptr [si + 4], 0x9305', 'mov word ptr [si], 0xc9',
        'mov word ptr [si + 2], 0x8653', 'retf'])
    for i in decoder.disasm(s[0x7865F9:0x7866B4], 0x7865F9):
        if i.operands and i.operands[0].type == CS_OP_MEM and i.operands[0].access & 2:
            need(i.reg_name(i.operands[0].mem.base) == 'si',
                 'auxiliary continuation writes only its own actor')
        if i.mnemonic == 'lcall':
            need(i.op_str in ('0x86bf, 0', '0x4090, 0x4ba9', '0x4fff, 0x2862'),
                 'auxiliary typed visual/release/presentation imports')
    exact(s, 0x7454B7, ['push ds', 'push si', 'lcall 0x4090, 0x181e'])
    effects, damage = imported_effects(s), kind3_damage(s)
    pointer = bytes.fromhex('742E9040')
    hits = [at for at in range(len(s)-3) if s.startswith(pointer, at)]
    need(hits == [0x74374E, 0x747D0D, 0x767504, 0x7676D2, 0x76BC63] and
         all(s[at-1] == 0x9A for at in hits), 'all encoded2E74 far references are five calls')
    for at, target in ((0x769E34, 0x769E64), (0x7731E2, 0x773212),
                       (0x78712A, 0x78715A)):
        exact(s, at, [f'je 0x{target:x}'])
    return dict(lower_instructions=2051, lower_callbacks=43,
        lower_kind_preserving_stores=kind_writes,
        lower_imports=[f'4FFF:{x:04X}' for x in sorted(expected_imports)],
        scheduler_callback_arguments=['4090:1899 new allocated actor wrapper',
                                      '4090:1BC4 released actor cleanup'],
        new_actor_flags='4104; new handle0724; never retags existing SECOND',
        borrowed_auxiliary='762D71 links via SECOND+1C;8653:02A7 retags only auxiliary kind5',
        imported_effects=effects, kind3_damage=damage,
        encoded_far_2E74_references=[f'{at:06X}' for at in hits],
        bounded_post197A_no_side1_companion_reload=True,
        resident_93E7_extension_supported=True,
        condition='Retained normal43lower/775upper/790borrowed graph and normal exclusive scene/task ownership.',
        external_gate='749824/4090:8F24 spatial dispatch outside existing bounded source domain can reach0A80/EB4C/E59A; global external-entry gate remains open.')


def intro_graph(source, seed):
    """Follow literal task continuations and literal child callback arguments."""
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    queue, seen, callbacks, children, imports = deque([INTRO+seed]), set(), set(), set(), set()
    while queue:
        at = queue.popleft()
        while at not in seen:
            need(INTRO <= at < INTRO+0x2400, 'bounded introduction code')
            i = next(decoder.disasm(source[at:at+15], at, 1), None)
            need(i is not None, 'complete introduction instruction')
            seen.add(at)
            seq = list(decoder.disasm(source[at:at+13], at))
            if i.mnemonic == 'mov' and i.op_str.startswith('ax, 0x') and len(seq) >= 4 and \
                    [(j.mnemonic, j.op_str) for j in seq[1:4]] == [
                        ('mov', 'word ptr [bx], ax'), ('mov', 'ax, 0x6b4a'),
                        ('mov', 'word ptr [bx + 2], ax')]:
                exact(source, at-12, ['push bx', 'push ds', 'mov ax, 0xc00',
                    'mov ds, ax', 'mov ax, word ptr [8]', 'mov bx, ax'])
                target = i.operands[1].imm
                callbacks.add(target)
                queue.append(INTRO+target)
            if i.mnemonic == 'push' and i.op_str == '0x6b4a':
                j = seq[1]
                need(j.mnemonic == 'push' and j.operands[0].type == CS_OP_IMM,
                     'literal introduction child callback')
                children.add(j.operands[0].imm)
                queue.append(INTRO+j.operands[0].imm)
            if i.mnemonic == 'lcall':
                need(len(i.operands) == 2 and all(o.type == CS_OP_IMM for o in i.operands),
                     'typed introduction far import')
                imports.add(tuple(o.imm for o in i.operands))
            elif i.mnemonic == 'call' or i.mnemonic.startswith(('j', 'loop')):
                need(len(i.operands) == 1 and i.operands[0].type == CS_OP_IMM,
                     'direct introduction branch')
                queue.append(i.operands[0].imm)
                if i.mnemonic == 'jmp':
                    break
            if i.mnemonic in ('ret', 'retf', 'iret'):
                break
            at += i.size
    return dict(seed=f'6B4A:{seed:04X}', instructions=len(seen),
        callbacks=[f'{x:04X}' for x in sorted(callbacks)],
        allocated_child_callbacks=[f'{x:04X}' for x in sorted(children)],
        direct_2E74=(0x4090, 0x2E74) in imports,
        reload_76BC62_reachable=0x76BC62 in seen,
        imports=[f'{s:04X}:{o:04X}' for s,o in sorted(imports)],
        current_task_self_free_76B8BA=0x76B8BA in seen,
        current_task_self_free_76C237=0x76C237 in seen)


def proof(s):
    control_contracts(s)
    exact(s, 0x74356F, ['test word ptr [si + 8], 0x4000', 'je 0x7435b0',
        'dec word ptr [si + 0x56]', 'jns 0x7435d4'])
    exact(s, 0x7435A4, ['mov word ptr [si], 0xc6f',
        'mov word ptr [si + 2], 0x668e'])
    exact(s, 0x747B1F, ['mov ax, word ptr [si + 0x50]', 'shr ax, 1',
        'mov word ptr [si + 0x54], ax', 'shr ax, 1', 'mov word ptr [si + 0x56], ax'])
    exact(s, 0x747B63, ['mov word ptr [si], 0x7792',
        'mov word ptr [si + 2], 0x4090'])
    exact(s, 0x76B4AC, ['test word ptr es:[0x68], 0x10', 'je 0x76b4c9',
        'push 0xef0', 'push 0x6b4a', 'push 0x423', 'lcall 0x4fff, 0x980'])
    exact(s, 0x76B4C9, ['cmp word ptr es:[0x3d0], 2', 'jne 0x76b502',
        'test word ptr es:[0x68], 0x200', 'je 0x76b4ee'])
    exact(s, 0x76B4EE, ['push 0xef0', 'push 0x6b4a', 'push 0xdaa',
        'lcall 0x4fff, 0x980'])
    exact(s, 0x76B880, ['push 0x4090', 'push 0x7fa', 'push 0xc00',
        'push word ptr es:[0x3de]', 'lcall 0x4fff, 0xbc7', 'add sp, 8',
        'push 0x4090', 'push 0xd0b', 'push 0xc00',
        'push word ptr es:[0x3e0]', 'lcall 0x4fff, 0xbc7', 'add sp, 8',
        'push ds', 'mov ax, 0xc00', 'mov ds, ax', 'mov ax, word ptr [8]',
        'pop ds', 'push 0xc00', 'push ax', 'lcall 0x4fff, 0xa32'])
    exact(s, 0x76C229, ['push ds', 'mov ax, 0xc00', 'mov ds, ax',
        'mov ax, word ptr [8]', 'pop ds', 'push 0xc00', 'push ax',
        'lcall 0x4fff, 0xa32', 'add sp, 4', 'push 3', 'lcall 0x71f0, 0'])
    graph = callback_graph(s)
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    writes = []
    for span in graph['ranges']:
        lo, hi = int(span['start'], 16), int(span['end'], 16)
        for i in decoder.disasm(s[lo:hi], lo):
            if i.operands and i.operands[0].type == CS_OP_MEM and \
                    i.operands[0].access & 2 and i.operands[0].mem.disp == 4:
                need(i.op_str in ('word ptr [si + 4], 0x20',
                                  'word ptr [si + 4], 0xffdf') and
                     i.mnemonic in ('or', 'and', 'xor'), 'boss callback kind-preserving store')
                writes.append(f'{i.address:06X}: {i.mnemonic} {i.op_str}')
    borrowed = borrowed_graph(s)
    need(not set(borrowed['callbacks']) & {
        '668E:0AFD', '668E:0B06', '668E:0B73', '668E:0C6F', '668E:0D09', '668E:0D35'},
        'audited zero-control/idF borrowed graph excludes form completion')
    normal, special = intro_graph(s, 0xDAA), intro_graph(s, 0x423)
    alternate = intro_graph(s, 0x101)
    need(not normal['direct_2E74'] and not normal['reload_76BC62_reachable'] and
         normal['current_task_self_free_76B8BA'], 'ordinary mode2 introduction excludes reload')
    need(special['direct_2E74'] and special['reload_76BC62_reachable'] and
         special['current_task_self_free_76C237'], 'positive special introduction reload owner')
    need(not alternate['direct_2E74'] and not alternate['reload_76BC62_reachable'] and
         alternate['current_task_self_free_76B8BA'], 'alternate normal introduction excludes reload')
    need(all((((high << 4) | 3) & 0x73FF & 0x43FF & 15) == 3
             for high in range(4096)), 'all high flag combinations preserve actor kind3')
    composed = composition(s)
    return dict(status='BOUNDED_P2_NO_RELOAD_COMPOSITION_PASS',
        game_mode=2, actor_kind=3, opponent_identity=15,
        generic_2AE0_runs_for_kind3=False,
        upper_callback_kind_writes=writes,
        upper_callback_instructions=graph['instructions'],
        borrowed_graph=borrowed, normal_intro=normal, alternate_intro=alternate,
        special_intro=special,
        interpretation='Known SECOND generic devolution is excluded by kind3;76BC62 is a special introduction task, not a stage7 gameplay callback.',
        composition=composed, full_post_clear_reload_exclusion_approved=False,
        remaining='Bounded resident93E7 projection supported; external8F24 domain/entry gate and arbitrary scheduler/callback states excluded.',
        ROM_modified=False, runtime_executed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    s = a.source.read_bytes()
    need(hashlib.sha256(s).hexdigest().upper() == SOURCE, 'exact original source')
    need(not a.output.exists(), 'fresh report required')
    result = proof(s)
    rejected = []
    for name, at in [('kind3 construction', 0x740D7B), ('wrapper kind gate', 0x7421E0),
        ('Shoot kind mask', 0x747B39), ('normal introduction seed', 0x76B4F5),
        ('callback kind store', 0x7480C5), ('intro self retirement', 0x76B8BD),
        ('lower indirect target', 0x7498DB), ('borrowed auxiliary owner', 0x762D73),
        ('auxiliary parent write', 0x78660D), ('encoded indirect2E74', 0x74374D)]:
        bad = bytearray(s)
        bad[at] ^= 1
        try:
            proof(bad)
        except (ValueError, AssertionError, SystemExit):
            rejected.append(name)
        else:
            raise ValueError('accepted mutation ' + name)
    result['negative_controls_rejected'] = rejected
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print('PASS bounded P2 no-reload composition;10 negatives; external8F24 gate retained')


if __name__ == '__main__':
    main()
