-- Observe each cartridge's own menus and the physical multiplayer input lanes.
local out="@@OUTPUT@@/"
local core,retail
local function bytes(a,n) return emu:readRange(a,n) end
local function b(a) return emu:read8(a) end
local function w(a) return emu:read16(a) end
local function u(a) return emu:read32(a) end
local function put(name,data)
 local h=assert(io.open(out..name,"wb"));h:write(data);h:close()
end
local function log(msg)
 local h=assert(io.open(out.."trace-"..core..".txt","a"));h:write(emu:currentFrame().." "..msg.."\n");h:close()
end
local function shot(tag) emu:screenshot(out.."p"..core.."-"..tag..".png") end
local function task(priority)
 for i=0,51 do local h=0x02010000+i*0x118
  if w(h+16)&2~=0 and u(h+4)==priority then return h end
 end
end
local mode,cb0,cursor=-1,0,-1
local started,done=false,false
local selected_at=nil
local observed={}
local last_index,stable,wrapped,last_packet,cancelled=nil,0,false,nil,false
local selector_id=nil
local sent,received={},{}
local wrong_cancelled=false
local locale_returned,locale_row_frame=false,nil
local wins,round=0,0
local victors={}
local contact=false
local low_score=false
local nextkey,release,held=0,0,0
local function pulse(f,key)
 if f>=nextkey then held=key;release=f+3;nextkey=f+32 end
end
local function finish(value) put("done-"..core,value);done=true;emu:clearKeys(1023) end
local function signed(x)return x>=32768 and x-65536 or x end
local function fight(f)
 local a,c=u(0x0300489c),u(0x030048a0)
 if a<0x02000000 or c<0x02000000 or a>=0x02040000 or c>=0x02040000 then return 0 end
 if b(0x03004528)==1 then a,c=c,a end
 local x,y=signed(w(a+0x34)),signed(w(a+0x36))
 local tx,ty=signed(w(c+0x34)),signed(w(c+0x36))
 local side=b(0x03004528)
 if w(a+0x66)>0 and w(a+0x66)<999 or w(c+0x66)>0 and w(c+0x66)<999 then low_score=true end
 local goal=victors[1] and 2 or (victors[2] and 1 or @@FIRST_ATTACKER@@)
 if f%240==0 then log(string.format("actors side=%d own=%02X other=%02X x=%d:%d y=%d:%d hp=%d:%d score=%d:%d",side,b(a+17),b(c+17),x,tx,y,ty,w(a+0x64),w(c+0x64),w(a+0x66),w(c+0x66))) end
 if core~=goal then
  if y+256<ty then return x<tx-320 and 32 or 16 end
  return 0
 end
 local towards=x<tx and 16 or 32
 local move=(math.abs(tx-x)>128 or f%160<42) and towards or 0
 if y+320<ty then move=f%240<145 and (x<tx and 32 or 16) or towards end
 return move | (f%14<7 and 2 or 0) | (f%55<7 and 1 or 0)
