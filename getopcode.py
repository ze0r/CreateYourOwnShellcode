import re
import pyperclip
from keystone import *


def keystone_asm(code, lineNum):
    if (code.startswith('int')):
        encoding = [0xcc]
    else:
        ks = Ks(KS_ARCH_X86, KS_MODE_64)
        try:
            encoding, count = ks.asm(code.split('//')[0])
        except Exception as e:
            print('Error occurred: %s line: %d ' %(code, lineNum) )
            return (b'', 0)

    return (bytes(encoding), len(encoding))

##################################################

f = open('asm.txt', 'r')
ins = [ i.strip() for i in f.readlines() ]
f.close()

lineNumber = 0
label_list = {}
instructions =  []
for i in ins:
    if i.startswith(':label'):
        label = i[1:].strip()
        instructions.append({'lineNum':lineNumber, 'instruction':'', 'opcode':b'', 'length':0, 'IsLabel':True, 'jmpInfo':False})
        label_list.update({ label: lineNumber})
    elif i.startswith('j'):
        op = i[ : 3].strip()
        label = i[3: ].strip()
        if (i.startswith('jmp')):
            instructions.append({'lineNum':lineNumber, 'instruction': i, 'opcode':b'\x90\x90\x90\x90\x90', 'length':5, 'IsLabel':False, 'jmpInfo':{'op': op, 'label':label, 'from': lineNumber, 'to': 0 } })
        else:
            instructions.append({'lineNum':lineNumber, 'instruction': i, 'opcode':b'\x90\x90\x90\x90\x90\x90', 'length':6, 'IsLabel':False, 'jmpInfo':{'op': op, 'label':label, 'from': lineNumber, 'to': 0 } })
    else:
        opcode, length = keystone_asm(i, lineNumber)
        instructions.append({'lineNum':lineNumber, 'instruction': i, 'opcode': opcode, 'length': length, 'IsLabel':False, 'jmpInfo':False})
    lineNumber += 1

for i in instructions:
    jmpInfo = i.get('jmpInfo')
    if (jmpInfo): i['jmpInfo']['to'] = label_list.get(jmpInfo.get('label'))

for i in range(len(instructions) - 1, 0, -1):
    jmpInfo = instructions[i]['jmpInfo']
    if (jmpInfo):
        offset = 0
        for x in range(jmpInfo.get('from'), jmpInfo.get('to'), 1):
            offset += instructions[x]['length']
        if ( (0 < offset) and (offset < 0x82) ):
            offset -= 4
            instructions[i]['length'] -= 4
            if (jmpInfo.get('op') == 'jmp' ):
                offset += 1
                instructions[i]['length'] += 1
            instructions[i]['opcode'] = b'\x90' * instructions[i]['length']
        jmpInfo['to'] = offset
        jmpInfo['from'] = 0


for i in range(0, len(instructions), 1):
    jmpInfo = instructions[i]['jmpInfo']
    if (jmpInfo):
        asm = jmpInfo.get('op') + ' ' + hex( jmpInfo.get('to') )
        opcode, length = keystone_asm(asm, lineNumber)
        instructions[i]['instruction'] = asm
        instructions[i]['opcode'] = opcode

bincodex = b''
for i in instructions:  bincodex += i['opcode']

f = open('ok.bin', 'wb')
f.write(bincodex)
f.close()
