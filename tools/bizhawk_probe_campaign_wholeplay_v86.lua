-- Continue a fresh assisted 16 MiB campaign through native Shoot cleanup and title return.
local OLD="3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F"
local ROM="574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"
local EXPECTED="campaign-shoot-terminal-results-title"
local APPROVAL="user-approved-development-stage11-boss-hp1-once"
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$") and userdata.get("probe_sha256")==ROM)
assert(userdata.get("stage11_boss_authorization")==APPROVAL,"explicit stage11 HP1 approval required")

local observer,healthy,p1,p2,aux,scene
local consumed,pre,hit,fatal,cleanup=false,nil,false,false,false
local result_mode,ending_mode,title_mode
local menu_ready,mode20_art,mode20_request,done
local seen={}
local function file(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));assert(f:close());return s
end
local function write(name,payload,mode)
 local f=assert(io.open(out.."/"..name,mode or "wb"));assert(f:write(payload));assert(f:close())
end
local function read(a,n)return observer.read(a,n)end
local function w(a)return read(a,2)end
local function mode()return w(0x03002310)end
local function positive(n)return n>0 and n<0x8000 end
local function active(h)
 return h>=0x02010000 and h<=0x02010000+51*0x118 and (h-0x02010000)%0x118==0 and w(h+0x10)&2~=0
end
local function same_live_pair()
 local p,q=observer.pair(true)
 return mode()==7 and read(0x0300231E,1)==11 and observer.live() and p==p1 and q==p2
  and read(0x03004D3C,4)==aux and w(p1+8)&0x100==0 and positive(w(p1+0x64))
end
local function record(name,detail,r,capture)
 if seen[name] then return end
 seen[name]=emu.framecount()
 local pc,lr=0,0
 if r then pc,lr=r.R15,r.R14 end
 local msg=string.format("event=%s core=%d mode=%d stage=%d pc=%08X lr=%08X %s",
  name,seen[name],mode(),read(0x0300231E,1),pc,lr,detail or "")
 write("wholeplay-trace.txt",msg.."\n","ab")
 if capture then observer.queue("wholeplay-"..name,msg,r)end
end
local function require_fact(ok,name,r)
 if ok then return true end
 observer.fail("wholeplay-"..name,observer.state(),r)
 return false
end
local function hook(pc,opcode,name,fn)
 assert(read(pc,4)==opcode,"whole-play opcode "..name)
 event.on_bus_exec(function()
  if healthy and not observer.stopped()then fn(emu.getregisters())end
 end,pc,"wholeplay-"..name)
