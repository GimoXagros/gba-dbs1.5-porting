#!/usr/bin/env python3
"""Reproducible OPEN_DOMAIN assessment for the resident controller bridge.

Combines existing finite action/pursuit proofs with concrete opponent control,
drop-through, horizontal collision and lower-object ownership contracts.
Does not authorize or claim terminal camera/graphics or external scene entry.
"""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha
from analyze_shoot_player_domain import action_rows, consumers
from analyze_shoot_pursuit_bounds import terrain
from analyze_shoot_opponent_controls import analyze as controls
from analyze_shoot_drop_path import analyze as drop
from analyze_shoot_outer_x import analyze as outer_x

ROOT=Path(__file__).resolve().parent.parent
V68='9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738'
FROZEN={
    'tools/analyze_shoot_player_domain.py':'9317949258F182498CC266704FEDA301AE8D94E00BCE26BDFF83AEC567D9875D',
    'tools/analyze_shoot_pursuit_bounds.py':'FB817D4890E09E0EC3B8ED02674FF11BDFF0FF79DE6287B88B0E03285C4D17AE',
    'records/shoot-spatial-independent-20261105.md':'243E5DF97A5121FF9D2654FDD486009E1454B4CE63A568818BAE2F40039105F7',
    'tools/analyze_shoot_opponent_controls.py':'30052414FDC255B5E553ED23243956A30933C8D4A4D72574A16622DB8B330F64',
    'tools/analyze_shoot_drop_path.py':'73749E10126AE7B2CF2EBAA7318D065E330378F082CC1F5636F359BCB0DA8314',
    'tools/analyze_shoot_outer_x.py':'AE7EA6CBC2373A3645519985FFF98675E4E13960FB4EE27065FA235734E8AAF2',
}


def owners(r):
    exact(r,0x747BDD,['and word ptr [si + 4], 0xfff0',
        'or word ptr [si + 4], 0x26','and word ptr [si + 4], 0x9fbf',
        'mov word ptr [si + 0x32], 0','mov word ptr [si + 0x34], 0',
        'mov word ptr [si + 0x36], 0','mov word ptr [si + 0x38], 0'])
    exact(r,0x74235D,['test word ptr [si + 4], 0x4000','je 0x742376',
        'mov ax, word ptr [si + 4]','and ax, 0xf','cmp ax, 9',
        'je 0x742376','call 0x7424d6'])
    exact(r,0x741625,['mov si, word ptr es:[0x65c]',
        'mov di, word ptr es:[0x65e]','call 0x74273b'])
    exact(r,0x747C0F,['mov ax, word ptr [bp - 6]',
        'mov word ptr [si + 0x1c], ax','mov ax, word ptr [bp - 8]',
        'mov word ptr [si + 0x14], ax'])
    exact(r,0x7495DD,['mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0','mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0','mov bx, word ptr [si + 0x14]',
        'mov ax, word ptr [bx + 0x26]','mov word ptr [si + 0x26], ax'])
    exact(r,0x7496A0,['mov word ptr [si + 0x80], 0x14',
        'mov bx, word ptr [si + 0x14]','mov ax, word ptr [bx + 0x28]',
        'mov word ptr [si + 0x8c], ax'])
    need(struct.unpack_from('<13H',r,0x760055)[6]==0x37A,'kind6 damage owner')
    exact(r,0x760362,['mov word ptr [di], 0x17cc',
        'mov word ptr [di + 2], 0x638c'])
    exact(r,0x7603B8,['push ax','push 0x638c','push 0x17cc',
        'push 0xc00','push di','lcall 0x5ffd, 0xec8'])
    exact(r,0x760135,['mov bx, word ptr [di + 0x1c]',
        'mov byte ptr [bx + 0x58], 0','mov word ptr [bx + 0xc], 1',
        'push 0x96','push word ptr [bx + 2]','push word ptr [bx]',
        'push 0xc00','push bx','lcall 0x5ffd, 0xec8'])
    exact(r,0x760F89,['test word ptr [si + 0xc], 1','jne 0x760fb1'])
    exact(r,0x760FB1,['retf'])
    for at in (0x76157D,0x76167F,0x761BA1,0x761CA3):
        exact(r,at,['sub word ptr [si + 0x3c], 0x10'])
    exact(r,0x780F39,['or word ptr [si + 4], 0x8000'])
    exact(r,0x781053,['and word ptr [si + 4], 0xdfff'])
    exact(r,0x781374,['or word ptr [si + 4], 0x20'])
    # Actual finite tracking interval: no instruction can turn hit-list/body
    # production back on. Visibility only changes bit20.
    from analyze_shoot_upper_state_graph import Cs,CS_ARCH_X86,CS_MODE_16
    c=Cs(CS_ARCH_X86,CS_MODE_16)
    writes=[]
    for i in c.disasm(r[0x7495DD:0x7497A6],0x7495DD):
        if i.op_str.split(',')[0]=='word ptr [si + 4]' and i.mnemonic not in ('test','cmp','push'):
            writes.append((i.address,i.mnemonic,i.op_str))
    need(writes==[(0x74960F,'and','word ptr [si + 4], 0xffdf'),
                  (0x74979E,'or','word ptr [si + 4], 0x20')],
         'tracking callback interval changes visibility only')
    return dict(lower_kind=6, lower_hitlist_and_bodypush_bits='6000 clear from747BE7 through8EF3',
        lower_damage_continuation='accepted hit cancels tracking to638C:17CC, optionally via freeze; never resumes tracking',
        linked_freeze='kind3 type18 sets linkedlower+C=1 before freeze; F89 skips wiggle; callback timer and position pause together, then original motion restores',
        body_push='065C/065E pair only, excludes lower071E; writes horizontal delta only',
        player_direct_vertical_effects='ordinary damage corrections only -10 or zero; positiveextra delta16 is checked drop',
        player_terrain='E700 reset; generic action OR8000/ANDDFFF/OR20 preserve collision/no0800; victim clear excluded bycontrols',
        lower_phase_flag_writes=[hex(p) for p,_,_ in writes])


