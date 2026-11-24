-- Inserted before the input driver. All guest memory accesses are reads.
local card_entered=nil
local music_tracking=false
local card_had_result=false
local function arena_keys(f,attacker)
 local a,b=read(0x0300489c,4),read(0x030048a0,4)
 if a<0x02000000 or b<0x02000000 or a>=0x03008000 or b>=0x03008000 then return 0 end
 if p==2 then a,b=b,a end
 local function signed(v) return v>=32768 and v-65536 or v end
 local x,y=signed(read(a+0x34,2)),signed(read(a+0x36,2))
 local tx,ty=signed(read(b+0x34,2)),signed(read(b+0x36,2))
 if f%600==0 then log(string.format("arena p=%d x=%d y=%d tx=%d ty=%d",p,x,y,tx,ty)) end
 local towards=(x<tx and 16 or 32)
 if p~=attacker then
  if y+256<ty then return x<tx-320 and 32 or 16 end
  return 0
 end
 local move=(math.abs(tx-x)>128 or f%160<42) and towards or 0
 if y+320<ty then move=(f%240<145) and (x<tx and 32 or 16) or towards end
 return move | ((f%14<7) and 2 or 0) | ((f%55<7) and 1 or 0)
end
local function card_bytes(name,address,count)
 local f=assert(io.open(out.."p"..p.."-card-"..name..".bin","wb"))
 local buffer={}
 for i=0,count-1 do buffer[#buffer+1]=string.char(emu:read8(address+i)) end
 f:write(table.concat(buffer));f:close()
end
local function inspect_card(f,mode)
 if not music_tracking and f>1 then
  music_tracking=true
  emu:setBreakpoint(function()
   if read(0x03002310,2)==24 then
    log(string.format("card-audio f=%d song=%02X priority=%d",emu:currentFrame(),emu:readRegister("r8"),emu:readRegister("r9")))
   end
  end,0x080D15C0)
 end
 if mode~=24 then
  if mode==8 and card_entered~=8 then
   log(string.format("before-card f=%d winin=%04X winout=%04X blend=%04X",f,read(0x04000048,2),read(0x0400004a,2),read(0x04000050,2)))
   card_entered=8
  elseif mode~=8 then card_entered=nil end
  return
 end
 if card_entered==8 then card_entered=nil end
 card_entered=card_entered or f
 local elapsed=f-card_entered
 if read(0x03002172,2)~=0xffff then card_had_result=true end
 if elapsed==0 or elapsed==8 or elapsed==34 or elapsed==150 or elapsed==365 then
  log(string.format("card f=%d elapsed=%d token=%04X ext=%04X BG0H=%04X ctl=%04X",f,elapsed,read(0x03002172,2),read(0x03002170,2),read(0x04000010,2),read(0x04000000,2)))
 end
 if elapsed==34 or elapsed==150 or elapsed==365 then
  emu:screenshot(out.."p"..p.."-card-"..elapsed..".png")
 end
 if elapsed==540 or elapsed==860 or elapsed==950 then
  emu:screenshot(out.."p"..p.."-card-"..elapsed..".png")
  log(string.format("special f=%d elapsed=%d token=%04X",f,elapsed,read(0x03002172,2)))
 end
 if elapsed==150 then
  emu:saveStateFile(out.."p"..p.."-card.ss1")
  card_bytes("palette",0x05000000,1024)
  card_bytes("vram",0x06000000,98304)
  card_bytes("oam",0x07000000,1024)
  card_bytes("bg",0x04000000,96)
 end
end