end
local function attach(obs)
 observer=obs
 hook(0x0836E5E4,0xE1C586B4,"hit-pre",function(r)
  if r.R4~=p1 or r.R5~=p2 or hit then return end
  local after=r.R8&0xFFFF
  if not require_fact(consumed and same_live_pair() and w(p2+0x64)==1 and r.R0>0
   and after==(1-r.R0)&0xFFFF and not positive(after),"unqualified-stage11-damage",r)then return end
  pre={core=emu.framecount(),after=after}
  record("hit-pre",string.format("FIRST=%08X SECOND=%08X before=1 damage=%d after=%04X",p1,p2,r.R0,after),r)
 end)
 hook(0x0836E5E8,0xCA000011,"hit-post",function(r)
  if not pre or r.R4~=p1 or r.R5~=p2 then return end
  if not require_fact(pre.core==emu.framecount() and w(p2+0x64)==pre.after and positive(w(p1+0x64)),"lethal-store",r)then return end
  hit=true;pre=nil;record("hit-post",observer.state(),r,true)
 end)
 hook(0x085CD960,0xE59F802C,"fatal-adapter",function(r)
  if hit and r.R4==p1 and r.R5==p2 then record("fatal-adapter","",r)end
 end)
 hook(0x0836E604,0xE3A09000,"fatal-pair",function(r)
  if not hit then return end
  fatal=require_fact(seen["fatal-adapter"] and r.R4==p1 and r.R5==aux and r.R0==p2
   and read(p2,4)==0x085BDD00 and read(aux,4)==0x085BF204,"fatal-pair",r)
  if fatal then record("fatal-pair",observer.state(),r)end
 end)
 hook(0x08373688,0xEBFF3166,"root4",function(r)
  if not cleanup then require_fact(false,"player-loss",r)end
 end)
 hook(0x083736B0,0xEBFF315C,"root5",function(r)
  if not cleanup and require_fact(hit and fatal and positive(w(p1+0x64)) and not positive(w(p2+0x64)),"root5-before-real-hit",r)then
   record("root5",observer.state(),r)
  end
 end)
 hook(0x0833FD08,0xE92D0100,"case5",function(r)
  if not cleanup and require_fact(seen.root5 and r.R8==0x086FC300,"terminal-case5",r)then record("case5","selected=086FC300",r)end
 end)
 hook(0x085CD000,0xE92D5FFF,"terminal-entry",function(r)
  local owner=read(0x0300133C,4)
  if require_fact(seen.case5 and active(owner) and read(owner+4,4)==0xFF0
   and (not scene or scene==owner),"terminal-owner",r)then
   scene=owner;record("terminal-entry",string.format("owner=%08X",scene),r,true)
  end
 end)
 for _,site in ipairs({{0x085CD340,"terminal-middle"},{0x085CD740,"terminal-final"}}) do
  hook(site[1],0xE92D5FFF,site[2],function(r)
   if require_fact(scene and active(scene) and read(0x0300133C,4)==scene,"terminal-phase-owner",r)then
    record(site[2],string.format("owner=%08X",scene),r,true)
   end
  end)
 end
 hook(0x086FF75C,0xEAFB9F27,"terminal-display",function(r)
  if scene and r.R0==0x086FFE10 and r.R14==0x086FF6EC then record("terminal-display","",r,true)end
 end)
 hook(0x086FFEBC,0xE12FFF1E,"terminal-irq-final",function(r)
  if scene and read(0x030012E0,4)==0x086FFEBC then record("terminal-irq-final","",r)end
 end)
 hook(0x08340C54,0xE92D4000,"cleanup-entry",function(r)
  if require_fact(seen["terminal-final"] and active(scene) and read(0x0300133C,4)==scene,"cleanup-owner",r)then
   record("cleanup-entry",string.format("owner=%08X",scene),r)
  end
 end)
 hook(0x08340CA8,0xE8BD4000,"cleanup-request",function(r)
  if require_fact(seen["cleanup-entry"] and not active(scene) and mode()==7 and w(0x03002314)==1
   and w(0x03002316)==0 and w(0x03002318)==0 and read(0x0300475E,1)==1
   and read(0x0300475F,1)==0 and read(0x0300452A,1)==0,"cleanup-request",r)then
   cleanup=true;record("cleanup-request",string.format("retired=%08X request=1,0,0",scene),r,true)
  end
 end)
 hook(0x080897AC,0xE92D403F,"results-constructor",function(r)
  if mode()==8 and require_fact(cleanup,"results-before-cleanup",r)then
   result_mode=result_mode or emu.framecount()
   record("results-constructor",observer.state(),r,true)
  end
 end)
 hook(0x0808A524,0xE59F4140,"result-ready",function(r)
  if mode()==8 and result_mode then
   menu_ready={mode=8,core=emu.framecount()}
   record("result-ready","",r,true)
  end
 end)
 for _,site in ipairs({{0x0808B0AC,0xEBFE1EDD},{0x0808B170,0xEBFE1EAC},{0x0808B19C,0xEBFE1EA1}}) do
  hook(site[1],site[2],"result-draw-"..site[1],function(r)
   if mode()~=8 or not result_mode then return end
   local p0=read(r.R5+0x48,4)
   local ev=w(r.R5+0xE)
   if p0>=0x08000000 and p0<0x09000000 and (ev==0 or ev==1 or ev==3)then
    record("result-label",string.format("object=%08X p0=%08X label=%d",r.R5,p0,ev),r,true)
   end
  end)
 end
 hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)
  if mode()==11 and require_fact(result_mode,"ending-before-results",r)then
   ending_mode=ending_mode or emu.framecount()
   record("ending-entry",observer.state(),r,true)
  end
 end)
 hook(0x080C0050,0xE59F83B0,"ending-ready",function(r)
  if mode()==11 and ending_mode then
   menu_ready={mode=11,core=emu.framecount()}
   record("ending-ready","",r,true)
  end
 end)
 hook(0x08040448,0xE92D4031,"mode20-entry",function(r)
  if mode()==20 and require_fact(ending_mode,"mode20-before-ending",r)then
   title_mode=title_mode or emu.framecount()
   record("mode20-entry",observer.state(),r,true)
  end
 end)
 hook(0x0804071C,0xE8BD403F,"mode20-art",function(r)
  if mode()~=20 or not title_mode then return end
  local owner=read(0x0300133C,4)
  if require_fact(active(owner) and read(owner+4,4)==0xF100 and read(owner,4)==0x0804074C
   and w(0x03004738)&2~=0,"mode20-art-owner",r)then
   mode20_art=true;record("mode20-art",string.format("owner=%08X flags=%04X",owner,w(0x03004738)),r,true)
  end
 end)
 hook(0x08040608,0xE59F8028,"mode20-return-request",function(r)
  if mode()==20 and require_fact(mode20_art and r.R9==0x03002310 and w(0x03004738)&0x100~=0
   and w(0x03002314)==1 and w(0x03002316)==0 and w(0x03002318)==0,"mode20-return-request",r)then
   mode20_request=true;record("mode20-return-request","request=1,0,0",r,true)
  end
 end)
 hook(0x08090C7C,0xE92D403F,"title-ready",function(r)
  if mode()~=3 or not title_mode then return end
  local owner=read(0x0300133C,4)
  if require_fact(mode20_request and active(owner) and read(owner+4,4)==0x1000
    and read(owner,4)==0x08090C7C,"title-owner",r)then
   done=true;record("title-ready",string.format("owner=%08X",owner),r,true)
  end
 end)
 event.on_bus_write(function(address,value,flags)
  if healthy and not observer.stopped() then
   local old,new=mode(),value&65535
   if old~=new then
    local r=emu.getregisters()
    write("wholeplay-mode-writes.txt",string.format("core=%d address=%08X old=%d new=%d flags=%X pc=%08X lr=%08X\n",
     emu.framecount(),address,old,new,flags,r.R15,r.R14),"ab")
   end
  end
 end,0x03002310,"wholeplay-mode-write")
