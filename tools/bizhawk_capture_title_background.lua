-- Native title observation through ordinary input only.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
assert(emu.getsystemid()=="GBA")
local function dump(name,domain,start,size)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(memory.read_bytes_as_binary_string(start,size,domain));f:close()
end
local function capture(name)
 for _,v in ipairs({{"iwram","IWRAM",0,0x8000},{"ewram","EWRAM",0,0x40000},{"vram","VRAM",0,0x18000},{"palette","PALRAM",0,0x400},{"oam","OAM",0,0x400},{"display","System Bus",0x04000000,0x60}}) do dump(name.."-"..v[1]..".bin",v[2],v[3],v[4]) end
 client.screenshot(out.."/"..name..".png")
 local f=assert(io.open(out.."/trace.txt","a"));f:write(string.format("capture=%s frame=%d mode=%d language_tag=%02X\n",name,emu.framecount(),memory.read_u16_le(0x2310,"IWRAM"),memory.read_u8(0x112F,"IWRAM")));f:close()
end
dump("loaded-rom.bin","ROM",0,0x800000)
client.speedmode(800)
local keys={};local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
for frame=0,3650 do
 for _,button in ipairs(buttons) do keys[button]=false end
 keys.Start=frame>=2970 and frame<2985;keys.A=frame>=3300 and frame<3315
 joypad.set(keys);emu.frameadvance()
 if frame==3200 then capture("prompt") end
end
for _,button in ipairs(buttons) do keys[button]=false end;joypad.set(keys)
capture("menu")
local f=assert(io.open(out.."/done.txt","w"));f:write("title-observation-complete");f:close()
client.exit()
