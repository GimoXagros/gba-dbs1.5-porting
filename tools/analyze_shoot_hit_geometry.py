#!/usr/bin/env python3
"""Positive upper-victim and ID14 aerial-hit geometry; no whole-route claim."""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha
from build_character_p0_completion import source_pointer
from shoot_resource_conversion import parse_shoot_p1


def ascent(velocity, acceleration):
    need(velocity<0 and acceleration>0,'finite upward impulse')
    distance=0
    # Include the initial velocity before acceleration. Actual actor updates
    # accelerate first; this deliberately grants one extra upward sample.
    while velocity<0:
        distance-=velocity>>4
        velocity+=acceleration
    return distance


def grab_positions(s):
    exact(s,0x74301B,['mov ax, word ptr [si + 0x28]','cmp ax, word ptr [di + 0x28]',
        'je 0x743026','jmp 0x743214','mov ax, word ptr [si + 6]',
        'or ax, word ptr [di + 6]','test ax, 1','je 0x743034','jmp 0x743214'])
    exact(s,0x743120,['push 0x52','push 0xc00','push si','lcall 0x4fff, 0x24cb'])
    exact(s,0x762CCB,['mov word ptr [si + 0x32], 0','mov word ptr [si + 0x34], 0',
        'mov word ptr [si + 0x36], 0','mov word ptr [si + 0x38], 0',
        'mov word ptr [si], 0x2d18','mov word ptr [si + 2], 0x5ffd'])
    exact(s,0x762CEF,['push 0x53','push 0xc00','push di','lcall 0x4fff, 0x24cb'])
    exact(s,0x762F3C,['mov al, byte ptr es:[bx + 9]','cwde','shl ax, 4','mov dx, ax',
        'mov bx, word ptr [si + 0x14]','add cx, word ptr [bx + 0x26]',
        'add dx, word ptr [bx + 0x28]','sub cx, word ptr [si + 0x26]',
        'sub dx, word ptr [si + 0x28]','shl cx, 4','shl dx, 4',
        'mov word ptr [si + 0x32], cx','mov word ptr [si + 0x34], dx'])
    exact(s,0x761208,['mov ax, word ptr [si + 0x90]','mov word ptr [si + 0x34], ax',
        'mov ax, word ptr [si + 0x92]','mov word ptr [si + 0x38], ax'])
    exact(s,0x766985,['mov word ptr [si + 0x8e], ax','mov word ptr [si + 0x90], dx',
        'mov ax, word ptr es:[bx + 0x1c]','mov dx, word ptr es:[bx + 0x1e]',
        'mov word ptr [si + 0x92], ax','mov word ptr [si + 0x94], dx'])
    need(struct.unpack_from('<H',s,0x763838)[0]==0x38A4,'actual throw descriptor')
    need(struct.unpack_from('<3h',s,0x763874+0x1A)==(448,0,0),'throw velocity downward and no vertical acceleration')
    samples=[]; forms=[]
    for identity in range(15):
        p1=source_pointer(s,0x740000+identity*32+6); values=[]
        for event in (0x52,0x53):
            count,off,_a,_b=struct.unpack_from('<4H',s,p1+4+event*8)
            values.extend(struct.unpack_from('<b',s,p1+off+k*12+9)[0] for k in range(count))
        samples.extend(values); forms.append([identity,min(values),max(values),len(values)])
    need((min(samples),max(samples))==(-53,0),'all base grab attachment offsets')
    # Every pair, including skipped/held animation rows, remains representable
    # by the signed16 delta<<4 used by the attachment consumer.
    for previous in set(samples):
        for current in set(samples):need(-32768<=(current-previous)*256<=32767,'attachment delta does not wrap')
    return dict(base_forms=forms,offset_samples=len(samples),Y_offset_pixels=[-53,0],
        position_lower_bound_given_grounded_parent_Y_at_least_4224=3376,
        throw_velocity=448,throw_vertical_acceleration=0,
        scope='position-only during ordinary stationary grab attachment and its immediate downward release; grounded-parent premise is conditional',
        resource_limit='generic victim events48/49/38 exceed the six-event Shoot upper resource; this position calculation does not establish borrowed-event hitbox ownership')