end
local function activation(p,q)
 p1,p2,aux=p,q,read(0x03004D3C,4)
 healthy=emu.framecount()
 if require_fact(same_live_pair() and positive(w(p2+0x64)),"activation-pair")then
  record("healthy",observer.state(),nil)
 end
end
local function hp1(r)
 if not require_fact(not consumed and same_live_pair() and w(p2+0x64)>1 and positive(w(p2+0x64)),"stage11-hp1-guard",r)then return false end
 local address=p2+0x64
 local hp,score,left,right,before=w(p1+0x64),w(p1+0x66),w(address-2),w(address+2),w(address)
 local row=string.format("kind=stage11-boss core=%d stage=11 FIRST=%08X SECOND=%08X AUX=%08X address=%08X bytes=2 before=%d requested=1 P1HP=%d P1score_before=%d neighbor_left=%d neighbor_right=%d authorization=%s",
  emu.framecount(),p1,p2,aux,address,before,hp,score,left,right,APPROVAL)
 consumed=true
 write("wholeplay-stage11-writes.txt",row.." verified=false\n")
 memory.write_u16_le(address-0x02000000,1,"EWRAM")
 if not require_fact(w(address)==1 and same_live_pair() and w(p1+0x64)==hp and w(p1+0x66)==score
  and w(address-2)==left and w(address+2)==right,"stage11-hp1-readback",r)then return false end
 write("wholeplay-stage11-writes.txt",row.." after=1 verified=true\n")
 record("stage11-hp1",row,nil,true)
 return true
