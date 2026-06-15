from translator.lisp.translator import generate_asm, string_data
from translator.asm.translator import assemble
from processor_model.model import run

LISP_FILE = "code.lisp"
ASM_FILE = "code.asm"
SIMULATION_CONF = "simulation.conf"
IO_IN = "io.in"

def start(layer):
    im_data = []
    io_data = eval(open("io.in").read())
    dm_data = {}
    if layer == "lisp" or layer == "":        
        with open(LISP_FILE, 'r') as file:
            dm_data, asm = generate_asm(file.read())
            print(asm)
            im_data = assemble(asm)
    elif layer == "asm":
         with open(ASM_FILE, 'r') as file:
            im_data = assemble(file.read())
    

    run(im_data,dm_data, io_data, 20000, SIMULATION_CONF)


layer = input("RUN: ")
start(layer)