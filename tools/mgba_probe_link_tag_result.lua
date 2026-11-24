local out="@@OUTPUT@@/"
local p=1
local first=io.open(out.."registered-1.txt","r")
if first then first:close();p=2 end
local function write(n,s) local f=assert(io.open(out..n,"w"));f:write(s);f:close()end
write("registered-"..p..".txt","ok")
local function log(s)local h=assert(io.open(out.."p"..p..".txt","a"));h:write(s.."\n");h:close()end
local function read(a,n)
 if n==1 then return emu:read8(a) elseif n==2 then return emu:read16(a) else return emu:read32(a) end
end
local function task(pr)
 for i=0,51 do local h=0x02010000+i*0x118
  if (read(h+16,2) & 2)~=0 and read(h+4,4)==pr then return h end
 end
end
local regh,rm,tval,nextkey,release,allowed,lastserial=0,-1,-1,0,0,0,-1
local entered_result=nil;local exit_frame=nil;local tracking=false;local success=0;local confirmed=false;local started=false
local function frame()
 local f=emu:currentFrame();local md=read(0x03002310,2)
 local serial=read(0x04000128,2)
 if not tracking and f>1 then
 tracking=true
 for _,pc in ipairs({0x083404e0,0x0837ab1c,0x0837ab34,0x0837ab50,0x0837ab8c,0x0837ab90,0x08015b18,0x08015b28})do
  local a=pc
  emu:setBreakpoint(function()
   local frame=emu:currentFrame();local base=0x03002168
   if a==0x0837ab8c then success=success+1 end
   log(string.format("pc=%08X f=%d role=%d side=%d score=%d:%d cfg=%X ver=%d out=%04X/%04X/%04X/%04X in=%04X/%04X/%04X/%04X %04X/%04X/%04X/%04X",a,frame,read(0x03001F00,1),read(0x03004528,1),read(0x0300475e,1),read(0x0300475f,1),read(0x0300232a,2),read(0x03002335,1),read(base,2),read(base+2,2),read(base+4,2),read(base+6,2),read(base+16,2),read(base+18,2),read(base+20,2),read(base+22,2),read(base+32,2),read(base+34,2),read(base+36,2),read(base+38,2)))
  end,a)
 end
 end
 if md~=rm or (f%600==0) then
  log(string.format("f=%d mode=%d config=%04X sel=%04X sio=%04X words=%04X,%04X",f,md,read(0x0300232a,2),read(0x03002312,2),serial,read(0x04000120,2),read(0x04000122,2)))
  rm=md
 end
 if f>=release then allowed=0 end
 local function pulse(mask) if f<nextkey then return end;allowed=mask;release=f+3;nextkey=f+32 end
 if md==3 then
  local h=task(0x1000);local cb=h and read(h,4) or 0
  if cb~=regh then regh=cb;log(string.format("f=%d title cb=%08X",f,cb)) end
  if cb==0x08090C7C and f>1500 then pulse(8)
  elseif cb==0x08DFE048 then
   local tree=read(h+0x1C,1);local row=read(h+0x1D,1)
   if tree*8+row~=tval then log(string.format("f=%d tree=%d row=%d",f,tree,row));tval=tree*8+row end
   if tree==0 then pulse(row==1 and 1 or 128)
   elseif tree==1 then confirmed=true;pulse(row==@@VERSION_ROW@@ and 1 or 128) end
  end
 elseif confirmed and md~=0 and md~=1 and md~=2 and md~=20 then
  if md==4 and entered_result and not exit_frame then exit_frame=f end
  if md==4 and not started then started=true;emu:screenshot(out.."p"..p.."-selection.png") end
  if f%400==0 then emu:screenshot(out.."p"..p.."-mode"..md..".png") end
  if md==7 then
   if p==@@ATTACKER@@ then
    local first=read(0x0300489c,4);local second=read(0x030048a0,4)
    if p==2 then first,second=second,first end
    local direction=(f%250<125) and 16 or 32
    if first>=0x02000000 and second>=0x02000000 and first<0x03008000 and second<0x03008000 then
     local q=read(first+0x34,2);local r=read(second+0x34,2)
     if q>=32768 then q=q-65536 end;if r>=32768 then r=r-65536 end
     if math.abs(q-r)>128 or f%160<42 then direction=(q<r) and 16 or 32 else direction=0 end
     if f%600==0 then log(string.format("fighters x=%d:%d score=%d:%d",q,r,read(first+0x66,2),read(second+0x66,2))) end
    end
    allowed=direction | ((f%14<7) and 2 or 0) | ((f%61<4) and 1 or 0)
   else allowed=0 end
  elseif md==8 then
   entered_result=entered_result or f
   if f-entered_result>140 then pulse(1) else allowed=0 end
  else pulse(1) end
 end
 emu:clearKeys(1023);if allowed~=0 then emu:addKeys(allowed) end
 if (exit_frame and f-exit_frame>220) or f>=21000 then write("finished-"..p..".txt",(exit_frame and success>0) and "exchange-complete" or "timeout") end
end
callbacks:add("frame",frame)