def open_air_contracts(r,actor):
    # An endtype2 row can still take hit/key transitions before landing.
    # This positive cycle prevents an unconditional finite-launch assertion.
    exact(r,0x781904,['jmp 0x7816f1'])
    exact(r,0x781759,['test byte ptr es:[di + 0xb], 1','je 0x781784',
        'test word ptr [si + 0xa0], 8','je 0x781784',
        'test word ptr [si + 0x20], 0x80','je 0x781784',
        'mov ax, word ptr es:[di + 0x22]'])
    exact(r,0x7816F8,['cmp word ptr es:[di + 0x18], 0','je 0x781720',
        'test word ptr [si + 0xa], 4','je 0x781720',
        'mov ax, word ptr es:[di + 0x18]'])
    exact(r,0x781A09,['test byte ptr es:[di + 0xb], 8','jne 0x781a1a',
        'mov word ptr [si], 0x1b8f','mov word ptr [si + 2], 0x668e','retf',
        'mov word ptr [si], 0x1cbb','mov word ptr [si + 2], 0x668e','retf'])
    exact(r,0x742322,['sar ax, 4','sar bx, 4'])
    direct=[]; cycle_rows={}
    for resource in actor['resources']:
        base=int(resource['pointer'],16); count=resource['count']
        ptrs=struct.unpack_from('<'+'H'*count,r,base+4)
        for index,p in enumerate(ptrs):
            row=r[base+p:base+p+36]
            if row[13]&8:
                direct.append([resource['form'],resource['identity'],index,base+p,
                               struct.unpack_from('<h',row,8)[0]])
            if resource['form']=='base' and resource['identity']==14 and index in (18,19,20,22,23):
                links={hex(k):ptrs.index(struct.unpack_from('<H',row,k)[0])
                       for k in range(22,36,2) if struct.unpack_from('<H',row,k)[0]}
                cycle_rows[index]=dict(motion=row[1],end=row[2],flags=row[10:14].hex(),links=links)
    need(direct==[['base',4,30,0x3BCA7A,24]],'complete indexed direct-X shift population')
    need(cycle_rows[19]['end']==2 and cycle_rows[19]['flags']=='02010000'
         and cycle_rows[19]['links']['0x22']==22,'landing-wait key exit')
    need(cycle_rows[22]['links']['0x18']==18 and cycle_rows[18]['links']['0x16']==20
         and cycle_rows[20]['links']['0x16']==19,'fresh-hit aerial repeat cycle')
    need(cycle_rows[23]['end']==2 and cycle_rows[23]['flags']=='02000000'
         and set(cycle_rows[23]['links'])=={'0x16'},'alternate landing lock')
    return dict(base14_possible_hit_key_cycle=[22,18,20,19,22],rows=cycle_rows,
        cycle_condition='each22 hit exit requires a fresh overlap/hit flag; actual Shoot target geometry remains to be correlated',
        direct_X_shift_rows=direct,
        direct_X_condition='base4 action30 moves X by facing-signed384 before action31; actual material6 wall-action entry exclusion remains separate',
        velocity_units='actor742322/325 SAR4 converts velocity to16-units-per-pixel coordinates before the cap',
        conclusion='ordinary jump/isolated launch arithmetic is not a proof excluding repeated hit-dependent aerial resets')


