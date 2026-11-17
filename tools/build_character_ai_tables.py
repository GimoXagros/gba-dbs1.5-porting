"""Complete source AI identity normalization, parameters, behaviors and actions."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine as ParentMachine
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
INPUT = '75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OLD = '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'
FIRST, LIMIT = 0xD88800, 0xD8AB00
PARAMS, HELPER, BEHAVIORS, ACTIONS = 0xD88800, 0xD888AC, 0xD88900, 0xD89800
PARAM_ALIASES = (0xC7140,0xC714C,0xC7154,0xC715C,0xC7164,0xC716C,0xC7174,
                 0xC717C,0xC7184,0xC718C,0xC7194,0xC719C,0xC71A4,0xC71AC,0xC71B4)
ACTION_ALIASES = {0xC6A2C:14,0xC6A3C:0,0xC6B2C:0,0xC6B34:0,
                  0xC6BB4:16,0xC6BB8:17,0xC6BBC:16}
OWNER_PINS = ('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
 '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
 '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD',
 '54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55',
 '6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C',
 '06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230')

def need(ok, message):
    if not ok: raise ValueError(message)
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def u(b,a): return struct.unpack_from('<I',b,a)[0]
def h(b,a): return struct.unpack_from('<H',b,a)[0]
def asm(code, at): return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(code,BASE+at)[0])
def normalize(ident): return 7 if ident == 11 else ident-5 if ident >= 13 else ident

def aliases(data,start,size):
    result={}
    for alignment in range(4):
        end=len(data)-(len(data)-alignment)%4
        for n,(value,) in enumerate(struct.iter_unpack('<I',data[alignment:end])):
            if BASE+start <= value < BASE+start+size:
                result[alignment+4*n]=value-BASE-start
    return result

def contract(before,gba,old,source):
    need(tuple(map(sha,(before,gba,old,source)))==(INPUT,GBA,OLD,SOURCE),'four pinned inputs')
    params=source[0x782970:0x782A1A]
    behaviors=source[0x74EB2A:0x74FA2A]
    actions=bytearray(source[0x74D89A:0x74EB2A])
    need(len(params)==170 and len(behaviors)==3840 and len(actions)==4752,'complete source extents')
    need(params[:136]==old[0x3C3250:0x3C32D8]==before[0xC6C7C:0xC6D04], 'all eight retained parameter rows')
    need(old[0x3AB1EE:0x3ABDEE]==before[0xC3FC0:0xC4BC0], 'all eight retail behavior blocks')
    source_deltas=[i for i in range(258*18) if actions[i]!=old[0x3A9FCA+i]]
    need(source_deltas==[12*18,148*18] and [actions[i] for i in source_deltas]==[7,7], 'two source retained action changes')
    retail_deltas=[i for i in range(258*18) if before[0xC4FC4+i]!=old[0x3A9FCA+i]]
    need(retail_deltas==[42*18+13] and before[0xC4FC4+42*18+13]==0, 'one explicitly retained commercial mask exception')
    actions[42*18+13]=0
    for a,z in ((0xC3FC0,0xC4BC0),(0xC4FC4,0xC4FC4+258*18),(0xC6C7C,0xC6D04),
                (0xC63C0,0xC65F4),(0xC65F4,0xC6C7C),(0xC6D04,0xC6EEC)):
        need(before[a:z]==gba[a:z], 'retained native data and consumers '+hex(a))
    need(aliases(before,0xC6C7C,136)==dict.fromkeys(PARAM_ALIASES,0), 'all15 parameter interior aliases')
    need(aliases(before,0xC3FC0,3072)=={0xC658C:0}, 'sole behavior alias')
    need(aliases(before,0xC4FC4,258*18)==ACTION_ALIASES, 'all7 action interior aliases')
    decoder=Cs(CS_ARCH_X86,CS_MODE_16)
    lines=[i.mnemonic+' '+i.op_str for i in decoder.disasm(source[0x782B46:0x782B63],0x782B46)]
    need(lines==['xor ah, ah','cmp ax, 0xb','jne 0x782b53','mov ax, 7','jmp 0x782b5b',
                 'cmp ax, 0xd','jb 0x782b5b','sub ax, 5','push ax','mov bx, 0x11','mul bx','mov bx, ax'], 'exact source identity normalization')
    need(source[0x74D45E:0x74D46A].hex()=='26031e960603da2e8b873a18','actual source behavior lookup')
    need(source[0x74D68D:0x74D695].hex()=='2e8b8faa0526890d','actual source action copy')
    need(source[0x782D23:0x782D2A].hex()=='58f7e326a39606','normalized identity retained for behavior block')
    cells=struct.unpack('<1920H',behaviors)
    need(max(cells)==262 and all(x<264 for x in cells),'all ten behavior domains')
    need(max(h(actions,i*18+14) for i in range(264))==261,'all action continuations bounded')
    states=sorted(set(h(actions,i*18)&255 for i in range(264)))
    need(states==[0,1,2,3,5,6,7,8,9,10],'existing opcode dispatch sufficient')
    changed_cells=[i for i in range(1536) if h(behaviors,2*i)!=h(before,0xC3FC0+2*i)]
    need(len(changed_cells)==23,'23 source behavior changes in retained eight blocks')
    return params,behaviors,bytes(actions),dict(source_parameters=[0x782970,0x782A1A],
      source_behaviors=[0x74EB2A,0x74FA2A],source_actions=[0x74D89A,0x74EB2A],
      identities=[dict(id=i,index=normalize(i),within_parameter_domain=normalize(i)<10) for i in range(15)],
      source_retained_action_changes=source_deltas,commercial_exception=dict(action=42,offset=12,source=0xFF7E,native=0x007E,
      significance='Full halfword input AND mask; deliberately retain commercial behavior, not full source parity.'),
      changed_retained_behavior_cells=changed_cells,action_state_codes=states,continuation_max=261,
      source_windows=[dict(start=a,end=z,sha256=sha(source[a:z])) for a,z in
        ((0x782B34,0x782D2E),(0x74D433,0x74D4AF),(0x74D66D,0x74D89A))])

def ownership(before,paths):
    blobs=[p.read_bytes() for p in paths]
    need(tuple(map(sha,blobs))==OWNER_PINS,'six frozen owner manifests')
    owners=list(map(json.loads,blobs));checked=0
    for owner in owners:
        for w in owner['writes']:
            a,z=w['offset'],w['offset']+w['size']
            need(not max(a,FIRST)<min(z,LIMIT),'new reservation disjoint from prior writes')
            if 'after_hex' in w:need(before[a:z]==bytes.fromhex(w['after_hex']),'prior owner bytes retained')
            else:need(sha(before[a:z])==w['after_sha256'],'prior owner hash retained')
            checked+=1
        for a,z in owner.get('reservations',[]):
            need(not max(a,FIRST)<min(z,LIMIT),'new reservation disjoint from prior reservation')
    need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'entire new reservation blank')
    need(sha(Path(scanner.__file__).read_bytes())==SCANNER,'frozen conservative scanner')
    scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
    hits=scan(before);need(not hits,'zero incoming references, no exemptions')
    return dict(reservation=[FIRST,LIMIT],prior_manifest_sha256=list(OWNER_PINS),preserved_writes=checked,inbound_hits=hits,new_RAM_bytes=0)

class Machine(ParentMachine):
    def run(self,start,stops,max_steps=16000):
        for _ in range(128):
            try:return super().run(start,stops,max_steps)
            except ValueError as e:
                if str(e)!='immediate halfword transfer':raise
                pc=self.r[15]-8;w=self.get(pc)
                if w in (0xE0010190,0xE0000091):
                    self.r[(w>>16)&15]=(self.r[w&15]*self.r[(w>>8)&15])&0xFFFFFFFF
                elif w==0xE19100B8:self.r[0]=self.get(self.r[1]+self.r[8],2)
                elif w==0xE19500F0:
                    v=self.get(self.r[5]+self.r[0],2);self.r[0]=(v if v<32768 else v-65536)&0xFFFFFFFF
                else:raise ValueError('unreviewed register/multiply form '+hex(w))
                start=pc+4
        raise ValueError('bounded native extension exhausted')

def fixture(rom,ident,difficulty=2,progress=2,flags=0):
    m=Machine(rom,seed=7,flags=(flags<<28)|0x1F)
    for a,z in ((0x03002310,0x03002340),(0x03003D30,0x03003DB0),(0x03004D88,0x03004DE0)):
        for at in range(a,z):m.put(at,0,1)
    m.put(0x0300231C,ident,1);m.put(0x0300231F,difficulty,1);m.put(0x0300232E,progress,1)
    m.services[0x08012600]=lambda q:q.r.__setitem__(0,0x55)
    return m

def validate(before,after,params):
    map_cases=0
    for ident in range(256):
        for flags in range(16):
            m=Machine(after,seed=3,flags=(flags<<28)|0x1F)
            m.r[0]=7 if ident==11 else ident
            regs=list(m.r);cpsr=m.cpsr
            m.run(BASE+HELPER,{0x080C6D6C})
            need(m.r[0]==normalize(ident) and m.r[13]==regs[13]-4 and m.get(m.r[13])==normalize(ident),'mapping and saved downstream identity')
            need(m.r[1:13]==regs[1:13] and m.r[14]==regs[14] and m.cpsr==cpsr,'all helper registers and flags retained')
            map_cases+=1
    full=parity=0
    for ident in (*range(10),11,13,14):
        for difficulty in range(3):
            for progress in range(13):
                m=fixture(after,ident,difficulty,progress);ret=m.r[14]
                m.run(0x080C6D04,{ret})
                index=normalize(ident);row=params[index*17:index*17+17]
                need(m.get(0x03004D92,2)==index*384,'actual full initializer behavior block offset')
                for src,dst,size in ((0,2,2),(2,4,2),(4,6,1),(5,7,1),(13,8,1),(14,9,1),(15,0x24,1),(16,0x25,1)):
                    if src==4:continue  # Existing progress consumer modifies this field.
                    need(m.get(0x03004D88+dst,size)==int.from_bytes(row[src:src+size],'little'),'actual initializer source parameter field')
                if ident<8 or ident==11:
                    old=fixture(before,ident,difficulty,progress);old.run(0x080C6D04,{ret})
                    need((old.r,old.cpsr,old.mem)==(m.r,m.cpsr,m.mem),'retained identity full native state parity')
                    parity+=1
                full+=1
    return dict(normalization_cases=map_cases,full_initializer_cases=full,retained_identity_fullstate_cases=parity,
      domain='Full initializer indices0..9 through IDs0..9,11,13,14; sourceIDs10/12 are not supported ordinary campaign CPU rows. Mapping alone checked all256 bytes.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','gba','old','source','output','manifest'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--owners',type=Path,nargs=6,required=True);a=p.parse_args()
    paths=[a.before,a.gba,a.old,a.source,*a.owners,a.output,a.manifest]
    need(len(set(x.resolve() for x in paths))==len(paths) and not a.output.exists() and not a.manifest.exists(),'fresh distinct outputs')
    before,gba,old,source=(x.read_bytes() for x in paths[:4])
    params,behaviors,actions,proof=contract(before,gba,old,source)
    allocation=ownership(before,a.owners)
    helper=asm('push {r8}; mrs r8,cpsr; cmp r0,#13; subhs r0,r0,#5; msr cpsr_f,r8; pop {r8}; push {r0}; b 0x080C6D6C',HELPER)
    need(len(helper)==32 and u(before,0xC6D68)==0xE92D0001,'exact helper and original hook')
    writes=[];after=bytearray(before)
    def put(at,blob,label):
        need(not any(max(at,w['offset'])<min(at+len(blob),w['offset']+w['size']) for w in writes),'disjoint writes')
        writes.append(dict(offset=at,size=len(blob),before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex(),label=label));after[at:at+len(blob)]=blob
    for at,blob,label in ((PARAMS,params,'ten source parameter rows'),(HELPER,helper,'source identity normalization with flags preserved'),
                          (BEHAVIORS,behaviors,'ten complete source behavior blocks'),(ACTIONS,actions,'264 actions preserving commercial row42 mask'),
                          (0xC6D68,asm(f'b 0x{BASE+HELPER:X}',0xC6D68),'normalized identity before saved push')):put(at,blob,label)
    for at in PARAM_ALIASES:put(at,struct.pack('<I',BASE+PARAMS),'parameter table reader')
    put(0xC658C,struct.pack('<I',BASE+BEHAVIORS),'behavior table reader')
    for at,off in ACTION_ALIASES.items():put(at,struct.pack('<I',BASE+ACTIONS+off),'action table interior reader')
    after=bytes(after);inverse=bytearray(after)
    for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
    need(bytes(inverse)==before and len(writes)==28 and sum(w['size'] for w in writes)==8890,'whole-image inverse and complete declared span count')
    checks=validate(before,after,params)
    report=dict(status='PASS',input_sha256=INPUT,output_sha256=sha(after),source_sha256=SOURCE,reservations=[[FIRST,LIMIT]],allocation=allocation,
      contract=proof,validation=checks,writes=writes,actual_changed_bytes=sum(x!=y for x,y in zip(before,after)),
      limits=['No live emulator or first-bad-state causal witness is claimed by this static layer.',
              'Existing12-handler opcode dispatch unchanged; no invalid state clamp.',
              'Native row42 full-halfword input-mask exception retained; no complete source parity claim for that commercial behavior.',
              'No RAM allocation, main builder, Git or frozen output changes.'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(after);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',output_sha256=sha(after),manifest_sha256=sha(a.manifest.read_bytes()),validation=checks)))

if __name__=='__main__':main()
