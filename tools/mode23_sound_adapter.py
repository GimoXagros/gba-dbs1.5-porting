"""Typed mode23 source-command adapter; new songs require installed reviewed bundle."""
import hashlib,json
REPORT='4FD3231076F583BF0B070D1A6E531EB8DB067E60C5FBAE9EAC5A2D708D8091A2'
AUDIO='3F59CECB61F4A1C43DEA8B9A861F790470B5E8BAB913E205AF4DBECF441DB90A'
MAPPING={0x04:(0x00,4),0x18:(0x04,4),0x1C:(0x05,4),0x24:(0x07,4),0x30:(0x0A,4),0x6C:(0x19,4),0x7C:(0x70,1),0x7D:(0x23,1),0x84:(0x71,1),0x98:(0x72,1),0x9A:(0x5A,1),0xAC:(0x4E,1),0xD5:(0x73,1),0xD6:(0x74,1),0xD7:(0x75,2),0xD9:(0x76,1),0xDA:(0x77,1),0xF0:(0x78,4),0xF4:(0x79,4)}
def assembly(report,audio):
 assert hashlib.sha256(report).hexdigest().upper()==REPORT
 assert hashlib.sha256(audio).hexdigest().upper()==AUDIO
 info=json.loads(report);assert {(x['source_id'],x['priority']) for x in info['commands']}=={(k,v[1]) for k,v in MAPPING.items()}
 # The source census proves every caller belongs to this finite domain.
 # Unknown table bytes deliberately remain FF, not a guessed native alias.
 values=[MAPPING[x][0] if x in MAPPING else 255 for x in range(256)]
 return """
m23_sound:
push {r4-r11,lr}
ldr r8,m23_sound_table
ldrb r8,[r8,r0]
mov r9,r1
mov r10,#0
bl 0x080d15c0
pop {r4-r11,lr}
bx lr
m23_sound_table: .word m23_sound_ids
m23_sound_ids:
"""+'.byte '+','.join(map(str,values))+'\n.align 2\n'
