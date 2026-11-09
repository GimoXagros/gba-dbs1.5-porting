-- One ordinary-input nonlethal Shoot hit and its eight eligible flash updates.
-- CPU callbacks retain scalar evidence only; full captures run outside callbacks.
local args={}
for _,k in ipairs({"output","checkpoint_dir","probe_sha256"})do args[k]=assert(userdata.get(k),k)end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$") and reference:match("^W:/build/[%w%-%_/]+$") and out~=reference)
assert(emu.getsystemid()=="GBA" and args.probe_sha256=="6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331")
local P,Q,AUX=0x02011710,0x02011828,0x02011940
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},{"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local keys={A=false,B=false,Select=false,Start=false,Right=false,Left=false,Up=false,Down=false,R=false,L=false}
local function release()for k in pairs(keys)do keys[k]=false end end
local function file(path)local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s end
local function write(name,s)local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(s));f:close()end
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
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
local rows,pending,seen,last={}, {}, {}, {}
local outcome,hit,pre,adapter,expiry,updates=nil,nil,nil,false,false,0
local function actor(a)
 return string.format("actor=%08X cb=%08X kind=%X hp=%d xy=%d,%d velocity=%d,%d accel=%d,%d held=%04X edge=%04X facing=%04X action=%04X event=%04X cmd_index=%X cmd_count=%X command=%08X A=%08X B=%08X timer=%d freeze=%d",a,read(a,4),w(a+4)%16,w(a+0x64),signed(w(a+0x34)),signed(w(a+0x36)),signed(w(a+0x42)),signed(w(a+0x44)),signed(w(a+0x46)),signed(w(a+0x48)),w(a+0x2C),w(a+0x2E),w(a+0xB4),w(a+0xA0),w(a+0xBA),w(a+0xC6),w(a+0xC8),read(a+0xD0,4),read(a+0xD4,4),read(a+0xD8,4),w(a+0x74),w(a+0x76))
