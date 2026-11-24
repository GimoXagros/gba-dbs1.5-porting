local master_seen={}
local master_render,master_controller=nil,nil
local master_break=nil
local function inspect_master(f)
 if not master_break then
  master_break=emu:setBreakpoint(function()
   master_render=emu:readRegister('r9'); master_controller=emu:readRegister('r10')
  end,@@PARTY_INIT@@)
 end
 local r,c=master_render,master_controller
 if not r or not c or read(c+0x114,4)~=r or read(r+24,2)~=0x800a then return end
 local stage=read(r+28,2)
 if stage~=2 and stage~=3 then return end
 local age=read(c+212,4)
 if age~=0 and age~=1 and age~=99 and age~=100 and age~=101 and age~=150 and age~=152 then return end
 if master_seen[age] then return end
 master_seen[age]=true
 log(string.format("party f=%d tick=%d phase=%d y=%d jump=%d facing=%d render=%08X controller=%08X",f,age,stage,read(c+184,4),read(c+192,4),read(c+204,4),r,c))
 local prefix="party-"..age.."-"
 card_bytes(prefix.."first",r+120,150)
 card_bytes(prefix.."second",c+24,150)
 if age==99 or age==100 or age==101 or age==152 then
  card_bytes(prefix.."oam",0x07000000,1024)
  card_bytes(prefix.."shadow",0x03001428,1024)
  card_bytes(prefix.."vram",0x06010000,32768)
  card_bytes(prefix.."palette",0x05000200,512)
  emu:screenshot(out.."p"..p.."-"..prefix.."frame.png")
 end
end