def proof(s):
    exact(s,0x747B7E,['push 0x24b2','push 0','push 0xbd','push 0x25f8',
        'push 0','push 0xbc','push 0x2f41','push 0','push 0xc00','push si',
        'lcall 0x4fff, 0x23f4'])
    exact(s,0x74252D,['mov si, word ptr [di + 0x22]','mov bx, 0x3b06'])
    exact(s,0x74258A,['cmp word ptr es:[si + 0xa], 0','jne 0x742594',
        'jmp 0x7425e7','mov si, word ptr es:[si + 0xa]','mov bx, 0x3a5e'])
    exact(s,0x74255D,['mov ax, word ptr es:[si + 4]',
        'add ax, word ptr [bp - 4]','mov word ptr [bx + 6], ax',
        'mov ax, word ptr es:[si + 6]','mov dx, word ptr es:[si + 8]',
        'mov word ptr [bx + 8], ax','mov word ptr [bx + 0xa], dx'])
    exact(s,0x7521FD,['mov bx, word ptr [bp + 0x10]',
        'add bx, word ptr [bp + 0x18]','sub bx, ax','jle 0x75221c'])
    exact(s,0x760033,['mov si, word ptr [si]','mov di, word ptr [di]',
        'or word ptr [si + 0xa], 1','or word ptr [di + 0xa], 2'])
    exact(s,0x7600DD,['or word ptr [si + 0xa], 4','or word ptr [di + 0xa], 8'])
    exact(s,0x742322,['sar ax, 4','sar bx, 4'])
    exact(s,0x742309,['mov ax, word ptr [bp - 4]','mov bx, word ptr [si + 0x38]',
        'add word ptr [si + 0x32], ax','add word ptr [si + 0x34], bx'])
    exact(s,0x7424E1,['mov ax, word ptr [si + 0x26]','mov bx, word ptr [si + 0x28]',
        'mov word ptr [bp - 2], ax','mov word ptr [bp - 4], bx'])
    exact(s,0x74161F,['call 0x7426b0','call 0x7427fb'])
    exact(s,0x741669,['call 0x7418c7'])
    exact(s,0x781826,['xor ax, ax','xor bx, bx','xor cx, cx','xor dx, dx','jmp 0x781094'])
    exact(s,0x781863,['mov ax, word ptr es:[di + 0xe]',
        'mov bx, word ptr es:[di + 0x10]','xor cx, cx','mov dx, word ptr es:[di + 0x14]'])
    exact(s,0x7818B6,['mov ax, word ptr es:[di + 0xe]',
        'mov bx, word ptr es:[di + 0x10]','mov cx, word ptr es:[di + 0x12]',
        'mov dx, word ptr es:[di + 0x14]'])
    exact(s,0x7810A4,['test byte ptr es:[di + 0xc], 0x20','je 0x7810b1',
        'add word ptr [si + 0x34], bx','jmp 0x7810b4','mov word ptr [si + 0x34], bx'])
    upper=parse_shoot_p1(s,0x3CF410)
    need(upper['b_relatives']==[0,0x1CC,0,0,0x1CC,0x1CC], 'upper victim events')
    body=struct.unpack_from('<5h',s,0x3CF410+0x1CC)
    need(body==(0,0,0,112,112),'upper type0 victim rectangle')
    upper_frames=sum(len(rows) for rows in upper['payloads'])
    need(upper_frames==34 and all(struct.unpack('<6H',row)[5]==0
        for rows in upper['payloads'] for row in rows),'all upper frames have no attack rectangle')
    action=source_pointer(s,0x740000+14*32+24)
    p1=source_pointer(s,0x740000+14*32+6)
    need((action,p1)==(0x2BFAF0,0x368FF0),'actual base14 resources')
    ptrs=struct.unpack_from('<'+'H'*struct.unpack_from('<H',s,action+2)[0],s,action+4)
    def row(index):return s[action+ptrs[index]:action+ptrs[index]+36]
    def word(r,n):return struct.unpack_from('<H',r,n)[0]
    need(word(row(22),4)==109,'repeat attack actual event')
    n,p,_a,_b=struct.unpack_from('<4H',s,p1+4+109*8)
    rects=[]
    for i in range(n):
        q=struct.unpack_from('<H',s,p1+p+i*12+10)[0]
        if q:rects.append(struct.unpack_from('<5h',s,p1+q))
    need(rects==[(10,-240,-112,208,168),(10,-224,-352,192,192),(10,-96,-400,160,144)],
         'complete direct repeat attack rectangles')
    need(max(y+h for _,x,y,w,h in rects)==56,'largest downward reach')
    for index,motion,vy,ay,nxt in ((18,0,0,0,20),(20,4,-512,16,19),(19,4,0,20,21),(22,7,-800,27,23)):
        v=row(index)
        need(v[1]==motion and struct.unpack_from('<hh',v,16)[0]==vy
             and struct.unpack_from('<h',v,20)[0]==ay and word(v,22)==ptrs[nxt],
             'actual post-hit motion chain '+str(index))
        need(not v[12]&0xA0 and not v[13]&0x30 and not v[11]&0x40,
             'no vertical additive acceleration/homing on chain')
    need(row(19)[11]&1 and word(row(19),34)==ptrs[22],'landing wait can key-cancel to repeat')
    need(word(row(22),24)==ptrs[18] and word(row(22),26)==ptrs[18], 'repeat hit/block exit')
    remaining=ascent(-512,16)+ascent(-800,27)
    need(remaining==1308,'post-hit upward envelope')
    accelerated=ascent(-512+16,16)+ascent(-800+27,27)
    pending_max=50
    need(accelerated==1226 and accelerated+pending_max<=remaining,
         'old-position hit rectangles include pending hit-frame displacement')
    targets=list(struct.iter_unpack('<4h',s[0x7489CC:0x748A0C]))
    need(min(min(y1,y2) for x1,y1,x2,y2 in targets)==3456,'ordinary target endpoints minimum')
    return dict(source_sha256=SOURCE_SHA,status='CONDITIONAL_GEOMETRY',complete_player_domain=False,
        upper=dict(events=6,frames=upper_frames,attack_rectangles=0,victim_events=[1,4,5],
                   victim_rectangle=body,target_routes=targets,
                   endpoint_min_Y=3456,endpoint_bound_is_not_a_trajectory_proof=True),
        repeat_attack=dict(character=14,form='base',action=22,event=109,rectangles=rects,
            maximum_bottom_offset=56,strict_overlap_P1Y_at_least_upperY_minus=167),
        post_fresh_hit=dict(chain=[18,20,19,22],launch_bounds=[528,780],maximum_ascent=remaining,
            accelerated_first_two_launches=accelerated,pending_hit_frame_upward_allowance=pending_max,
            timing='old-world hit rectangle is tested before pending movement commits;1226+50=1276 is covered by conservative1308',
            sufficient_upper_Y_for_strictly_positive_P1Y=1476,
            inequality='P1Y_after_fresh_hit >= upperY - 167 - 1308 = upperY - 1475'),
        grounded_grab_position_only=grab_positions(s),
        remaining=['Actual upper victim Y lower bound through ordinary travel, grounded grab/throw and damage ownership.',
                   'Other target families and indirect attacker-to-parent flag propagation remain separate.',
                   'Complete P1 motion and coupled X/Y closure remain separate.'],
        ROM_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    s=a.source.read_bytes();need(sha(s)==SOURCE_SHA,'immutable source');need(not a.output.exists(),'fresh output')
    result=proof(s);negative=[]
    for at in (0x742596,0x752205,0x7600E0,0x742327,0x3CF5E4,0x36B226,0x762F43,0x76388F):
        bad=bytearray(s);bad[at]^=1
        try:proof(bad)
        except ValueError:negative.append(hex(at))
        else:raise ValueError('ineffective mutation '+hex(at))
    result['negative_controls_rejected']=negative
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('PASS conditional upper/ID14 hit geometry; whole trajectory remains open')


if __name__=='__main__':main()
