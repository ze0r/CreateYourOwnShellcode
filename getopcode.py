import re
import pyperclip
from keystone import *

lineNumber = 0
viewedASMCODE = ""

def keystone_asm(code):
    global viewedASMCODE, lineNumber

    ks = Ks(KS_ARCH_X86, KS_MODE_64)
    try:
        encoding, count = ks.asm(code.split('//')[0])
    except Exception as e:
        print('Error occurred: %s line: %d ' %(code, lineNumber) )
        return ('', 0)
    lineNumber += 1
    if (code.startswith('int')):
        encoding = [0xcc]

    result = ''
    for i in encoding:
        result += '\\x%02x' % (i)
    viewedASMCODE += result

    result = '"%s" %s // %s \r\n' % (result," " * (50 - len(result)), code)

    return (result, len(encoding))

##################################################

f = open('asm.txt', 'r')
instructions = [ i.strip() for i in f.readlines() ]
f.close()

current_instruction_position = 0
label_list = {}
for i in instructions:
    if i.startswith(':label'):
        label = i[1:].strip()
        label_list.update({ label : current_instruction_position })
        continue

    if i.startswith('j'):
        current_instruction_position += 2
        label = re.search(' [A-Za-z0-9].+?( |$)', i).group(0).strip()
        if (label_list.get(label)):
            current_instruction_position += 4
            if (i.startswith('jmp')):
                current_instruction_position -= 1
    else:
        opcode, length = keystone_asm(i)
        current_instruction_position += length

result = ""
viewedASMCODE = ""
current_instruction_position = 0
for i in instructions:

    if i.startswith(':label'): continue
    if i.startswith('j'):
        label = re.search(' [A-Za-z0-9].+?( |$)', i).group(0).strip()
        pos =  label_list.get(label) - current_instruction_position
        asm = i[:3] + '     ' + hex(pos & 0xffffffff)
        opcode, length = keystone_asm(asm)
    else:
        opcode, length = keystone_asm(i)

    current_instruction_position += length
    result += opcode

result += "\"\\x90\";"

print(result)
pyperclip.copy(result)

# for i in range(0, len(viewedASMCODE), 64): print('"%s"' % viewedASMCODE[i : i+64])