end
local function init()
 local sig=u(0x0837c2a4)
 assert(sig==@@FIRST_SIG@@ or sig==@@SECOND_SIG@@)
 core=sig==@@FIRST_SIG@@ and 1 or 2
 retail=core==@@RETAIL_CORE@@
 local f=assert(io.open(out.."loaded-"..core..".bin","wb"))
 for i=0,(retail and 0x400000 or 0x1000000)-1,65536 do f:write(bytes(0x08000000+i,65536))end;f:close()
 emu:setBreakpoint(function()
  if w(0x03002310)==4 then
   local offset=emu:readRegister("r1")
   local base=emu:readRegister("r8")
   selector_id=w(base+offset)
   local idx=offset//2
   if "@@SCENARIO@@"=="boundary" and not observed[idx] then
    observed[idx]=selector_id
    log(string.format("selector index=%d id=%d max=%d",idx,selector_id,w(0x03004740)))
   end
  end
 end,0x0808323c)
 emu:setBreakpoint(function()
  local op=emu:readRegister("r3")&255
  if not sent[op] then sent[op]=true;log(string.format("offer op=%02X",op)) end
 end,0x08081e68)
 emu:setBreakpoint(function()
  if contact then return end
  local a,c=emu:readRegister("r4"),emu:readRegister("r5")
  local p,q=u(0x0300489c),u(0x030048a0)
  if p~=0 and q~=0 and ((c==q and (a==p or u(a+0x14)==p)) or (c==p and (a==q or u(a+0x14)==q))) then
   contact=true;log(string.format("hit attack=%08X target=%08X flags=%04X/%04X",a,c,w(a+0xa),w(c+0xa)))
  end
 end,0x0836e3d0)
 local function record_echo()
  local localop=b(0x03002168)
  if localop==15 or localop==79 then
   local key=string.format("op=%02X frames=%04X/%04X",localop,w(0x03002178),w(0x03002188))
   if not received[key] then received[key]=true;log("handshake "..key) end
  end
 end
 emu:setBreakpoint(record_echo,0x08015360)
 emu:setBreakpoint(record_echo,0x080153a4)
 for _,addr in ipairs({0x083404e0,0x0837ab1c,0x0837ab34,0x0837ab50,0x0837ab8c,0x0837ab90,0x08015b18,0x08015b28})do
  local pc=addr
  emu:setBreakpoint(function()
   local base=0x03002168
   local function packet(a)return string.format("%04X/%04X/%04X/%04X",w(a),w(a+2),w(a+4),w(a+6))end
   local s,t=b(0x0300475e),b(0x0300475f)
   log(string.format("pc=%08X role=%d side=%d score=%d:%d cfg=%04X out=%s in=%s %s",pc,b(0x03001f00),b(0x03004528),s,t,w(0x0300232a),packet(base),packet(base+16),packet(base+32)))
   if pc==0x0837ab8c then
    if s~=t then
     local victor_side=s>t and 0 or 1
     local victor=b(0x03004528)==victor_side and core or 3-core
     if not victors[victor] then victors[victor]=true;wins=wins+1 end
    end
   end
  end,pc)
 end