end
local function signed(n)return n<0x8000 and n or n-0x10000 end
local function select_tail(keys,which)
 if not healthy then return false end
 if done or observer.stopped()then return true end
 local core=emu.framecount()
 if which==7 and not hit then
  if not require_fact(same_live_pair() and positive(w(p2+0x64)),"live-aim-owner")then return true end
  local cb=read(p1,4)
  if (cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(p1+6)&1==0 and w(p1+0x76)==0 then
   if w(p1+0xB4)&0x4000==0 then keys.Right=true
   else
    local dx=signed(w(p2+0x34))-signed(w(p1+0x34))
    local dy=signed(w(p2+0x36))-signed(w(p1+0x36))
    local ev=w(p2+0xBA)
    local fresh=w(p1+0x2C)&0x80==0
    if fresh and (ev==1 or ev==4 or ev==5) and dx>=96 and dx<=384 and dy>=128 and dy<=256 then
     keys.B=consumed or hp1()
    end
   end
  end
 elseif (which==8 or which==11) and menu_ready and menu_ready.mode==which and menu_ready.core>=core-1 then
  local entry=which==8 and result_mode or ending_mode
  if entry and core-entry>=120 and (core-entry)%30<4 then keys.A=true end
 end
 return true
end
local function tail_outcome()
 return done and EXPECTED or nil
end
local function finish(outcome)
 write("wholeplay-done.txt",outcome.."\n")
end

local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique whole-play adaptation: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function campaign(code)
 code=replace(code," install();return observer"," install();attach_wholeplay(observer);return observer")
 code=replace(code,'if result=="healthy-native-shoot-activation"then',
  'if result=="campaign-shoot-terminal-results-title"then')
 code=replace(code,'outcome="campaign-eleven-stages-and-healthy-shoot-activation"',
  'outcome="campaign-shoot-terminal-results-title"')
 code=replace(code,'  return result','  finish_wholeplay(outcome)\n  return result')
 code=replace(code,'stage11_writes=disabled frozen_frame_cap=120000','stage11_writes=separate-guarded-ledger frozen_frame_cap=120000')
 code=replace(code,' assisted=true stage11_writes=disabled',' assisted=true stage11_writes=separate-guarded-ledger')
 return replace(code,"guarded-score999-and-stage7-bossHP1 input=frozen-approach-jump-no-up",
  "guarded-score999-and-stage7/11-bossHP1 input=frozen-campaign-then-aimed-shoot")
end
local function shoot_observer(code)
 code=replace(code,"local boss_checkpoint=false","local boss_checkpoint,activation_verified=false,false")
 code=replace(code," if activation and not outcome then"," if activation and not activation_verified and not outcome then")
 code=replace(code,'outcome="healthy-native-shoot-activation";queue("healthy-activation",state())',
  'activation_verified=true;queue("healthy-activation",state());notify_wholeplay_activation(p,q)')
 code=replace(code,' for _,e in ipairs(pending)do capture(e)end;pending={}',
  ' outcome=outcome or wholeplay_outcome()\n for _,e in ipairs(pending)do capture(e)end;pending={}')
 code=replace(code,'outcome=outcome or "bounded-no-activation"','outcome=outcome or "bounded-wholeplay-incomplete"')
 code=replace(code,'stage11_writes=0 initial_core=','stage11_writes=separate-ledger initial_core=')
 return replace(code,' stage11_writes=disabled',' stage11_writes=separate-ledger')
end
local function driver(code)
 local marker=' local mode=observer.read(0x03002310,2)'
 return replace(code,marker,marker.."\n if select_wholeplay_input(keys,mode)then return end")
end
local patches={
 ["@frozen-campaign-with-readonly-provenance"]=campaign,
 ["@frozen-shoot-observer-16MiB"]=shoot_observer,
 ["@frozen-shoot-entry-driver"]=driver,
}
local native_load=load
local env=setmetatable({attach_wholeplay=attach,notify_wholeplay_activation=activation,
 select_wholeplay_input=select_tail,wholeplay_outcome=tail_outcome,finish_wholeplay=finish},{
 __index=_ENV})
env.load=function(code,name,kind,context)
 local patch=patches[name]
 if patch then code=patch(code)end
 return native_load(code,name,kind,context)
end
local source=replace(file("W:/tools/bizhawk_probe_ai_aligned_iraira.lua"),OLD,ROM)
assert(native_load(source,"@frozen-iraira-wholeplay","t",env))()