end
local function log(kind,s,r)
 rows[#rows+1]=string.format("core=%d kind=%s %s",emu.framecount(),kind,s or "")
 if r then local names={};for k in pairs(r)do names[#names+1]=k end;table.sort(names);local rr={};for _,k in ipairs(names)do rr[#rr+1]=string.format("%s=%08X",k,r[k])end;rows[#rows+1]="regs "..table.concat(rr," ")end
end
local function queue(name,r)
 if seen[name]then return end;seen[name]=true
 pending[#pending+1]={name=name,core=emu.framecount()};log(name,actor(P).." | "..actor(Q).." | "..actor(AUX),r)
end
local function fail(name,r)
 if outcome and outcome~="positive-hit-flash-expired" then return end;outcome="failure:"..name;queue(name,r)
 write("positive-hit-first-failure.txt",outcome.."\n"..table.concat(rows,"\n").."\n")
end
local function need(ok,name,r)if not ok then fail(name,r);return false end;return true end
local function palette(raw)
 for i=0,14 do if w(0x05000222+2*i)~=w(raw+8+2*i)then return false end end
 return true
end
local function hook(a,name,fn)event.on_bus_exec(function()if not outcome then fn(emu.getregisters())end end,a,"shoot-positive-"..name)end
local function install()
 hook(0x08375140,"input-stored",function(r)
  if r.R4==P then
   need(w(P+0x2C)==w(0x03001302) and w(P+0x2E)==w(0x03001306),"input-copy-mismatch",r)
   local ab=(keys.A and 0x40 or 0)|(keys.B and 0x80 or 0)
   need(w(P+0x2C)&0xC0==ab,"input-button-map",r)
  end
 end)
 hook(0x0836E5E4,"damage-pre",function(r)
  if r.R4~=P or r.R5~=Q then return end
  if not need(typed() and live() and pos(w(P+0x64)),"hit-owner-refusal",r)then return end
  if hit then fail("second-hit-before-expiry",r);return end
  local before,damage,after=w(Q+0x64),r.R0,r.R8&0xFFFF
  if not need(pos(before) and damage>0 and before>damage and after==before-damage and pos(after),"nonpositive-hit",r)then return end
  pre={before=before,damage=damage,after=after,core=emu.framecount()};log("damage-pre",string.format("before=%d damage=%d computed=%d",before,damage,after),r)
 end)
 hook(0x0836E5E8,"damage-post",function(r)
  if not pre or r.R4~=P or r.R5~=Q then return end
  if need(emu.framecount()==pre.core and w(Q+0x64)==pre.after,"damage-store-mismatch",r)then hit=pre;pre=nil;queue("first-positive-hit",r)end
 end)
 hook(0x0836E634,"nonfatal-hook",function(r)
  if hit and r.R4==P and r.R5==Q then hit.hook=true;log("nonfatal-hook","",r)end
 end)
 hook(0x085CD9A0,"adapter-entry",function(r)
  if hit and r.R4==P and r.R5==Q then adapter=need(hit.hook==true,"adapter-without-hook",r);log("adapter-entry","",r)end
 end)
 hook(0x085CDA20,"flash-complete",function(r)
  if not adapter or r.R4~=P or r.R5~=Q then return end
  if not need(w(Q+0x74)==8 and palette(0x085C0B00),"flash-palette-or-timer",r)then return end
  if not need(w(0x0300450A)&0x4030==0,"unexpected-flash-mask",r)then return end
  for i=0,23 do if not need(w(0x05000000+i*0x20)==0x1F,"red-zero-entry",r)then return end end
  hit.flash=true;queue("flash-eight",r)
 end)
 hook(0x08586C7C,"timer-store",function(r)
  if not hit or not hit.flash or r.R5~=Q then return end
  updates=updates+1
  if not need(updates<=8 and w(Q+0x74)==9-updates and r.R8==8-updates,"timer-update-sequence",r)then return end
  log("timer-store",string.format("update=%d before=%d computed=%d",updates,w(Q+0x74),r.R8),r)
 end)
 hook(0x08587000,"expiry-entry",function(r)
  if not hit or not hit.flash or r.R4~=Q then return end
  expiry=need(updates==8 and w(Q+0x74)==0 and r.R14==0x08586C90,"expiry-owner",r);log("expiry-entry","",r)
 end)
 hook(0x08587068,"expiry-return",function(r)
  if not expiry or r.R4~=Q then return end
  local raw=w(Q+0x64)<=w(Q+0x6A) and 0x08587150 or w(Q+0x64)<=w(Q+0x68) and 0x08587128 or 0x08587100
  if need(typed() and live() and pos(w(P+0x64)) and pos(w(Q+0x64)) and w(Q+0x74)==0 and palette(raw),"expiry-palette-or-owner",r)then queue("flash-expired",r);outcome="positive-hit-flash-expired"end
 end)
 local function producer(a,base,count)
  hook(a,"producer-"..a,function(r)
   local i=(r.R1-base)/20;local actorptr=read(r.R1,4)
   local detail=string.format("pc=%08X dst=%08X index=%g count=%d type=%X B=%08X source_type=%X %s",a,r.R1,i,b(count),r.R0,r.R4,w(r.R4),actor(actorptr))
   last[r.R1]={type=r.R0,core=emu.framecount(),detail=detail}
   if r.R0>0x1B or r.R0<0 then log("producer",detail,r);fail("first-invalid-producer",r)
   elseif i<0 or i>=12 or i%1~=0 or i~=b(count)then log("producer",detail,r);fail("producer-geometry",r)end
  end)
 end
 producer(0x08353C70,0x030049B8,0x03004C4E);producer(0x08353D24,0x030048C8,0x03004C4D);producer(0x083776E4,0x030048C8,0x03004C4D)
 hook(0x0836E370,"overlap",function(r)
  local origin=last[r.R4]
  if r.R0>0x1B or r.R0<0 or (origin and origin.core==emu.framecount() and origin.type~=r.R0)then log("overlap",origin and origin.detail or "origin-unobserved",r);fail("invalid-overlap",r)end
 end)
 hook(0x0836EB58,"scratch-consumer",function(r)if w(0x03004D20)>0x1B then fail("invalid-scratch-type",r)end end)
 hook(0x0836EBA4,"dispatch",function(r)
  if r.R1<0 or r.R1>34 or r.R1%2~=0 or r.R8~=0x0836EBA8 or r.R9~=read(0x0836EBA8+r.R1*2,4)then fail("invalid-dispatch-target",r)end
 end)
 hook(0x08373688,"root4",function(r)fail("player-loss",r)end)
end
local function capture(name,observed)
 log("capture",string.format("name=%s observed_core=%d export_core=%d memory=outer-frame-boundary",name,observed,emu.framecount()))
 for _,r in ipairs(regions)do write(name.."-"..r[1]..".bin",memory.read_bytes_as_binary_string(0,r[3],r[2]))end
 client.screenshot(out.."/"..name..".png")
 assert(savestate.save(out.."/"..name..".State",true)==true,"capture save failed")
end
local function flush()
 for _,e in ipairs(pending)do capture(e.name,e.core)end;pending={}
 write("positive-hit-trace.txt",table.concat(rows,"\n").."\n")
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
 assert(typed() and live() and w(P+0x64)==4 and w(Q+0x64)==37 and w(0x0300450A)==6,"genuine healthy owners")
 assert(w(P+0x2C)==0 and w(P+0x2E)==0 and w(0x03001302)==0 and w(0x03001306)==0,"released checkpoint")
 capture("00-before",68927);install()
 for frame=1,1200 do
  release()
  if not hit then
   -- Neutral jump, followed by repeated separate attack edges; no Up/Down variants.
   keys.A=(frame-1)%60==0;keys.B=frame>=7 and (frame-7)%12==0
   local dx=signed(w(Q+0x34))-signed(w(P+0x34))
   if frame>6 and math.abs(dx)>0x180 then keys.Right=dx>0;keys.Left=dx<0 end
  end
  log("input",string.format("relative=%d A=%s B=%s Left=%s Right=%s",frame,tostring(keys.A),tostring(keys.B),tostring(keys.Left),tostring(keys.Right)))
  joypad.set(keys);emu.frameadvance();assert(emu.framecount()==68927+frame,"single-frame advance")
  log("frame",actor(P).." | "..actor(Q).." | "..actor(AUX))
  if not pos(w(P+0x64))then fail("player-death")end
  if not typed() or not live()then fail("live-owner-lost")end
  if hit and not hit.flash and not outcome then fail("hit-did-not-complete-adapter")end
  flush();if outcome then break end
 end
 if not outcome then fail("bounded-no-completion");flush()end
 write("shoot-positive-hit-done.txt",outcome.."\nupdates="..updates.."\n")
end
local ok,err=pcall(run)
release();joypad.set(keys)
if not ok then write("positive-hit-error.txt",tostring(err));write("positive-hit-trace.txt",table.concat(rows,"\n").."\n");write("shoot-positive-hit-done.txt","failure:script-error\n")end
client.exit()
