"""Reuse frozen ID14 Lua54 checks with only the held-jump delta and source pins."""
import hashlib
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
def replace(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)

base=ROOT/'tools/check_evolution_id14.py'
assert sha(base.read_bytes())=='F583B39E67F9D49CD71CE2FFB991CDA85552190042919460625CCDD2E2FB5E7B'
rom=(ROOT/'build/impmon-evolution-clean15-20261116/component.gba').read_bytes()
assert sha(rom)=='8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
for a,w in {0x356B88:0xE1C49AB2,0x356B9C:0xE3A09010,0x356BCC:0xE1D482BC,
 0x356BD0:0xE3180040,0x356BE8:0xE1C49AB2,0x356C70:0xE1D101F4,
 0x356C78:0xE1D101F6,0x356C84:0xE1D48AB2,0x356C88:0xE3580001,
 0x356C90:0xE1D100F4,0x356C98:0xE1D100F6}.items():
 assert struct.unpack_from('<I',rom,a)[0]==w,hex(a)
assert struct.unpack_from('<2h',rom,0x4851A8)==(-1240,50)
assert struct.unpack_from('<2h',rom,0x4851B8)==(-640,31)
source=(Path.home()/'Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc').read_bytes()
assert sha(source)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
assert source[0x768001:0x768015].hex()=='f7441e4000750df7440680007506c7848c000100'
text=base.read_text(encoding='utf-8')
text=replace(text,"PINS={","PINS={\n 'bizhawk_probe_evolution_id14.lua':'DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B',")
text=replace(text,"tools/bizhawk_probe_evolution_id14.lua","tools/bizhawk_probe_evolution_id14_r2.lua")
text=replace(text,"env.RAM=ram;env.REGS=regs;env.HOOKS=hooks;env.CASE=case","env.RAM=ram;env.REGS=regs;env.HOOKS=hooks;env.CASE=case;env.SET_FRAME=function(n)frame=n end")
before="music_contact(keys,'battle',7);assert(keys.Right and not keys.Left)"
after=before+r'''
 RAM[cal+0x36]=0x800;RAM[p+4]=0;RAM[p+6]=0;SET_FRAME(200)
 music_contact(keys,'battle',7);assert(keys.A and contact_jump_until==220)
 for n=201,219 do SET_FRAME(n);music_contact(keys,'battle',7);assert(keys.A and contact_jump_until==220)end
 SET_FRAME(220);music_contact(keys,'battle',7);assert(not keys.A and contact_jump_until==220)
 RAM[p+6]=1;SET_FRAME(221);music_contact(keys,'battle',7);assert(not keys.A and contact_jump_until==220)
 RAM[p+6]=0;RAM[p+4]=3;SET_FRAME(222);music_contact(keys,'battle',7);assert(not keys.A)
 RAM[p+4]=0;SET_FRAME(223);music_contact(keys,'battle',7);assert(keys.A and contact_jump_until==243)
 RAM[cal+4]=8;SET_FRAME(224);music_contact(keys,'battle',7);assert(keys.A and contact_jump_until==243)
 SET_FRAME(243);music_contact(keys,'battle',7);assert(not keys.A)
 RAM[cal+4]=0x1008;SET_FRAME(244);music_contact(keys,'battle',7);assert(keys.A and contact_jump_until==264)
 RAM[p+0x11]=13;SET_FRAME(245);keys.A=false;music_contact(keys,'battle',7);assert(not keys.A)
 RAM[p+0x11]=14
'''
text=replace(text,before,after)
text=replace(text,"status='ID14_ORDINARY_CONTACT_AUTHOR_PASS'","status='ID14_HELD_JUMP_R2_AUTHOR_PASS',jump_hold_frames=20,minimum_release_frames=1,rearm_grounded_only=True,source_jump_contract_verified=True")
exec(compile(text,str(base),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve())})
