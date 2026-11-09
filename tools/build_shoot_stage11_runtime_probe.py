#!/usr/bin/env python3
"""Separate 84D probe: compose approved HUD guard and one resident nonfatal hook."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import analyze_shoot_fatal_callback_contract as fatal
from analyze_waterfall_third_pattern import no_inbound
from build_shoot_presentation_target_lifetime import WRITES as TARGET_WRITES
from verify_shoot_static_companion_clear import Machine as ParentMachine

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
D0='D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
INPUT='84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
C8='C8E810258B41A979A4DCE514119D8CAF139D615D63355F18F1C2E49AD72332F6'
HOOK,ADAPTER=0x36E634,0x5CD9A0
P,Q,AUX=0x02011710,0x02011828,0x02011940
RETURN=0x09000000
CAPTURE=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
PINS=((ADAPTER,ADAPTER+156,'FAF0C722D88D307D08C32F20B2F5E06A9713ADC116B54CC2E22805C51CAF7404'),
 (0x132EC,0x133A8,'10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B'),
 (0x3730E8,0x373100,'3BD48A92D9CD1EABA958B7B7BBACD9E63DA7DF63ABD3DAD75D40E48D8E1D21FE'),
 (0x3700F0,0x370104,'044B00D7AE30247DC4AEAED3AF68F788E1B78245840F59257673D830C6E9FB95'),
 (0x370248,0x370250,'364EAAFB92517167A4D185FDD66848223FA4FCFC6A143BE84E9EF35839573CD9'),
 (0x586B00,0x586B34,'A91DE0DCF1BC768B83B7388DDF4034BE2DE88F73771CF857E78773B57A3AD75D'),
 (0x586C00,0x586D7C,'3BE9E5C9475CF912228CD64416B3AF5B30E130A0ACBBB87E77D53672EFAC7854'),
 (0x586E00,0x586ECC,'55EAB111B9F17E191D071A52009FE01BB0CA0A2A86F5963D63EFE30966EEC95F'),
 (0x587000,0x58707C,'E14474002C68F04F1A4C48ACF2256D22D84D4528F2F6CC81B2B836608E36EFF6'),
 (0x5C0B00,0x5C0B28,'829EB7173630790AA6266A53A0C4AB43BF98D9ED1B5964E8037E6311F693D793'),
 (0x587100,0x587178,'8A45017FD9AC75690D201120A6C50640866FDE13A05A8A10BEF16895551E047E'),
 (0x586F00,0x586F60,'68E8B987993C62EDB9944C97F4B1EF47C2BE4A038A9EA8E51E16585B168C9C79'))
DEPS={'build_shoot_presentation_target_lifetime.py':'8C099EAD5CCA7AFD86482DC810AD15FE90DA09F429D30C86AEE95F5A9EA3C783',
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
 'analyze_shoot_fatal_callback_contract.py':'310DC0A39AA5055B29BCE81C3033D75B5A13AEC385F56C713739EF1391755395',
 'analyze_waterfall_third_pattern.py':'DB327A22961631CBEE0CEB725525BFBA06775115313C0F34504AF1D9CAE174A3'}


def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def branch(at,target):return struct.pack('<I',0xEA000000|(((target-at-8)//4)&0xFFFFFF))


class Machine(ParentMachine):
    """Actual ARM, adding only reviewed immediate postindexed halfwords.

    No imported service or BIOS model is used on any executed test route.
    """
    EXTRA={0x08013308,0x085CDA04,0x085CDA14,0x08586EA4,0x08586EA8}
    EXTRA.update(range(0x08013328,0x080133A0,4))

    def run(self,start,stops,max_steps=16000):
        pc=start
        for _ in range(1024):
            pc=super().run(pc,set(stops)|self.EXTRA,max_steps)
            if pc in stops:return pc
            w=self.get(pc);self.r[15]=pc+8
            need(w>>28==14 and w&0x0E400090==0x00400090 and not w&0x01200000,
                 'reviewed unconditional immediate postindexed halfword')
            base,reg=(w>>16)&15,(w>>12)&15
            need(base!=reg and (w>>5)&3==1,'nonalias LDRH/STRH')
            offset=((w>>4)&0xF0)|(w&15);address=self.r[base]
            if w&0x100000:self.r[reg]=self.get(address,2)
            else:self.put(address,self.r[reg],2,True)
            self.r[base]=(address+(offset if w&0x800000 else -offset))&0xFFFFFFFF
            pc+=4
        raise ValueError('bounded halfword execution did not return')


def apply(data,writes):
    out=bytearray(data)
    for at,before,after in writes:
        need(out[at:at+len(before)]==before,'ExpectedWrite predecessor '+hex(at))
        out[at:at+len(after)]=after
    return bytes(out)


def inverse(candidate,writes):
    return apply(candidate,[(a,z,b)for a,b,z in writes])


def compose(before,d0,c8):
    need((sha(before),sha(d0),sha(c8))==(INPUT,D0,C8),'approved 84D,D0,C8 identities')
    tw=[(a,struct.pack('<I',b),struct.pack('<I',c))for a,b,c in TARGET_WRITES]
    hw=[(0x373ED8,struct.pack('<I',0xE3590007),branch(0x373ED8,0x6FF400)),
        (0x6FF400,b'\xff'*16,struct.pack('<3I',0xE359000B,0x012FFF1E,0xE3590007)+branch(0x6FF40C,0x373EDC))]
    need(apply(d0,tw)==before and inverse(before,tw)==d0,'exact target-fix inverse')
    need(apply(d0,hw)==c8 and inverse(c8,hw)==d0,'exact approved HUD inverse')
    ledger_bytes=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    irq_bytes=(ROOT/'build/shoot-guarded-transition-20261109/component-c.json').read_bytes()
    need(sha(ledger_bytes)=='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33','1394-interval ledger')
    need(sha(irq_bytes)=='D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C','IRQ ownership manifest')
    ledger,irq=json.loads(ledger_bytes),json.loads(irq_bytes)
    need(ledger['normalized_interval_count']==1394 and ledger['layer_count']==70,'complete interval population')
    owned=[[0,0x400000]]+ledger['merged_union']+irq['reservations']+[
        [0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0],[0x33FD04,0x33FD08],[0x6FF380,0x6FF400]]
    need(not any(a<0x6FF410 and 0x6FF400<z for a,z in owned),'HUD cave outside every full reservation')
    need(before[0x6FF400:0x6FF410]==b'\xff'*16,'whole HUD cave blank on84D')
    ownership=no_inbound(before,[(0x6FF400,0x6FF410)])
    need(not ownership['classified_instruction_interiors'],'no inbound exemption')
    intermediate=apply(before,hw)
    need(intermediate==apply(c8,tw),'HUD/target changes commute byte-for-byte')
    need(inverse(intermediate,hw)==before and inverse(intermediate,tw)==c8,'both component inverse paths')
    nw=[(HOOK,bytes.fromhex('5C809FE5'),branch(HOOK,ADAPTER))]
    final=apply(intermediate,nw)
    need(inverse(final,nw)==intermediate and inverse(inverse(final,nw),hw)==before,'nonfatal and composed inverse')
    need(inverse(inverse(inverse(final,nw),hw),tw)==d0,'complete inverse toD0')
    return intermediate,final,hw,nw,dict(ownership=ownership,ledger_sha256=sha(ledger_bytes),
        IRQ_manifest_sha256=sha(irq_bytes),commutes=True,both_component_inverse_paths=True)


def source_contract(before,gba,source):
    need(sha(gba)==fatal.GBA and sha(source)==fatal.SOURCE,'immutable native/source identities')
    for name,digest in DEPS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'pinned helper '+name)
    for lo,hi,digest in PINS:need(sha(before[lo:hi])==digest,'resident consumer pin '+hex(lo))
    need(sha(source[0x760229:0x7602AA])=='972B1E365B43B0813CDB370EEA2FE8D9444154A55E0C61644B983D248E7894AD','source positive-HP branch')
    need(before[0x36E5C8:0x36E5EC]==gba[0x36E5C8:0x36E5EC],'unchanged damage adjustment/subtract/store and BGT')
    need(before[0x36E634:0x36E69C]==gba[0x36E634:0x36E69C],'unchanged non11 native path')
    need(u(before,0x3730F8)==0xE1500008,'legacy refresh CMP kills all incoming flags')
    shared=fatal.flags_dead(before)
    return dict(source_nonfatal=0x760229,stage11_palette=0x085C0B00,flash_timer=0x74,
        non11_join=0x0836E638,stage11_join=0x0836E438,shared_tail_flags_dead=shared,
        timer_owner=[0x083700F4,0x08586B00,0x08586C00,0x08587000],no_new_lifetime_owner=True)


def capture_memory():
    mem={};pins={}
    for name,base,digest in [('iwram',0x03000000,'9FC46E5351D0FEBB822C18591855E6B2BFE2FCDCC8077FB0EBCA6524B9C4E978'),
        ('ewram',0x02000000,'65D380F9ED988253D931269E944C94786B4428EA12F9E9940666A982F70E1DA6')]:
        data=(CAPTURE/('13-healthy-activation-'+name+'.bin')).read_bytes()
        need(sha(data)==digest,'actual healthy capture '+name);pins[name]=digest
        mem.update((base+i,v)for i,v in enumerate(data))
    return mem,pins


def fixture(rom,mem,stage=11,flags=0,mask=0,hp=37,damage=1,evolved=False):
    m=Machine(rom,flags%3,(flags<<28)|0x10);m.mem=mem.copy()
    m.r[4],m.r[5],m.r[11],m.r[14]=P,Q,0,RETURN
    for a,v,n in [(0x0300231E,stage,1),(0x0300450A,mask,2),(0x03004D40,0,2),
        (P+8,0x4000 if evolved else 0,2),(Q+0x64,hp,2),(Q+0x74,0,2),(Q+0x76,0,2),
        (0x03004D24,damage,1),(0x03004D32,0,1),(P+0xA,0,2),(P+0xB6,0,2)]:m.put(a,v,n)
    m.reads.clear();return m


def palette_writes(m):return [(a,v,n)for a,v,n in m.writes if 0x05000000<=a<0x05000400]
def expected_palette(rom,raw):return [(0x05000222+2*i,h(rom,raw+8+2*i),2)for i in range(15)]


def checks(before,after,mem):
    n=0
    # All byte stages/NZCV: exact original non11 register join; stage11 checked below.
    for stage in range(256):
        if stage==11:continue
        for flags in range(16):
            a=fixture(before,{},stage,flags);b=fixture(after,{},stage,flags)
            a.run(BASE+HOOK,{0x0836E638});b.run(BASE+HOOK,{0x0836E638})
            need(a.r[:15]==b.r[:15] and not b.writes and not b.calls,'non11 exact displaced load/register join')
            n+=1
    linked=0
    for stage in (0,7,255):
        for flags in range(16):
            a=fixture(before,mem,stage,flags);b=fixture(after,mem,stage,flags)
            a.run(BASE+HOOK,{0x083730FC});b.run(BASE+HOOK,{0x083730FC})
            need(a.r[:15]==b.r[:15] and a.cpsr==b.cpsr and a.writes==b.writes and a.calls==b.calls,
                 'non11 actual palette loader and native flag kill retained')
            linked+=1
    masks=(0,0x10,0x20,0x30,0x4000,0x4010,0x4020,0x4030)
    stage11=0
    for mask in masks:
        for flags in range(16):
            m=fixture(after,mem,flags=flags,mask=mask);initial=m.r[:15]
            m.run(BASE+HOOK,{0x0836E438})
            wanted=expected_palette(after,0x5C0B00)
            if mask==0:wanted += [(0x05000000+32*i,31,2)for i in range(24)]
            need(palette_writes(m)==wanted,'real P2 flash payload and exact conditional24zero entries')
            need(m.get(Q+0x74,2)==8 and m.r[4:8]==initial[4:8] and m.r[13]==initial[13],
                 'actual palette ABI preserves actors and balances20-byte frame')
            need(m.get(Q,4)==0x085BF800 and m.get(AUX,4)==0x085BC600,'normal hit does not replace callbacks')
            need(m.services=={},'no modeled imports');stage11+=1
    hp_cases=0
    for hp in (-1,0,1,2,8,37):
        for damage in (0,1,2,255):
            for evolved in (False,True):
                a=fixture(before,mem,hp=hp,damage=damage,evolved=evolved)
                b=fixture(after,mem,hp=hp,damage=damage,evolved=evolved)
                stops={0x0836E5EC,BASE+HOOK}
                old=a.run(0x0836E5C8,stops);new=b.run(0x0836E5C8,stops)
                need(old==new and a.r[:15]==b.r[:15] and a.cpsr==b.cpsr and a.writes==b.writes,
                     'actual positive/lethal HP boundary unchanged')
                hp_cases+=1
    # Actual collision save and positive-HP suffix. Untouched visual/audio hit
    # construction between the save and damage prefix is an explicit boundary.
    collision=fixture(after,mem);initial=collision.r[:15]
    collision.run(0x0836E348,{0x0836E34C})
    collision.run(0x0836E5C8,{RETURN})
    need(collision.r[1:8]==initial[1:8] and collision.r[13:15]==initial[13:15], 'actual collision PUSH/POP and return frame')
    need(collision.get(Q+0x64,2)==36 and collision.get(Q+0x74,2)==8,'full collision computes positiveHP and initializes flash')
    expiry=0
    for hp in (1,9,10,18,19,37):
        for mask in masks:
            m=fixture(after,mem,mask=mask,hp=hp);m.run(BASE+HOOK,{0x0836E438})
            expected=expected_palette(after,0x587150 if hp<=9 else 0x587128 if hp<=18 else 0x587100)
            for tick in range(1,9):
                m.r[14]=RETURN;save=m.r[4:6]+m.r[13:15];m.writes.clear();m.calls.clear()
                # The real wrapper selects the real stage11 core and returns through retail epilogue.
                m.put(0x03004506,m.get(0x03004506,2)&~0x400,2)
                m.run(0x083700F0,{RETURN})
                need(m.get(Q+0x74,2)==8-tick,'eight eligible main-loop updates')
                need(m.r[4:6]+m.r[13:15]==save,'real wrapper/core restores its inherited frame')
                wanted=[]
                if tick==8:
                    wanted=expected[:]
                    if mask==0:wanted += [(0x05000000+32*i,h(after,0x586F40+2*i),2)for i in range(16)]
                need(palette_writes(m)==wanted,'exact threshold palette expiry and sixteen BGzero entries')
                expiry+=1
    return dict(non11_stage_NZCV_join_cases=n,linked_non11_palette_flag_cases=linked,
        stage11_native_palette_cases=stage11,HP_prefix_cases=hp_cases,full_collision_frame_cases=1,
        real_wrapper_expiry_updates=expiry,service_models=[],
        runtime_claim=False,fixture_scope='Healthy actor RAM; finite controlled HP/mask fixtures. Collision executes actual entry save and HP suffix/return; untouched visual/audio prefix is not executed or modeled',
        expiry_scope='Eight eligible wrapper calls; not an unconditional eight video frames; OBJzero transparency entries are not restored')


def build(before,d0,c8,gba,source):
    proof=source_contract(before,gba,source)
    intermediate,after,hw,nw,composition=compose(before,d0,c8)
    mem,pins=capture_memory();semantics=checks(intermediate,after,mem)
    def validate(candidate):
        need(inverse(inverse(candidate,nw),hw)==before,'exact combined ExpectedWrite/inverse')
    validate(after);negative=[]
    for label,at in [('nonfatal hook',HOOK),('HUD hook',0x373ED8),('HUD cave',0x6FF400),
        ('target fix retained',0x5C9174),('P2loader retained',0x132EC),('timer retained',0x586C78),
        ('entry selector retained',0x33FD04),('fatal route retained',0x36E5EC)]:
        bad=bytearray(after);bad[at]^=1
        try:validate(bad)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective wholeROM mutation')
    return intermediate,after,dict(schema=1,status='SEPARATE_STAGE11_RUNTIME_PROBE_AUTHOR_PASS',
        input_sha256=INPUT,D0_sha256=D0,approved_HUD_sha256=C8,intermediate_sha256=sha(intermediate),
        output_sha256=sha(after),source_contract=proof,composition=composition,semantics=semantics,
        capture_sha256=pins,writes=[dict(raw=a,bytes=len(b),before=b.hex().upper(),after=z.hex().upper())for a,b,z in hw+nw],
        declared_bytes=24,changed_bytes=sum(x!=y for x,y in zip(before,after)),
        new_nonfatal_code_RAM_or_task=False,whole_ROM_inverse=True,original_components_unchanged=True,
        negative_controls_rejected=negative,builder_sha256=sha(Path(__file__).read_bytes()),dependencies=DEPS,
        runtime_positive_hit_or_ending_proven=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('input','d0','hud','gba','source','output_dir'):p.add_argument(n,type=Path)
    a=p.parse_args();paths=[a.output_dir/n for n in ('hud-intermediate.gba','component.gba','component.json')]
    need(not any(x.exists()for x in paths),'fresh outputs only')
    middle,result,report=build(*(x.read_bytes()for x in (a.input,a.d0,a.hud,a.gba,a.source)))
    a.output_dir.mkdir(parents=True,exist_ok=True);paths[0].write_bytes(middle);paths[1].write_bytes(result)
    paths[2].write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k]for k in ('status','intermediate_sha256','output_sha256','builder_sha256')}))


if __name__=='__main__':main()
