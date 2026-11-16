-- Read-only scalar music observations over the frozen ordinary16MiB result flow.
local telemetry=[=[
local music_out=assert(userdata.get("output"))
assert(music_out:match("^W:/build/[%w%-%_/]+$"))
local music_file=assert(io.open(music_out.."/music-lifetime.txt","wb"))
local function music_read(at,width)
 local domain,offset
 if at>=0x02000000 and at+width<=0x02040000 then domain,offset="EWRAM",at-0x02000000
 elseif at>=0x03000000 and at+width<=0x03008000 then domain,offset="IWRAM",at-0x03000000
 elseif at>=0x08000000 and at+width<=0x09000000 then domain,offset="ROM",at-0x08000000
 else return -1 end
 if width==1 then return memory.read_u8(offset,domain) end
 if width==2 then return memory.read_u16_le(offset,domain) end
 return memory.read_u32_le(offset,domain)
end
assert(music_read(0x0837B458,4)==0x5A280AD8,"reviewed pause-cache hook")
assert(music_read(0x08D7DFC0,4)==0xE358006C and music_read(0x08D7DFC8,4)==0xE3580070,"reviewed four-ID cache tail")
assert(music_read(0x0837FBB4,4)==0x03006B40,"reviewed player-zero pointer")
local music_headers={}
for id=0x6C,0x6F do
 local row=0x08D33000+id*8
 local header=music_read(row,4)
 assert(header>=0x08D33000 and header<0x08D7DFC0 and music_read(row+4,2)==0,"four player-zero scores")
 music_headers[header]=id
end
local music_counts,music_emitted={},{}
local music_new_starts={[0x6C]=0,[0x6D]=0,[0x6E]=0,[0x6F]=0}
local music_selectors=0
local music_pending_frame=nil
local function music_log(label,r,extra)
 music_counts[label]=(music_counts[label] or 0)+1
 if (music_emitted[label] or 0)>=32 then return end
 music_emitted[label]=(music_emitted[label] or 0)+1
 assert(music_file:write(string.format(
  "event=%s core=%d pc=%08X lr=%08X sp=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r8=%08X cache=%08X queue=%04X type=%04X gate=%04X flags=%04X player_header=%08X player_status=%08X %s\n",
  label,emu.framecount(),r.R15,r.R14,r.R13,r.R0,r.R1,r.R2,r.R3,r.R4,r.R8,
  music_read(0x03004E98,4),music_read(0x030022F2,2),music_read(0x030022FE,2),
  music_read(0x030022F6,2),music_read(0x03002300,2),music_read(0x03006B40,4),
  music_read(0x03006B44,4),extra or "")))
 music_file:flush()
end
local function music_hook(address,label,callback)
 music_counts[label]=0;music_emitted[label]=0
 event.on_bus_exec(function()callback(emu.getregisters(),label)end,address,"music-lifetime-"..label)
end
music_hook(0x080D14BC,"evolution-selector",function(r,label)
 music_selectors=music_selectors+1
 music_log(label,r,string.format("entry_identity=%08X actor_identity=%02X",music_read(r.R13,4),music_read(r.R4+0x11,1)))
end)
music_hook(0x080D14F0,"evolution-queue-return",function(r,label)music_log(label,r)end)
music_hook(0x0837B44C,"music-request",function(r,label)
 if r.R8<0x1E or (r.R8>=0x6C and r.R8<0x70) then music_log(label,r) end
end)
music_hook(0x0837C298,"player-zero-start",function(r,label)
 if r.R0~=0x03006B40 then return end
 music_pending_frame=emu.framecount()
 local id=music_headers[r.R1]
 if id then music_new_starts[id]=music_new_starts[id]+1 end
 music_log(label,r,string.format("requested_header=%08X appended_id=%d",r.R1,id or -1))
end)
music_hook(0x0837C29C,"player-zero-start-return",function(r,label)
 if music_pending_frame~=emu.framecount() then return end
 music_pending_frame=nil;music_log(label,r)
end)
music_hook(0x0835A75C,"devolution-return-site",function(r,label)
 music_log(label,r,string.format("stage_music_eligible=%s",tostring((music_read(0x03004506,2)&0x80)==0)))
end)
music_hook(0x0837B48C,"pause-entry",function(r,label)music_log(label,r)end)
music_hook(0x0837B4A8,"resume-entry",function(r,label)music_log(label,r)end)
music_hook(0x0837C364,"pause-header-compare",function(r,label)
 music_log(label,r,string.format("active_header=%08X requested_header=%08X equal=%s",r.R1,r.R0,tostring(r.R1==r.R0)))
end)
music_hook(0x0837C398,"resume-header-compare",function(r,label)
 music_log(label,r,string.format("active_header=%08X requested_header=%08X equal=%s",r.R1,r.R0,tostring(r.R1==r.R0)))
end)
assert(music_file:write("start readonly=true policy=unchanged hook_count=10 per_label_limit=32 max_event_rows=320 absence_is_not_coverage=true\n"))
music_file:flush()
local function music_lifetime_finish()
 assert(music_file:write(string.format("summary core=%d evolution_entries=%d starts6C=%d starts6D=%d starts6E=%d starts6F=%d\n",
  emu.framecount(),music_selectors,music_new_starts[0x6C],music_new_starts[0x6D],music_new_starts[0x6E],music_new_starts[0x6F])))
 local labels={};for label in pairs(music_counts)do labels[#labels+1]=label end;table.sort(labels)
 for _,label in ipairs(labels)do assert(music_file:write(string.format("count event=%s observed=%d emitted=%d\n",label,music_counts[label],music_emitted[label])))end
 music_file:close()
end
]=]
local f=assert(io.open("W:/tools/bizhawk_probe_result_languages_16m.lua","rb"))
local wrapper=assert(f:read("*a"));f:close()
local anchor='assert(load(source,"@reviewed-result-sixteen-MiB-capture","t",_ENV))()'
local a,b=wrapper:find(anchor,1,true)
assert(a and not wrapper:find(anchor,b+1,true),"unique frozen16MiB execution")
local insert='local finish="client.exit()"\n'
 ..'local x,y=source:find(finish,1,true)\n'
 ..'assert(x and not source:find(finish,y+1,true),"unique unchanged result exit")\n'
 ..'source=source:sub(1,x-1).."music_lifetime_finish()\\n"..source:sub(x)\n'
 ..'source='..string.format("%q",telemetry)..'..source\n'
 ..'assert(load(source,"@reviewed-result-music-lifetime","t",_ENV))()'
wrapper=wrapper:sub(1,a-1)..insert..wrapper:sub(b+1)
assert(load(wrapper,"@reviewed-result-music-lifetime-wrapper","t",_ENV))()
