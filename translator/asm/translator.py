import re

REGS = {f"d{i}": i for i in range(4)}
REGS.update({f"a{i}": 4 + i for i in range(4)})
REGS["sp"] = 8
REGS["fp"] = 9

# arg_type
A_NONE  = 0b000
A_IND   = 0b001   # (Ax)
A_DISP  = 0b010   # d(Ax)
A_IDX   = 0b011   # d(Ax,Yx)
A_IMM   = 0b100   # #imm
A_REG   = 0b101   # Rx
A_PRE   = 0b110   # -(Ax)
A_POST  = 0b111   # (Ax)+

# instr_type
ITYPE_SYS, ITYPE_ALU, ITYPE_CTL, ITYPE_IO = 0, 1, 2, 3

INSTRS = {
    # sys
    "hlt": (0b0000, ITYPE_SYS),
    "nop": (0b0001, ITYPE_SYS),
    "mov": (0b0010, ITYPE_SYS),
    # alu
    "cmp": (0b0000, ITYPE_ALU),
    "add": (0b0001, ITYPE_ALU),
    "sub": (0b0010, ITYPE_ALU),
    "mul": (0b0011, ITYPE_ALU),
    "div": (0b0100, ITYPE_ALU),
    "not": (0b0101, ITYPE_ALU),
    "or":  (0b0110, ITYPE_ALU),
    "and": (0b0111, ITYPE_ALU),
    "xor": (0b1000, ITYPE_ALU),
    "asl": (0b1001, ITYPE_ALU),
    "asr": (0b1010, ITYPE_ALU),
    "lsl": (0b1011, ITYPE_ALU),
    "lsr": (0b1100, ITYPE_ALU),
    "pass":(0b1101, ITYPE_ALU),
    "inc": (0b1110, ITYPE_ALU),
    "dec": (0b1111, ITYPE_ALU),
    # control
    "jmp": (0b0000, ITYPE_CTL),
    "beq": (0b0001, ITYPE_CTL),
    "bne": (0b0010, ITYPE_CTL),
    "bmi": (0b0011, ITYPE_CTL),
    "bpl": (0b0100, ITYPE_CTL),
    "bvs": (0b0101, ITYPE_CTL),
    "bcs": (0b0110, ITYPE_CTL),
    "bcc": (0b0111, ITYPE_CTL),
    "call":(0b1000, ITYPE_CTL),
    "ret": (0b1001, ITYPE_CTL),
    # io
    "in":  (0b0000, ITYPE_IO),
    "out": (0b0001, ITYPE_IO),
}

# control flow
BRANCHES_REL = {"beq", "bne", "bmi", "bpl", "bvs", "bcs", "bcc"}
BRANCHES_ABS = {"jmp", "call"}                                   
NO_OPERANDS  = {"hlt", "nop", "ret"}


