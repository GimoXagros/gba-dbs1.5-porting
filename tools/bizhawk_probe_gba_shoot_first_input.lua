-- Genuine healthy checkpoint, one fresh A edge and five released frames; no guest writes.
local args={}
for _,k in ipairs({"output","checkpoint_dir","probe_sha256"})do args[k]=assert(userdata.get(k),k)end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$") and reference:match("^W:/build/[%w%-%_/]+$") and out~=reference)
assert(emu.getsystemid()=="GBA" and args.probe_sha256=="84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B")
local function read(path)local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s end
local function write(name,s)local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(s));f:close()end
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},{"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local keys={A=false,B=false,Select=false,Start=false,Right=false,Left=false,Up=false,Down=false,R=false,L=false}
local function word(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 else error("unexpected observation address")end
 if n==1 then return memory.read_u8(o,d)elseif n==2 then return memory.read_u16_le(o,d)else return memory.read_u32_le(o,d)end
end
local rows={}
local function sample(kind)
 local p,q=word(0x0300489C,4),word(0x030048A0,4)
 assert(p==0x02011710 and q==0x02011828,"healthy actor owners changed")
 local s=string.format("kind=%s core=%d mode=%d stage=%d flags=%04X FIRST=%08X SECOND=%08X P1HP=%d P2HP=%d held=%04X edge=%04X pheld=%04X pedge=%04X x=%04X y=%04X callback=%08X event=%04X",kind,emu.framecount(),word(0x03002310,2),word(0x0300231E,1),word(0x0300450A,2),p,q,word(p+0x64,2),word(q+0x64,2),word(0x03001302,2),word(0x03001306,2),word(p+0x2C,2),word(p+0x2E,2),word(p+0x34,2),word(p+0x36,2),word(p,4),word(p+0xBA,2))
 rows[#rows+1]=s
 return p,q
end
local function dump(name)
 for _,r in ipairs(regions)do write(name.."-"..r[1]..".bin",memory.read_bytes_as_binary_string(0,r[3],r[2]))end
 client.screenshot(out.."/"..name..".png")
end
local function run()
 local meta=read(reference.."/healthy-activation.txt")
 assert(meta:match("^core=68927 input_relative=68926 stage7_consumed=true "),"healthy checkpoint epoch")
 assert(read(reference.."/healthy-activation.State"):sub(1,4)=="PK\003\004")
 assert(savestate.load(reference.."/healthy-activation.State",true)==true,"checkpoint load failed")
 userdata.clear();for k,v in pairs(args)do userdata.set(k,v);assert(userdata.get(k)==v)end
 local function restored()
  assert(emu.framecount()==68927,"restored frame")
  for _,r in ipairs(regions)do
   assert(memory.getmemorydomainsize(r[2])==r[3])
   assert(memory.read_bytes_as_binary_string(0,r[3],r[2])==read(reference.."/13-healthy-activation-"..r[1]..".bin"),"restored "..r[1])
  end
 end
 restored();assert(savestate.save(out.."/restored.State",true)==true,"restore export failed");restored()
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))
 local p,q=sample("before-input")
 assert(word(0x03002310,2)==7 and word(0x0300231E,1)==11 and word(0x0300450A,2)==6)
 assert(word(p+0x64,2)==4 and word(q+0x64,2)==37)
 assert(word(0x03001302,2)&0x40==0,"A must be released at checkpoint")
 assert(word(word(0x03004510,4),4)==0x08374FF4 and word(word(0x03004514,4),4)==0x083735BC,"live controllers required")
 dump("00-before")
 for _,address in ipairs({0x08375138,0x0837513C,0x08375140})do
  event.on_bus_exec(function()
   sample(string.format("before-%08X",address))
   local regs=emu.getregisters();local names={};for k in pairs(regs)do names[#names+1]=k end;table.sort(names)
   local line={};for _,k in ipairs(names)do line[#line+1]=string.format("%s=%08X",k,regs[k])end
   rows[#rows+1]="regs "..table.concat(line," ")
  end,address,"shoot-first-input-"..address)
 end
 for i=1,6 do
  keys.A=i==1;joypad.set(keys);emu.frameadvance()
  assert(emu.framecount()==68927+i,"single-frame input advance")
  sample("after-"..i);dump(string.format("%02d-after",i))
  write("first-input-trace.txt",table.concat(rows,"\n").."\n")
 end
 keys.A=false;joypad.set(keys)
 assert(savestate.save(out.."/after-input.State",true)==true,"final export failed")
 write("first-input-done.txt","six-input-frames-captured")
end
local ok,err=pcall(run)
keys.A=false;joypad.set(keys)
if not ok then write("first-input-failure.txt",tostring(err));write("first-input-done.txt","failure")end
client.exit()
