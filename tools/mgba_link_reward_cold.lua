local out="@@OUTPUT@@/"
local function dump(file,address,size)
 local data={}
 for i=0,size-1 do data[#data+1]=string.char(emu:read8(address+i)) end
 local h=assert(io.open(out..file,"wb")); h:write(table.concat(data));h:close()
end
local function finish(s)
 local h=assert(io.open(out.."finished.txt","w"));h:write(s);h:close()
end
local function title()
 for i=0,51 do
  local h=0x02010000+i*0x118
  if emu:read16(h+16)&2~=0 and emu:read32(h+4)==0x1000 then return h,emu:read32(h) end
 end
end
local phase="title"
local next_press,release,down=0,0,0
local function step()
 local f=emu:currentFrame()
 if f>=release then down=0 end
 local function press(key) if f>=next_press then down=key;release=f+3;next_press=f+32 end end
 local mode=emu:read16(0x03002310)
 if phase=="title" and mode==3 and f>=1500 then
  local h,cb=title()
  if cb==0x08090c7c then
   local count=0
   for i=0,127 do
    local a=0x07000000+8*i
    if emu:read16(a)&0x300~=0x200 and emu:read16(a+4)>>12>=13 then count=count+1 end
   end
   if count==37 then
    dump("title-oam.bin",0x07000000,1024);dump("title-vram.bin",0x06000000,98304)
    dump("title-palette.bin",0x05000000,1024);emu:screenshot(out.."title.png")
    press(8);phase="root"
   end
  end
 elseif (phase=="root" or phase=="collection") and mode==3 then
  local h,cb=title()
  if cb==0x08dfe048 then
   local tree,row=emu:read8(h+28),emu:read8(h+29)
   if tree==0 then
    if phase=="root" then
     local n=0;for i=0,127 do if emu:read16(0x07000000+8*i)&0x300~=0x200 then n=n+1 end end
     if n==110 then dump("root-oam.bin",0x07000000,1024);phase="collection" end
    end
    if phase=="collection" then press(row==4 and 1 or 128) end
   elseif tree==2 then press(row==0 and 1 or 64) end
  elseif cb==0x08090c7c then press(8) end
 elseif phase=="collection" and mode==22 then
  next_press=f+110;phase="viewer"
 elseif phase=="viewer" and mode==22 and f>=next_press then
  dump("tag-oam.bin",0x07000000,1024);dump("tag-vram.bin",0x06000000,98304)
  dump("tag-palette.bin",0x05000000,1024);emu:screenshot(out.."tag.png");finish("PASS");phase="done"
 end
 emu:clearKeys(1023);if down~=0 then emu:addKeys(down) end
 if f>7500 and phase~="done" then finish(phase.."-timeout");phase="done" end
end
callbacks:add("frame",step)