def b16(v): return [(v >> 8) & 0xFF, v & 0xFF]
def b32(v): return [(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]
def reg_byte(n): return [n & 0x0F]
def disp16(v): return [(v >> 8) & 0xFF, v & 0xFF]


def parse_int(tok):
    t = tok.lstrip("#").strip()
    if t.startswith("'") and t.endswith("'") and len(t) == 3:
        return ord(t[1])
    return int(t, 0)

def parse_operand(tok):
    t = tok.strip().lower()

    if t in REGS:
        return A_REG, {"reg": REGS[t]}

    if tok.startswith("#"):
        return A_IMM, {"imm": parse_int(tok)}

    m = re.fullmatch(r"\((\w+)\)\+", t)
    if m:
        return A_POST, {"reg": REGS[m.group(1)]}
    m = re.fullmatch(r"-\((\w+)\)", t)
    if m:
        return A_PRE, {"reg": REGS[m.group(1)]}
    m = re.fullmatch(r"\((\w+)\)", t)
    if m:
        return A_IND, {"reg": REGS[m.group(1)]}

    m = re.fullmatch(r"(-?\w+)\((\w+),(\w+)\)", t)
    if m:
        return A_IDX, {"disp": int(m.group(1), 0),
                       "reg": REGS[m.group(2)],
                       "idx": REGS[m.group(3)]}
    m = re.fullmatch(r"(-?\w+)\((\w+)\)", t)
    if m:
        return A_DISP, {"disp": int(m.group(1), 0), "reg": REGS[m.group(2)]}

    return "LABEL", {"label": tok}


def make_opcode(lb, instr, itype, a1, a2, is_addr_dest):
    val = (lb << 15) | (instr << 11) | (itype << 8) | (a1 << 5) | (a2 << 2) | (is_addr_dest << 1)
    return b16(val)


def parse_line(line):
    line = line.split(";")[0].strip()
    if not line:
        return None
    if line.endswith(":"):
        return ("label", line[:-1])
    parts = line.split(None, 1)
    mnem = parts[0].lower()
    size = "l"
    if "." in mnem:
        mnem, size = mnem.split(".")
    operands = []
    if len(parts) > 1:
        operands = [o.strip() for o in parts[1].split(",")]
    return ("instr", mnem, size, operands)


def instr_size(mnem, operands):
    if mnem in NO_OPERANDS:
        return 2
    if mnem in BRANCHES_REL:
        return 2 + 2
    if mnem in BRANCHES_ABS:
        return 2 + 4
    size = 2
    for op in operands:
        at, _ = parse_operand(op)
        if at == A_REG:        size += 1
        elif at == A_IMM:      size += 4
        elif at == A_IND:      size += 1
        elif at == A_POST:     size += 1
        elif at == A_PRE:      size += 1
        elif at == A_DISP:     size += 1 + 2
        elif at == A_IDX:      size += 1 + 1 + 2
      
    if mnem in ("in", "out"):
        size += 1
    return size


def gen_instr(mnem, size, operands, labels, pc):
    instr, itype = INSTRS[mnem]
    lb = 1 if size == "l" else 0
    if mnem in ("call", "ret"):
        lb = 1
    if mnem in ("hlt", "nop"):
        lb = 0

    if mnem in NO_OPERANDS:
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0)

    if mnem in BRANCHES_ABS:
        at, info = parse_operand(operands[0])
        target = labels[info["label"]] if at == "LABEL" else parse_int(operands[0])
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0) + b32(target)

    if mnem in BRANCHES_REL:
        at, info = parse_operand(operands[0])
        target = labels[info["label"]] if at == "LABEL" else parse_int(operands[0])
        disp = (target - (pc + 4)) & 0xFFFF
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0) + disp16(disp)

    if mnem in ("in", "out"):
        a1t, a1 = parse_operand(operands[0])
        port = parse_int(operands[1])
        out = make_opcode(lb, instr, itype, a1t, A_NONE, 0)
        if a1t == A_REG:   out += reg_byte(a1["reg"])
        elif a1t == A_IMM: out += b32(a1["imm"])
        elif a1t in (A_IND, A_POST, A_PRE): out += reg_byte(a1["reg"])
        out += [port & 0xFF]
        return out

    src = parse_operand(operands[0])
    dst = parse_operand(operands[1]) if len(operands) > 1 else (A_NONE, {})
    a1t, a1 = src
    a2t, a2 = dst

    mem_types = (A_IND, A_DISP, A_IDX, A_PRE, A_POST)
    is_addr_dest = 0

    if a2t in mem_types:
        a1t, a1, a2t, a2 = a2t, a2, a1t, a1
        is_addr_dest = 1

    out = make_opcode(lb, instr, itype, a1t, a2t, is_addr_dest)

    def emit(at, info):
        bs = []
        if at == A_REG:
            bs += reg_byte(info["reg"])
        elif at == A_IMM:
            bs += b32(info["imm"])
        elif at == A_IND:
            bs += reg_byte(info["reg"])
        elif at == A_POST:
            bs += reg_byte(info["reg"])
        elif at == A_PRE:
            bs += reg_byte(info["reg"])
        elif at == A_DISP:
            bs += reg_byte(info["reg"]) + disp16(info["disp"] & 0xFFFF)
        elif at == A_IDX:
            bs += reg_byte(info["reg"]) + reg_byte(info["idx"]) + disp16(info["disp"] & 0xFFFF)
        return bs

    out += emit(a1t, a1)
    out += emit(a2t, a2)
    return out


def assemble(text):
    parsed = []
    for line in text.splitlines():
        p = parse_line(line)
        if p:
            parsed.append(p)

    labels = {}
    pc = 0
    for p in parsed:
        if p[0] == "label":
            labels[p[1]] = pc
        else:
            _, mnem, size, operands = p
            pc += instr_size(mnem, operands)

    out = []
    pc = 0
    for p in parsed:
        if p[0] == "label":
            continue
        _, mnem, size, operands = p
        code = gen_instr(mnem, size, operands, labels, pc)
        out += code
        pc += len(code)
    return out
    
