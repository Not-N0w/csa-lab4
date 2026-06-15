import re 
from common import *

def generate_sig_instr(signals_active, mode):
    instr = "1"
    clr_mode = mode[2:] 
    
    instr = instr + sig_modes[clr_mode]
    for i in all_signals:
        if i in signals_active:
            instr = instr + "1"
        else:
            instr = instr + "0"
    return instr

def generate_jmp_instr(jmp_type, template, label):
    instr = "0"
    clr_type = jmp_type[2:]

    instr = instr + jmp_types[clr_type]

    if clr_type != "simple" and not clr_type in ["ja1", "ja2"]:
        instr = instr + template
    else: 
        instr = instr + "0"*4

    if clr_type in ["ja1", "ja2"]:
        instr = instr + "0"*9
    else:
        addr = bin(labels[label])[2:]
        addr = "0"*(9-len(addr)) + addr
        instr = instr + addr 
        
    instr = instr + "0"*55

    return instr


labels = {}
print(len(all_signals))

with open(microinstructions_file, "wb") as result_file:
    with open('/Users/yaroslavmakogon/Documents/itmo/csa/csa-lab4/processor_model/control_unit/microcode/microcode.txt', 'r') as file:
        str_number = 0
        for line in file:
            clean_line = line.strip()
            if re.match(r'.*:$', clean_line): 
                labels[clean_line[:-1]] = str_number
            elif clean_line != '':
                str_number += 1

        file.seek(0)
        str_number = 0
        for line in file:
            clean_line = line.strip()

            lexems = clean_line.split()
            
            instr = ""
            if clean_line == '' or re.match(r'.*:$', lexems[0]): 
                continue
            if re.match(r'^sig', lexems[0]):
                mode = "t.simple"
                signals = lexems[1:]
                if re.match(r'^t\..*', lexems[1]):
                    mode = lexems[1]
                    signals = lexems[2:]
                instr = generate_sig_instr(signals, mode) 
            if re.match(r'^jmp', lexems[0]):
                jmp_type = "t.simple"
                template = ""
                label = ""
                if re.match(r'^t\..*', lexems[1]):
                    jmp_type = lexems[1]
                    if len(lexems) > 2:
                        template = lexems[2]
                        label = lexems[3]
                else:
                    label = lexems[1]
                instr = generate_jmp_instr(jmp_type, template, label)
            
            print(clean_line)
            print (str_number, ": ", instr)
            
            value = int(instr, 2)
            result_file.write(value.to_bytes(11, byteorder="big"))
            
            str_number+=1
