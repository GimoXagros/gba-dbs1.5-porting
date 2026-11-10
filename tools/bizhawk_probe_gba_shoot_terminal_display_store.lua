-- Observe the executed scroll store; its hardware destination is write-only.
local target="280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7"
assert(userdata.get("probe_sha256")==target,"reviewed display-epoch ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_terminal.lua","rb"))
local source=assert(f:read("*a"));f:close()
local old="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen ROM binding")
source=source:sub(1,a-1)..target..source:sub(b+1)
local before='if read(Q+0x28,4)~=AUX or read(AUX+0x18,4)~=Q then return "native-guard-aux18-not-upper"end'
local after='if read(Q+0x28,4)~=AUX or read(AUX+0x28,4)~=Q then return "native-guard-aux28-not-upper"end'
local x,y=source:find(before,1,true)
assert(x and not source:find(before,y+1,true),"unique frozen owner predicate")
source=source:sub(1,x-1)..after..source:sub(y+1)
local changes={
 {'w(0x0400000A)&0xDFCC~=0x1E00','w(0x0400000A)&0xCC~=0'},
 {'hook(0x086FF6E8,"guarded-display"','hook(0x086FF75C,"guarded-display"'}
}
for _,change in ipairs(changes)do
 local i,j=source:find(change[1],1,true)
 assert(i and not source:find(change[1],j+1,true),"unique frozen display epoch site")
 source=source:sub(1,i-1)..change[2]..source:sub(j+1)
end
local old_scroll=[=[ hook(0x085E743C,"next-scroll-stored",function(r)
  if scroll_pending then
   if need(b(0x030012B8)==scroll_pending and w(0x04000014)==(scroll_pending-8)&0xFFFF,"next-scroll-store",r)then
    scroll_after=true;scroll_pending=nil;queue("next-display-scroll",r);log("next-display-scroll-post",irq_state(),r)
   end
  end
 end)
]=]
local new_scroll=[=[ local scroll_store=nil
 hook(0x08000F3C,"next-scroll-STRH",function(r)
  if scroll_pending then
   if need(not scroll_store and r.R14==0x085E743C and r.R0==scroll_pending and r.R8==0x030012B8 and r.R9==0x04000000 and (r.R10&0xFFFF)==((scroll_pending-8)&0xFFFF)and b(0x030012B8)==scroll_pending,"next-scroll-store-operands",r)then
    scroll_store={value=r.R10&0xFFFF,shadow=scroll_pending,executed=false}
    log("next-scroll-store-pre",string.format("address=04000014 bytes=2 value=%04X shadow=%02X",scroll_store.value,scroll_store.shadow),r)
   end
  end
 end)
 hook(0x08000F40,"next-scroll-STRH-completed",function(r)
  if scroll_pending then
   if need(scroll_store and not scroll_store.executed and r.R14==0x085E743C and r.R0==scroll_store.shadow and r.R8==0x030012B8 and r.R9==0x04000000 and (r.R10&0xFFFF)==scroll_store.value and b(0x030012B8)==scroll_store.shadow,"next-scroll-store-completed",r)then
    scroll_store.executed=true
    log("next-scroll-store-executed",string.format("address=04000014 bytes=2 value=%04X shadow=%02X",scroll_store.value,scroll_store.shadow),r)
   end
  end
 end)
 hook(0x085E743C,"next-scroll-stored",function(r)
  if scroll_pending then
   if need(scroll_store and scroll_store.executed and r.R5==0x0300456C and b(0x030012B8)==scroll_pending and scroll_store.shadow==scroll_pending,"next-scroll-store",r)then
    scroll_after=true;scroll_pending=nil;scroll_store=nil;queue("next-display-scroll",r);log("next-display-scroll-post",irq_state(),r)
   end
  end
 end)
]=]
local i,j=source:find(old_scroll,1,true)
assert(i and not source:find(old_scroll,j+1,true),"unique frozen write-only readback predicate")
source=source:sub(1,i-1)..new_scroll..source:sub(j+1)
assert(load(source,"@reviewed-terminal-display-store-observer","t",_ENV))()

