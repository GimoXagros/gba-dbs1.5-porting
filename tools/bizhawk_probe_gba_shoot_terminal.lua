-- One authorized stage11 boss HP1 intervention, actual lethal hit and native terminal exit.
-- CPU callbacks retain scalar evidence only; full captures run outside callbacks.
local args={}
for _,k in ipairs({"output","checkpoint_dir","probe_sha256","boss_authorization"})do args[k]=assert(userdata.get(k),k)end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$") and reference:match("^W:/build/[%w%-%_/]+$") and out~=reference)
assert(emu.getsystemid()=="GBA" and args.probe_sha256=="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC")
assert(args.boss_authorization=="user-approved-development-boss-once-per-stage","explicit one-shot boss approval required")
local P,Q,AUX=0x02011710,0x02011828,0x02011940
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},{"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local keys={A=false,B=false,Select=false,Start=false,Right=false,Left=false,Up=false,Down=false,R=false,L=false,Power=false}
local function release()for k in pairs(keys)do keys[k]=false end end
local function file(path)local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s end
local function write(name,s)local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(s));f:close()end
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x04000000 and a+n<=0x04000400 then d,o="System Bus",a
 elseif a>=0x06000000 and a+n<=0x06018000 then d,o="VRAM",a-0x06000000
 elseif a>=0x05000000 and a+n<=0x05000400 then d,o="PALRAM",a-0x05000000
 elseif a>=0x08000000 and a+n<=0x08800000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d)elseif n==2 then return memory.read_u16_le(o,d)else return memory.read_u32_le(o,d)end
end
local function w(a)return read(a,2)end
local function b(a)return read(a,1)end
local function pos(h)return h>0 and h<0x8000 end
local function signed(h)return h>=0x8000 and h-0x10000 or h end
local function header(a)return a>=0x02010000 and a<=0x02010000+51*0x118 and (a-0x02010000)%0x118==0 and w(a+0x10)&2~=0 end
local function task(a,cb)local p=read(a,4);return header(p) and read(p,4)==cb end
local function typed()
 return read(0x0300489C,4)==P and read(0x030048A0,4)==Q and read(0x03004D3C,4)==AUX
  and header(P-0x18) and header(Q-0x18) and header(AUX-0x18)
  and w(P+4)%16==0 and b(P+0x10)==0 and b(P+0x11)==0 and w(P+8)&0x100==0
  and w(Q+4)%16==3 and b(Q+0x10)==1 and b(Q+0x11)==15 and w(AUX+4)%16==6
  and read(P+0x14,4)==P and read(P+0x18,4)==Q and read(Q+0x14,4)==Q and read(Q+0x18,4)==P
  and read(Q+0x28,4)==AUX and read(AUX+0x28,4)==Q and read(AUX+0x18,4)==P
  and read(Q+0xF0,4)==0x085D0000 and read(Q+0xF4,4)==0x085D1000
  and read(AUX+0xF0,4)==0x085D029C and read(AUX+0xF4,4)==0x085D1100
end
local function live()
 return w(0x03002310)==7 and b(0x0300231E)==11 and w(0x03004502)==2 and b(0x03004529)&7==0
  and task(0x03004510,0x08374FF4) and task(0x03004514,0x083735BC)
end
local logs,ring,pending,seen,last={}, {}, {}, {}, {}
local outcome,pre,hit,scene,cleanup=nil,nil,nil,nil,nil
local consumed,root5,case5,fatal,irq_selected,irq_final,scroll_after=false,false,false,false,false,false,false
local serial,captures,irq_steps=0,0,0
local irq_cycle,irq_pending,scroll_pending=nil,nil,nil
local phases,guard_refusals={},{}
local upper_done,aux_done=false,false
local function actor(a)
 return string.format("actor=%08X cb=%08X kind=%X HP=%d XY=%04X,%04X prev=%04X,%04X flags=%04X,%04X held=%04X edge=%04X motion=%04X,%04X,%04X,%04X,%04X,%04X event=%X action=%X counter=%X,%X,%X links=%08X,%08X P1/P0=%08X,%08X",a,read(a,4),w(a+4)%16,w(a+0x64),w(a+0x34),w(a+0x36),w(a+0x38),w(a+0x3A),w(a+6),w(a+8),w(a+0x2C),w(a+0x2E),w(a+0x42),w(a+0x44),w(a+0x46),w(a+0x48),w(a+0x4A),w(a+0x4C),w(a+0xBA),w(a+0xA0),w(a+0x94),w(a+0x96),w(a+0x98),read(a+0x18,4),read(a+0x28,4),read(a+0xF0,4),read(a+0xF4,4))
