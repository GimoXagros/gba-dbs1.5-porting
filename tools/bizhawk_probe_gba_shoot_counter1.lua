-- Resume one genuine terminal checkpoint; observe natural counter1 with neutral input.
local args={}
for _,k in ipairs({"output","checkpoint_dir","probe_sha256"})do args[k]=assert(userdata.get(k),k)end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$")and reference:match("^W:/build/[%w%-%_/]+$")and out~=reference)
assert(emu.getsystemid()=="GBA"and args.probe_sha256=="280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7")
local P,Q,AUX,S,D,IRQ,FINAL=0x02011710,0x02011828,0x02011940,0x020121E8,0x020120D0,0x086FFE10,0x086FFEBC
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},{"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local keys={A=false,B=false,Select=false,Start=false,Right=false,Left=false,Up=false,Down=false,R=false,L=false,Power=false}
local function file(path)local f=assert(io.open(path,"rb"));local b=assert(f:read("*a"));f:close();return b end
local function write(name,b)local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(b));f:close()end
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x04000000 and a+n<=0x04000400 then d,o="System Bus",a
 else error("unapproved scalar address")end
 if n==1 then return memory.read_u8(o,d)elseif n==2 then return memory.read_u16_le(o,d)else assert(n==4);return memory.read_u32_le(o,d)end
end
local function w(a)return read(a,2)end
local function b(a)return read(a,1)end
local function header(a)return a>=0x02010000 and a<=0x02010000+51*0x118 and(a-0x02010000)%0x118==0 and w(a+0x10)&2~=0 end
local function owner()
 return w(0x03002310)==7 and b(0x0300231E)==11 and header(S)and read(S,4)==0x085CD510
  and read(0x0300489C,4)==P and read(0x030048A0,4)==Q and read(0x03004D3C,4)==AUX
  and header(P-0x18)and header(Q-0x18)and header(AUX-0x18)
  and read(P,4)==0x0835620C and read(Q,4)==0x085BF200 and read(AUX,4)==0x085BF600
  and read(Q+0x28,4)==AUX and read(AUX+0x18,4)==P and read(AUX+0x28,4)==Q
  and read(0x0300133C,4)==D and read(0x03001344,4)==D and read(0x03004518,4)==D
  and header(D)and read(D,4)==0x08352268 and read(D+4,4)==0xFFFFF000
end
local rows,outcome={},nil
local display,target,compared,pending=nil,nil,nil,nil
local matches,ignored,first_entry,first_picture=0,0,false,false
local installed=false
local function state()
 return string.format("base=%04X counter=%04X index=%04X slot=%08X DISPSTAT=%04X VCOUNT=%d BG1CNT=%04X mode=%d stage=%d scene=%08X",w(0x03004712),w(0x03004714),w(0x03004716),read(0x030012E0,4),w(0x04000004),w(0x04000006),w(0x0400000A),w(0x03002310),b(0x0300231E),read(S,4))
