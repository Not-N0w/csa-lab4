from translator.lisp.translator import generate_asm, string_data
from translator.asm.translator import assemble, disasm_map
from processor_model.model import run
from translator.binio import write_im, write_dm, read_im, read_dm


LISP_FILE = "code.lisp"
ASM_FILE = "code.asm"
IM_BIN = "out.im.bin"
DM_BIN = "out.dm.bin"
IO_IN = "io.in"
LOG = "journal.log"


def build(layer):
    if layer in ("lisp", ""):
        asm = generate_asm(open(LISP_FILE).read())
        dm = string_data()
    else:
        asm = open(ASM_FILE).read()
        dm = {}
    write_im(assemble(asm), IM_BIN)
    write_dm(dm, DM_BIN)
    return disasm_map(asm)


def start(layer):
    disasm = build(layer)
    im = read_im(IM_BIN)
    dm = read_dm(DM_BIN)
    io = eval(open(IO_IN).read())
    run(im, dm, io, 200000, LOG, disasm)


if __name__ == "__main__":
    start(input("RUN: "))