def analyze(r,g):
    need(sha(r)==SOURCE_SHA and sha(g)==V68,'immutable source and exact v68 baseline')
    for path,digest in FROZEN.items():need(sha((ROOT/path).read_bytes())==digest,'frozen prior proof '+path)
    actor=action_rows(r);consumers(r)
    geometry=terrain(r,g)
    control=controls(r);fall=drop(r);ownership=owners(r)
    horizontal=outer_x(r)
    air=open_air_contracts(r,actor)
    negative=[]
    for at in (0x78175D,0x7816FC,0x781A0D,0x742327):
        bad=bytearray(r);bad[at]^=1
        try:open_air_contracts(bad,actor)
        except ValueError:negative.append(hex(at))
        else:raise ValueError('ineffective open-contract mutation '+hex(at))
    return dict(status='OPEN_DOMAIN',complete_controller_input_domain=False,
        external_scene_entry_authorized=False,source_sha256=sha(r),candidate_sha256=sha(g),
        scope='source producer contracts only; internal resident wiring may be reviewed separately while the external retail scene route stays unchanged',
        dependencies=FROZEN,
        closed_components=dict(opponent_controls=control,drop_path=fall,lower_ownership=ownership,
            action_resources=dict(resources=actor['resources_count'],rows=actor['indexed_rows'],
                landing_type2_rows=actor['landing_type2_rows'],
                parent_position_rewrite_rows=actor['parent_position_rewrite_rows']),
            source_native_terrain=geometry),
        conditional_prior_pursuit=dict(recomputed=False,reference='records/shoot-spatial-independent-20261105.md',
            abstract_state_visits=5462663,updates=245,signed_X=[-5839,7198],
            target_X_required=[0,7167],selector_X_exclusive_upper=7680,
            condition='arbitrary target within0..1BFF each tick, exact245-update callback timing and own-motion only; P1 target-domain premise remains open'),
        horizontal=horizontal,airborne=air,
        remaining=[
            'Coupled reachable P1 X/Y invariant: horizontal-only0..7167 and0..7199 envelopes are disproved by source corner states.',
            'Correlate actual Shoot hit targets and auxiliary children with aerial reset cycles and external damage; a whole-player nonnegativeY claim is not established.',
            'Close base4 direct-X action30 entry ownership and all applicable airborne special/reset continuations.',
            'Combine those facts with closed drop and landing contracts before claiming capturedP1Y<=1B00 and unconditional lower selector bounds.',
            'External scene route, terminal camera/IRQ and graphics lifetime are separate and are not approved by this report.'],
        negative_controls_rejected=negative,ROM_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    need(not a.output.exists(),'fresh output required')
    result=analyze(a.source.read_bytes(),a.candidate.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('OPEN_DOMAIN: controls/drop/action/ownership checks pass; reachable coupled X/Y and external entry remain unproved')


if __name__=='__main__':main()