end
local function frame()
 if done then return end
 local f=emu:currentFrame()
 if not core then init() end
 local md=w(0x03002310)
 if md==4 or md==5 or md==6 or md==8 then
  local buf=0x03002168
  local state=string.format("%04X/%04X %04X/%04X %04X/%04X",w(buf),w(buf+2),w(buf+16),w(buf+18),w(buf+32),w(buf+34))
  if state~=last_packet then
   last_packet=state
   local op=b(buf)
   if op==15 or op==79 or op==129 or op==130 then log("wire "..state) end
  end
 end
 if md~=mode or f%1200==0 then
  log(string.format("mode=%d cfg=%04X stage=%d variant=%d serial=%04X role=%d side=%d ids=%d/%d",md,w(0x0300232a),b(0x0300231e),b(0x03002335),w(0x04000128),b(0x03001f00),b(0x03004528),b(0x0300231a),b(0x0300231b)))
  if md~=mode and (md==4 or md==7 or md==8 or md==24) then shot("round"..round.."-entry-"..md) end
  if md~=mode and md==7 then round=round+1 end
  mode=md
 end
 if f>=release then held=0 end
 if md==3 then
  local h=task(0x1000);local cb=h and u(h) or 0
  if "@@SCENARIO@@"=="wrong" and cancelled and not wrong_cancelled and (cb==0x08090c7c or cb==0x08090fa0 or cb==0x08dfe048) then
   shot("cancelled-title");log("ordinary cancel returned, retry legacy");wrong_cancelled=true
  end
  if cb~=cb0 then cb0=cb;log(string.format("title cb=%08X",cb)) end
  if "@@SCENARIO@@"=="locale" and cancelled then locale_returned=true end
  if cb==0x08090c7c and f>700 then pulse(f,8)
  elseif retail and cb==0x08090fa0 then
   local row=b(0x03002c5e)
   if row~=cursor then log("retail root="..row);cursor=row end
   if "@@SCENARIO@@"=="cold" then shot("cold-root");put("cold-native-"..core..".bin",bytes(0x03001120,196));finish("PASS");return end
   if "@@SCENARIO@@"=="locale" and locale_returned then shot("returned-root");log("retail menu after cancel");finish("PASS");return end
   if row==1 then started=true end
   pulse(f,row==1 and 1 or 128)
  elseif not retail and cb==0x08dfe048 then
   local tree,row=b(h+28),b(h+29)
   if tree*8+row~=cursor then log("port tree="..tree.." row="..row);cursor=tree*8+row end
   if "@@SCENARIO@@"=="cold" then shot("cold-root");put("cold-native-"..core..".bin",bytes(0x03001120,196));finish("PASS");return end
   if tree==0 then pulse(f,row==1 and 1 or 128)
   elseif tree==1 then
    local target="@@SCENARIO@@"=="wrong" and not wrong_cancelled and 0 or 1
    if row==target then
     started=true
     if "@@SCENARIO@@"=="locale" then
      if not locale_row_frame then locale_row_frame=f end
      if f-locale_row_frame<24 then held=0;emu:clearKeys(1023);return end
      local lang=b(0x0300112f)
      log(string.format("version locale=%02X row=%d returned=%d",lang,row,locale_returned and 1 or 0))
      if locale_returned then shot("returned-version");finish("PASS");return end
      shot("legacy-version")
     end
    end
    pulse(f,row==target and 1 or 128)
   end
  end
 elseif started then
  if md==4 and "@@SCENARIO@@"=="locale" then
   selected_at=selected_at or f
   if f-selected_at>150 then
    if not cancelled then shot("actual-select");log("cancel before fighter confirm");cancelled=true;locale_row_frame=nil end
    pulse(f,2)
   end
  elseif md==4 and "@@SCENARIO@@"=="boundary" then
   selected_at=selected_at or f
   if f-selected_at>130 then
    local idx=b(0x0300473c)
    local max=w(0x03004740)
    if last_index~=idx then
     last_index=idx;stable=f
     if idx==0 and observed[max]~=nil then wrapped=true end
    end
    if wrapped and idx==max then
     if f-stable>=12 then shot("boundary");pulse(f,1) end
    else pulse(f,128) end
   end
  elseif md==7 and "@@SCENARIO@@"=="boundary" then

   local p,q=u(0x0300489c),u(0x030048a0)
   if p>=0x02010000 and p<0x02014000 and q>=0x02010000 and q<0x02014000 and u(p+0x18)==q and u(q+0x18)==p then
    log(string.format("common fighters %d/%d",b(p+17),b(q+17)));shot("boundary-arena");finish("PASS");return
   end
  elseif md==4 and "@@SCENARIO@@"=="wrong" and not wrong_cancelled then
   selected_at=selected_at or f
   if f-selected_at>1400 then
    if not cancelled then cancelled=true;log("cancel mismatched version");shot("before-cancel") end
    pulse(f,2)
   else pulse(f,1) end
  elseif md==7 and "@@SCENARIO@@"=="wrong" then
   if wrong_cancelled then shot("recovered-battle");log("recovered with normal link retry");finish("PASS") else shot("accepted-wrong-menu");finish("WRONG_MENU_ACCEPTED") end;return
  elseif md==4 and wins>=2 then
   shot("back-to-select");log("two results returned");finish("PASS");return
  elseif md==7 then
   held=fight(f)
   if "@@SCENARIO@@"=="contact" and contact and low_score then shot("score-after-hit");log("native hit and ordinary nonzero score");finish("PASS");return end
  elseif md==4 or md==5 or md==6 or md==8 or md==24 then pulse(f,1) end
 end
 emu:clearKeys(1023);if held~=0 then emu:addKeys(held) end
 if f>=@@LIMIT@@ then shot("limit");finish("limit") end
end
callbacks:add("frame",frame)