end
local function state()
 return string.format("mode=%d stage=%d flags=%04X common=%04X control=%02X current=%08X last=%08X display=%08X input=%08X battle=%08X scene=%08X timer=%d camera=%d scene52=%04X",w(0x03002310),b(0x0300231E),w(0x0300450A),w(0x03004506),b(0x03004529),read(0x0300133C,4),read(0x03001344,4),read(0x03004518,4),read(read(0x03004510,4),4),read(read(0x03004514,4),4),scene or 0,scene and w(scene+0x18+0x50)or 0,w(0x0300451E),scene and w(scene+0x18+0x52)or 0)
end
local function log(kind,s,r)
 local line=string.format("core=%d kind=%s %s",emu.framecount(),kind,s or "")
 if r then local names={};for k in pairs(r)do names[#names+1]=k end;table.sort(names);for _,k in ipairs(names)do line=line..string.format(" %s=%08X",k,r[k])end end
 serial=serial+1;ring[(serial-1)%256+1]=line;logs[#logs+1]=line
end
local function queue(name,r)
 if seen[name]then return end;seen[name]=true
 pending[#pending+1]={name=name,core=emu.framecount()}
 log(name,state().." | "..actor(P).." | "..actor(Q).." | "..actor(AUX),r)
end
local function fail(name,r)
 if outcome and outcome~="native-terminal-mode8"then return end
 outcome="failure:"..name;queue(name,r)
 local recent={outcome,state()};for n=math.max(1,serial-255),serial do recent[#recent+1]=ring[(n-1)%256+1]end
 write("terminal-first-failure.txt",table.concat(recent,"\n").."\n")
end
local function need(ok,name,r)if not ok then fail(name,r);return false end;return true end
local function hook(a,name,fn)
 event.on_bus_exec(function()if not outcome then fn(emu.getregisters())end end,a,"shoot-terminal-"..name)
end
local function irq_state()
 local values={};for offset=0,12,2 do values[#values+1]=string.format("%04X",w(0x03004710+offset))end
 return string.format("state=%s slot=%08X prepared=%d/%08X copied=%d/%08X scroll=%08X tuple=%08X DISPCNT=%04X BG1CNT=%04X DISPSTAT=%04X VCOUNT=%d BG1HOFS=%04X BG1VOFS=%04X",table.concat(values,","),read(0x030012E0,4),read(0x03002474,4),read(0x03002478,4),read(0x03004574,4),read(0x03004578,4),read(0x030012B8,4),read(0x0300456C,4),w(0x04000000),w(0x0400000A),w(0x04000004),w(0x04000006),w(0x04000014),w(0x04000016))
end
-- Name the native guard's first refusal without changing any predicate or guest field.
local function stationary_reason()
 if not task(0x03004510,0x08374FAC)or not task(0x03004514,0x0837354C)then return "terminal-controller"end
 if read(0x0300489C,4)~=P or read(0x030048A0,4)~=Q or read(0x03004D3C,4)~=AUX or not header(P-0x18)or not header(Q-0x18)or not header(AUX-0x18)then return "actor-owner"end
 if read(P,4)~=0x0835620C or read(Q,4)~=0x085BF200 or read(AUX,4)~=0x085BF600 then return "stationary-callbacks"end
 if w(P+4)%16~=0 or b(P+0x11)~=0 or w(P+6)&3~=0 or w(P+8)&0x100~=0 then return "base-grounded"end
 for _,a in ipairs({0x2C,0x2E,0x42,0x44,0x46,0x48,0x4A,0x4C})do if w(P+a)~=0 then return "player-field-"..string.format("%X",a)end end
 if w(P+0x34)~=w(P+0x38)or w(P+0x36)~=w(P+0x3A)then return "previous-position"end
 for _,r in ipairs({{P,0x080D7A58,0x080D45B8,0},{Q,0x085D1000,0x085D0000,1},{AUX,0x085D1100,0x085D029C,0}})do
  if read(r[1]+0xF4,4)~=r[2]or read(r[1]+0xF0,4)~=r[3]or w(r[1]+0xBA)~=r[4]then return "presentation-owner"end
 end
 if read(Q+0x28,4)~=AUX or read(AUX+0x18,4)~=Q then return "native-guard-aux18-not-upper"end
 if w(0x0300482A)~=1 or read(0x03004830,4)~=P+0xAC then return "FIRST-only-render-queue"end
 for _,a in ipairs({0x03002354,0x03002356,0x030023A4,0x030023A6})do if w(a)~=0 then return "BG-velocity"end end
 if w(0x04000000)&7~=0 or w(0x0400000A)&0xDFCC~=0x1E00 then return "hardware-BG-mapping"end
 for a=0,28,4 do if read(0x06000000+a,4)~=0 then return "blank-tile"end end
 if w(0x0300450A)&0x800~=0 then return nil end
 local k=w(0x03004712);if k<1 or k>143 then return "visible-counter"end
 local checked={}
 for y=k+37,159 do
  local row=((b(0x03004718)-29+y)&255)>>3
  if not checked[row]then
   checked[row]=true
   for x=0,31 do if w(0x0600F000+row*64+x*2)~=0 then return "visible-map-row-"..row end end
  end
 end
 return nil
end
local function scene_owner(r)
 return need(scene and read(0x0300133C,4)==scene and header(scene),"terminal-scene-owner",r)
end
local function install()
 hook(0x08375140,"input-copy",function(r)
  if not hit and r.R4==P then
   need(w(P+0x2C)==w(0x03001302)and w(P+0x2E)==w(0x03001306),"input-copy",r)
   need(w(P+0x2C)&0xC0==(keys.B and 0x80 or 0),"input-map",r)
  end
 end)
 hook(0x0836E5E4,"lethal-pre",function(r)
  if r.R4~=P or r.R5~=Q then return end
  if not need(consumed and not hit and typed()and live()and pos(w(P+0x64)),"lethal-owner",r)then return end
  local after=r.R8&0xFFFF
  if not need(w(Q+0x64)==1 and r.R0>0 and after==(1-r.R0)&0xFFFF and (after==0 or after>=0x8000),"lethal-math",r)then return end
  pre={core=emu.framecount(),after=after,damage=r.R0};log("lethal-pre",string.format("before=1 damage=%d computed=%04X",r.R0,after),r)
 end)
 hook(0x0836E5E8,"lethal-post",function(r)
  if pre and r.R4==P and r.R5==Q then
   if need(pre.core==emu.framecount()and w(Q+0x64)==pre.after and pos(w(P+0x64)),"lethal-store",r)then hit=pre;pre=nil;queue("lethal-hit",r)end
  end
 end)
 hook(0x0836E5EC,"fatal-branch",function(r)
  if hit and r.R4==P and r.R5==Q then hit.branch=true;log("fatal-branch","",r)end
 end)
 hook(0x085CD960,"fatal-adapter",function(r)
  if hit and r.R4==P and r.R5==Q then hit.adapter=need(hit.branch==true,"fatal-adapter-without-branch",r);log("fatal-adapter","",r)end
 end)
 hook(0x0836E604,"fatal-pair",function(r)
  if not hit or not hit.adapter then return end
  fatal=need(r.R4==P and r.R5==AUX and r.R0==Q and read(Q,4)==0x085BDD00 and read(AUX,4)==0x085BF204,"fatal-pair-bindings",r)
  if fatal then queue("fatal-pair",r)end
 end)
 hook(0x08373688,"root4",function(r)fail("player-loss-root4",r)end)
 hook(0x083736B0,"root5",function(r)
  root5=need(hit and fatal and pos(w(P+0x64))and not pos(w(Q+0x64))and b(0x0300231E)==11,"healthy-root5",r)
  if root5 then queue("root5",r)end
 end)
 hook(0x0833FD08,"case5",function(r)
  if root5 then case5=need(r.R8==0x086FC300 and b(0x0300231E)==11,"terminal-case5-argument",r);queue("case5",r)end
 end)
 hook(0x086FC324,"terminal-route",function(r)if case5 then queue("terminal-route",r)end end)
 hook(0x085CD000,"terminal-entry",function(r)
  local current=read(0x0300133C,4)
  if not need(case5 and root5 and fatal and header(current)and read(current+4,4)==0xFF0 and (not scene or scene==current),"terminal-allocation-owner",r)then return end
  scene=current;phases[0x085CD000]=true;queue("terminal-entry",r)
 end)
 local phase_addresses={0x085CD0A0,0x085CD120,0x085CD270,0x085CD2B0,0x085CD340,0x085CD3A0,0x085CD420,0x085CD4B0,0x085CD510,0x085CD550,0x085CD5E0,0x085CD640,0x085CD6A0,0x085CD710,0x085CD740}
 for _,a in ipairs(phase_addresses)do
  hook(a,"phase-"..a,function(r)
   if not scene_owner(r)then return end
   phases[a]=true;queue(string.format("phase-%X",a),r)
  end)
 end
 hook(0x085CD314,"camera-call",function(r)
  if scene_owner(r)and need(r.R1==w(0x0300451E),"camera-snapshot",r)then queue("camera-capture",r)end
 end)
 hook(0x086FE900,"camera-adapter",function(r)if scene_owner(r)then queue("camera-adapter",r)end end)
 hook(0x085CD318,"camera-return",function(r)
  if scene_owner(r)then log("camera-return",string.format("scene52=%04X camera=%d",w(scene+0x18+0x52),w(0x0300451E)),r)end
 end)
 for _,a in ipairs({0x085BDD00,0x085BE000,0x085BE200,0x085BE600,0x085BEA00,0x085BEE00,0x085BF200,0x085BF204,0x085BF400,0x085BF600,0x085CDA40,0x085CDA50,0x085CDA60,0x085CDA70})do
  hook(a,"actor-phase-"..a,function(r)
   if not hit then return end
   local aux=(a==0x085BF204 or a==0x085BF400 or a==0x085BF600 or a==0x085CDA70)
   if not need(r.R4==(aux and AUX or Q),"fatal-actor-owner",r)then return end
   if a==0x085BF200 then upper_done=true elseif a==0x085BF600 then aux_done=true end
   queue(string.format("actor-%X",a),r)
  end)
 end
 hook(0x086FF9C0,"guard-entry",function(r)
  if not scene then return end
  local why=stationary_reason()
  if why and not guard_refusals[why]then guard_refusals[why]=true;log("guard-refusal",why.." "..irq_state().." "..actor(P).." "..actor(Q).." "..actor(AUX),r)end
 end)
 hook(0x086FF698,"guard-return",function(r)
  if scene and r.R0~=0 then log("guard-accepted",irq_state(),r)end
 end)
 hook(0x086FF6A8,"queue-substitution",function(r)
  if not scene then return end
  local current=read(0x0300133C,4);local why=stationary_reason()
  if not need(not why and header(current)and current==read(0x03001344,4)and current==read(0x03004518,4)and read(current,4)==0x08352268 and read(current+4,4)==0xFFFFF000 and read(0x03004574,4)==1 and read(0x03004578,4)==0x08587200 and r.R0==0x03004574 and r.R1==0x086FF6B4,"accepted-queue-contract",r)then return end
  irq_selected=true;queue("irq-queue-selected",r);log("queue-substitution",irq_state(),r)
 end)
 hook(0x086FF6E8,"guarded-display",function(r)
  if scene then
   if need(irq_selected and w(0x03002310)==7 and b(0x0300231E)==11 and w(0x0300450A)&0x400~=0 and r.R0==0x086FFE10,"guarded-display-owner",r)then
    if not irq_final then irq_cycle={matches=0};irq_pending=nil;irq_steps=0 end
    queue("guarded-display",r)
   end
  end
 end)
 hook(0x086FFE10,"irq-entry",function(r)
  if not scene or irq_final then return end
  if need(irq_selected and read(0x030012E0,4)==0x086FFE10,"actual-IRQ-slot",r)then queue("irq-first-entry",r);log("irq-entry",irq_state(),r)end
 end)
 hook(0x086FFE48,"irq-compare",function(r)
  if scene and not irq_final then
   local offsets={0,2,4,7,10,13,17,21};local index=w(0x03004716)
   if need(index<8 and r.R4==0x03004710 and r.R5==index and r.R6==offsets[index+1]and r.R1==((b(0x03004714)+offsets[index+1])&255),"IRQ-compare-owner",r)then log("irq-compare",irq_state(),r)end
  end
 end)
 hook(0x086FFE50,"irq-match",function(r)
  if scene and not irq_final then
   local index=w(0x03004716)
   if need(irq_cycle and index==irq_cycle.matches and index<8 and r.R4==0x03004710 and r.R5==index and r.R0==r.R1,"IRQ-match-sequence",r)then
    irq_pending={index=index,counter=w(0x03004714)};log("irq-match",irq_state(),r)
   end
  end
 end)
 hook(0x086FFE74,"irq-match-stored",function(r)
  if scene and not irq_final then
   if need(irq_pending and w(0x03004716)==irq_pending.index+1 and r.R5==irq_pending.index+1 and w(0x03004714)==(irq_pending.counter+1)&0xFFFF,"IRQ-counter-store",r)then
    irq_cycle.matches=irq_cycle.matches+1;irq_steps=irq_cycle.matches;irq_pending=nil;log("irq-match-stored",irq_state(),r)
   end
  end
 end)
 hook(0x086FFE84,"irq-final-install",function(r)
  if scene and not irq_final then
   if need(irq_steps==8 and w(0x03004716)==8 and r.R0==0x030012E0 and r.R1==0x086FFEBC,"IRQ-final-store",r)then queue("irq-final-install",r)end
  end
 end)
 hook(0x086FFEBC,"irq-final-call",function(r)
  if scene and not irq_final then
   if need(irq_steps==8 and read(0x030012E0,4)==0x086FFEBC,"genuine-final-IRQ-call",r)then irq_final=true;queue("irq-final-called",r);log("irq-final",irq_state(),r)end
  end
 end)
 hook(0x085E7434,"next-scroll-overwrite",function(r)
  if irq_final and not scroll_after and need(r.R5==0x0300456C,"next-scroll-owner",r)then scroll_pending=b(0x0300456E);log("next-display-scroll-pre",irq_state(),r)end
 end)
 hook(0x085E743C,"next-scroll-stored",function(r)
  if scroll_pending then
   if need(b(0x030012B8)==scroll_pending and w(0x04000014)==(scroll_pending-8)&0xFFFF,"next-scroll-store",r)then
    scroll_after=true;scroll_pending=nil;queue("next-display-scroll",r);log("next-display-scroll-post",irq_state(),r)
   end
  end
 end)
 hook(0x08340C54,"cleanup-entry",function(r)
  if not need(scene and phases[0x085CD740]and read(0x0300133C,4)==scene,"cleanup-entry-owner",r)then return end
  queue("cleanup-entry",r)
 end)
 hook(0x08340CA8,"cleanup-request",function(r)
  if not scene then return end
  if need(seen["cleanup-entry"]and not header(scene)and w(0x03002314)==1 and w(0x03002316)==0 and w(0x03002318)==0 and b(0x0300475E)==1 and b(0x0300475F)==0 and b(0x0300452A)==0,"cleanup-retirement-triplet",r)then
   cleanup={core=emu.framecount(),mode=w(0x03002310)};queue("cleanup-request",r)
  end
 end)
 local function producer(a,base,count)
  hook(a,"producer-"..a,function(r)
   if cleanup then return end
   local i=(r.R1-base)/20;local owner=read(r.R1,4)
   local detail=string.format("pc=%08X slot=%08X type=%X rectangle=%08X source_type=%X owner=%08X event=%X cmd=%08X A=%08X B=%08X",a,r.R1,r.R0,r.R4,w(r.R4),owner,w(owner+0xBA),read(owner+0xD0,4),read(owner+0xD4,4),read(owner+0xD8,4))
   last[r.R1]={core=emu.framecount(),type=r.R0,detail=detail}
   if r.R0<0 or r.R0>0x1B or i<0 or i>=12 or i%1~=0 or i~=b(count)then log("producer",detail,r);fail("invalid-producer",r)end
  end)
 end
 producer(0x08353C70,0x030049B8,0x03004C4E);producer(0x08353D24,0x030048C8,0x03004C4D);producer(0x083776E4,0x030048C8,0x03004C4D)
 hook(0x0836E370,"overlap",function(r)
  local origin=last[r.R4]
  if r.R0<0 or r.R0>0x1B or (origin and origin.core==emu.framecount()and origin.type~=r.R0)then log("overlap",origin and origin.detail or "unobserved",r);fail("invalid-overlap",r)end
 end)
 hook(0x0836EB58,"scratch",function(r)if w(0x03004D20)>0x1B then fail("invalid-scratch",r)end end)
 hook(0x0836EBA4,"dispatch",function(r)if r.R1<0 or r.R1>34 or r.R1%2~=0 or r.R8~=0x0836EBA8 or r.R9~=read(0x0836EBA8+r.R1*2,4)then fail("invalid-dispatch",r)end end)
end
local function dump(name,events)
 log("capture",string.format("name=%s export_core=%d memory=outer-frame-boundary events=%s",name,emu.framecount(),events))
 for _,r in ipairs(regions)do write(name.."-"..r[1]..".bin",memory.read_bytes_as_binary_string(0,r[3],r[2]))end
 write(name.."-display.bin",memory.read_bytes_as_binary_string(0x04000000,0x60,"System Bus"))
 client.screenshot(out.."/"..name..".png")
 assert(savestate.save(out.."/"..name..".State",true)==true,"capture save failed")
 write(name..".txt",string.format("export_core=%d memory=outer-frame-boundary %s\n",emu.framecount(),events))
end
local function flush()
 if #pending>0 then
  captures=captures+1;local names={};for _,e in ipairs(pending)do names[#names+1]=e.name.."@"..e.core end
  dump(string.format("%02d-%s",captures,pending[1].name),table.concat(names,","));pending={}
 end
 if #logs>0 then local f=assert(io.open(out.."/terminal-trace.txt","a"));assert(f:write(table.concat(logs,"\n").."\n"));f:close();logs={}end
end
local function authorize_hp1()
 assert(not consumed and typed()and live()and w(Q+0x64)==37 and w(P+0x64)==4,"single approved stage11 HP write")
 local left,right,hp,score=w(Q+0x62),w(Q+0x66),w(P+0x64),w(P+0x66)
 consumed=true
 local ledger=string.format("core=%d actor=%08X address=%08X bytes=2 before=37 requested=1 P1HP=%d P1score=%d left=%d right=%d attempt_consumed=true",emu.framecount(),Q,Q+0x64,hp,score,left,right)
 write("terminal-write-ledger.txt",ledger.." verified=false\n")
 memory.write_u16_le(Q-0x02000000+0x64,1,"EWRAM")
 assert(w(Q+0x64)==1 and w(Q+0x62)==left and w(Q+0x66)==right and w(P+0x64)==hp and w(P+0x66)==score and typed()and live(),"HP1 word and neighbor/player invariants")
 write("terminal-write-ledger.txt",ledger.." after=1 verified=true\n")
 queue("authorized-hp1");flush()
end
local function run()
 assert(file(reference.."/healthy-activation.txt"):match("^core=68927 input_relative=68926 stage7_consumed=true "))
 assert(file(reference.."/healthy-activation.State"):sub(1,4)=="PK\003\004")
 assert(savestate.load(reference.."/healthy-activation.State",true)==true,"checkpoint load failed")
 userdata.clear();for k,v in pairs(args)do userdata.set(k,v);assert(userdata.get(k)==v)end
 local function restored()
  assert(emu.framecount()==68927,"restored frame")
  for _,r in ipairs(regions)do assert(memory.getmemorydomainsize(r[2])==r[3]);assert(memory.read_bytes_as_binary_string(0,r[3],r[2])==file(reference.."/13-healthy-activation-"..r[1]..".bin"),"restored "..r[1])end
 end
 restored();assert(savestate.save(out.."/restored.State",true)==true);restored()
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))
 assert(typed()and live()and w(P+0x64)==4 and w(Q+0x64)==37 and w(0x0300450A)==6,"genuine healthy owners")
 assert(w(P+0x2C)==0 and w(P+0x2E)==0 and w(0x03001302)==0 and w(0x03001306)==0,"released checkpoint")
 dump("00-before","healthy68927")
 install()
 for frame=1,3000 do
  release()
  if not hit then
   local cb=read(P,4)
   local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4)and w(P+6)&1==0 and w(P+0x76)==0
   if ready then
    if w(P+0xB4)&0x4000==0 then keys.Right=true
    else
     local dx=signed(w(Q+0x34))-signed(w(P+0x34));local dy=signed(w(Q+0x36))-signed(w(P+0x36));local ev=w(Q+0xBA)
     keys.B=w(P+0x2C)&0x80==0 and (ev==1 or ev==4 or ev==5)and dx>=96 and dx<=384 and dy>=128 and dy<=256
    end
   end
   if keys.B and not consumed then authorize_hp1()end
   log("input",string.format("relative=%d Right=%s B=%s",frame,tostring(keys.Right),tostring(keys.B)))
  end
  joypad.set(keys);emu.frameadvance();assert(emu.framecount()==68927+frame,"single-frame advance")
  if not hit or frame%30==0 then log("frame",state().." | "..actor(P).." | "..actor(Q).." | "..actor(AUX))end
  if not scene and not pos(w(P+0x64))then fail("player-death-before-terminal")end
  if not hit and (not typed()or not live())then fail("live-hit-owner-lost")end
  if hit and not fatal then fail("lethal-did-not-reach-fatal-adapter")end
  if not cleanup and w(0x03002310)~=7 then fail("mode-exit-before-cleanup")end
  if cleanup and w(0x03002310)==8 and not outcome then
   local required=hit and fatal and root5 and case5 and scene and upper_done and aux_done and irq_selected and irq_final and scroll_after
   for _,a in ipairs({0x085CD000,0x085CD0A0,0x085CD120,0x085CD2B0,0x085CD340,0x085CD3A0,0x085CD420,0x085CD4B0,0x085CD510,0x085CD550,0x085CD5E0,0x085CD640,0x085CD6A0,0x085CD710,0x085CD740})do required=required and phases[a]end
   if need(required and cleanup.mode~=8 and emu.framecount()>=cleanup.core,"mode8-missing-required-native-chain")then queue("native-mode8");outcome="native-terminal-mode8"end
  end
  flush();if outcome then break end
 end
 if not outcome then fail("bounded-no-completion");flush()end
 write("shoot-terminal-done.txt",outcome.."\n")
end
local ok,err=pcall(run)
release();joypad.set(keys)
if not ok then
 write("terminal-error.txt",tostring(err));pcall(function()fail("script-error");flush()end)
 write("shoot-terminal-done.txt","failure:script-error\n")
end
client.exit()