end
local function log(kind,detail,r)
 if #rows>=100 then outcome="failure:scalar-log-bound";return end
 local line=string.format("core=%d kind=%s %s %s",emu.framecount(),kind,detail or "",state())
 if r then for i=0,15 do line=line..string.format(" R%d=%08X",i,r["R"..i]or 0)end end
 rows[#rows+1]=line
end
local function fail(reason,r)if not outcome then log("failure",reason,r);outcome="failure:"..reason end end
local function need(ok,reason,r)if not ok then fail(reason,r);return false end;return true end
local function hook(a,label,fn)event.on_bus_exec(function()if not outcome then fn(emu.getregisters())end end,a,"shoot-counter1-"..label)end
local function install()
 hook(0x086FF75C,"display-success",function(r)
  if target then return end
  if need(owner()and w(0x0300450A)&0x400~=0 and r.R0==IRQ and r.R14==0x086FF6EC,"display-owner",r)then
   display={core=emu.framecount(),state=state(),PC=r.R15,LR=r.R14}
  end
 end)
 hook(0x085E74D8,"initialized",function(r)
  if target or not display then return end
  if w(0x03004714)~=1 or w(0x03004716)~=0 then return end
  if not need(owner()and display.core==emu.framecount()and r.R5==0x03004710 and read(0x030012E0,4)==IRQ and w(0x03004712)==0,"counter1-initialization-owner",r)then return end
  target={core=emu.framecount(),display_core=display.core,first_compare=false}
  log("display-success",string.format("observed_core=%d observed_PC=%08X observed_LR=%08X observed_state={%s}",display.core,display.PC,display.LR,display.state))
  log("counter1-initialized","",r)
  need(w(0x04000006)<=8,"counter1-initialization-late",r)
 end)
 hook(IRQ,"IRQ-entry",function(r)
  if not target then ignored=ignored+1;return end
  if not first_entry then first_entry=true;log("first-IRQ-entry","",r)end
 end)
 hook(0x086FFE48,"compare",function(r)
  if not target then ignored=ignored+1;return end
  local offsets={0,2,4,7,10,13,17,21};local index=w(0x03004716)
  if not need(index==matches and index<8 and r.R4==0x03004710 and r.R5==index and r.R6==offsets[index+1]and w(0x03004714)==1+index and read(0x030012E0,4)==IRQ,"compare-owner",r)then return end
  local programmed=w(0x04000004)>>8
  if not need(r.R0==(programmed-8)&255 and r.R1==1+index+offsets[index+1],"compare-operands",r)then return end
  if not target.first_compare then
   target.first_compare=true;target.compare_core=emu.framecount();target.VCOUNT=w(0x04000006);target.line=r.R0
   if not need(index==0 and target.compare_core==target.core and r.R0<=1 and target.VCOUNT<=9,"first-deadline-late",r)then return end
  end
  compared={core=emu.framecount(),index=index,counter=w(0x03004714),line=r.R0,target=r.R1}
  log("IRQ-compare","",r)
  need(r.R0<=r.R1,"deadline-late",r)
 end)
 hook(0x086FFE50,"match",function(r)
  if not target then ignored=ignored+1;return end
  if not need(compared and target.first_compare and not pending and compared.core==emu.framecount()and compared.index==matches and r.R5==matches and r.R0==r.R1 and r.R0==compared.line and r.R1==compared.target,"missing-or-wrong-first-compare",r)then return end
  pending=compared;log("IRQ-match","",r)
 end)
 hook(0x086FFE74,"stored",function(r)
  if not target then ignored=ignored+1;return end
  if not need(pending and pending.index==matches and w(0x03004714)==pending.counter+1 and w(0x03004716)==matches+1 and r.R5==matches+1,"counter-store",r)then return end
  matches=matches+1;pending=nil;compared=nil;log("IRQ-match-stored","",r)
 end)
 hook(0x086FFE84,"final-install",function(r)
  if not target then ignored=ignored+1;return end
  if need(matches==8 and w(0x03004716)==8 and w(0x03004714)==9 and r.R0==0x030012E0 and r.R1==FINAL,"final-install",r)then installed=true;log("IRQ-final-install","",r)end
 end)
 hook(FINAL,"final-called",function(r)
  if not target then ignored=ignored+1;return end
  if need(installed and matches==8 and read(0x030012E0,4)==FINAL and w(0x03004716)==8 and w(0x03004714)==9,"final-called",r)then
   log("IRQ-final-called","",r);outcome="earliest-counter1-irq-complete"
  end
 end)
end
local captures={}
local function capture(name,why)
 for _,region in ipairs(regions)do write(name.."-"..region[1]..".bin",memory.read_bytes_as_binary_string(0,region[3],region[2]))end
 assert(savestate.save(out.."/"..name..".State",true)==true,"capture save failed")
 local text=string.format("export_core=%d memory=outer-frame-boundary event=%s %s\n",emu.framecount(),why,state())
 write(name..".txt",text);captures[#captures+1]=name.." "..text
end
local function run()
 assert(savestate.load(reference.."/19-irq-final-install.State",true)==true,"genuine checkpoint load failed")
 userdata.clear();for k,v in pairs(args)do userdata.set(k,v)end
 assert(emu.framecount()==69935 and owner(),"genuine terminal checkpoint owner")
 for _,region in ipairs(regions)do
  assert(memory.getmemorydomainsize(region[2])==region[3])
  assert(memory.read_bytes_as_binary_string(0,region[3],region[2])==file(reference.."/19-irq-final-install-"..region[1]..".bin"),"restored full RAM mismatch")
 end
 assert(memory.getmemorydomainsize("ROM")==0x800000)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))
 capture("restored","genuine69935");log("start","neutral200 first-target1-only")
 install()
 for i=1,200 do
  joypad.set(keys);emu.frameadvance();assert(emu.framecount()==69935+i,"single-frame advance")
  if target and not first_picture then
   capture("counter1-first",string.format("counter1-initialized@%d first-compare@%s",target.core,tostring(target.compare_core)));first_picture=true
  end
  if outcome then break end
 end
 if not outcome then fail(target and "target-cycle-incomplete"or"target-first-compare-not-observed")end
 capture("final",outcome)
 write("counter1-trace.txt",table.concat(rows,"\n").."\n")
 write("counter1-captures.txt",table.concat(captures))
 write("counter1-summary.txt",string.format("outcome=%s start=69935 final=%d matches=%d ignored_prefresh_events=%d scalar_records=%d target_core=%s first_compare_core=%s first_compare_VCOUNT=%s first_compare_line=%s\n",outcome,emu.framecount(),matches,ignored,#rows,tostring(target and target.core),tostring(target and target.compare_core),tostring(target and target.VCOUNT),tostring(target and target.line)))
 write("counter1-done.txt",outcome.."\n")
end
local ok,err=pcall(run)
joypad.set(keys)
if not ok then
 write("counter1-error.txt",tostring(err))
 write("counter1-trace.txt",table.concat(rows,"\n").."\n")
 write("counter1-done.txt","failure:script-error\n")
end
client.exit()
