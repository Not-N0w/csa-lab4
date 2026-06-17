import re

REGS = {f"d{i}": i for i in range(4)}
REGS.update({f"a{i}": 4 + i for i in range(4)})
REGS["sp"] = 8
REGS["fp"] = 9

A_NONE, A_IND, A_DISP, A_IDX, A_IMM, A_REG, A_PRE, A_POST = range(8)
MEM_TYPES = (A_IND, A_DISP, A_IDX, A_PRE, A_POST)

SYS, ALU, CTL, IO = 0, 1, 2, 3
INSTRS = {
    "hlt": (0, SYS), "nop": (1, SYS), "mov": (2, SYS),
    "cmp": (0, ALU), "add": (1, ALU), "sub": (2, ALU), "mul": (3, ALU),
    "div": (4, ALU), "not": (5, ALU), "or": (6, ALU), "and": (7, ALU),
    "xor": (8, ALU), "asl": (9, ALU), "asr": (10, ALU), "lsl": (11, ALU),
    "lsr": (12, ALU), "pass": (13, ALU), "inc": (14, ALU), "dec": (15, ALU),
    "jmp": (0, CTL), "beq": (1, CTL), "bne": (2, CTL), "bmi": (3, CTL),
    "bpl": (4, CTL), "bvs": (5, CTL), "bcs": (6, CTL), "bcc": (7, CTL),
    "call": (8, CTL), "ret": (9, CTL),
    "in": (0, IO), "out": (1, IO),
}
BRANCHES_REL = {"beq", "bne", "bmi", "bpl", "bvs", "bcs", "bcc"}
BRANCHES_ABS = {"jmp", "call"}
NO_OPERANDS = {"hlt", "nop", "ret"}


def b16(v): return [(v >> 8) & 0xFF, v & 0xFF]
def b32(v): return [(v >> i) & 0xFF for i in (24, 16, 8, 0)]


def parse_int(tok):
    t = tok.lstrip("#").strip()
    if len(t) == 3 and t[0] == t[-1] == "'":
        return ord(t[1])
    return int(t, 0)


def parse_operand(tok):
    t = tok.strip().lower()
    if t in REGS:
        return A_REG, {"reg": REGS[t]}
    if tok.startswith("#"):
        return A_IMM, {"imm": parse_int(tok)}
    for pat, at in ((r"\((\w+)\)\+", A_POST), (r"-\((\w+)\)", A_PRE), (r"\((\w+)\)", A_IND)):
        m = re.fullmatch(pat, t)
        if m:
            return at, {"reg": REGS[m.group(1)]}
    m = re.fullmatch(r"(-?\w+)\((\w+),(\w+)\)", t)
    if m:
        return A_IDX, {"disp": int(m.group(1), 0), "reg": REGS[m.group(2)], "idx": REGS[m.group(3)]}
    m = re.fullmatch(r"(-?\w+)\((\w+)\)", t)
    if m:
        return A_DISP, {"disp": int(m.group(1), 0), "reg": REGS[m.group(2)]}
    return "LABEL", {"label": tok}


def make_opcode(lb, instr, itype, a1, a2, is_addr_dest):
    return b16((lb << 15) | (instr << 11) | (itype << 8) | (a1 << 5) | (a2 << 2) | (is_addr_dest << 1))


def parse_line(line):
    line = line.split(";")[0].strip()
    if not line:
        return None
    if line.endswith(":"):
        return ("label", line[:-1])
    parts = line.split(None, 1)
    mnem, size = parts[0].lower(), "l"
    if "." in mnem:
        mnem, size = mnem.split(".")
    operands = []
    if len(parts) > 1:
        depth, cur = 0, ""
        for ch in parts[1]:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                operands.append(cur.strip()); cur = ""
            else:
                cur += ch
        if cur.strip():
            operands.append(cur.strip())
    return ("instr", mnem, size, operands)


def operand_size(at):
    return {A_REG: 1, A_IMM: 4, A_IND: 1, A_POST: 1, A_PRE: 1, A_DISP: 3, A_IDX: 4}.get(at, 0)


def instr_size(mnem, operands):
    if mnem in NO_OPERANDS:
        return 2
    if mnem in BRANCHES_REL:
        return 4
    if mnem in BRANCHES_ABS:
        return 6
    if mnem in ("in", "out"):
        return 4
    return 2 + sum(operand_size(parse_operand(op)[0]) for op in operands)


def emit_operand(at, info):
    if at in (A_REG, A_IND, A_POST, A_PRE):
        return [info["reg"] & 0xF]
    if at == A_IMM:
        return b32(info["imm"])
    if at == A_DISP:
        return [info["reg"] & 0xF] + b16(info["disp"] & 0xFFFF)
    if at == A_IDX:
        return [info["reg"] & 0xF, info["idx"] & 0xF] + b16(info["disp"] & 0xFFFF)
    return []


def gen_instr(mnem, size, operands, labels, pc):
    instr, itype = INSTRS[mnem]
    lb = 0 if mnem in ("hlt", "nop") else (1 if size == "l" or mnem in ("call", "ret") else 0)

    if mnem in NO_OPERANDS:
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0)

    if mnem in BRANCHES_ABS:
        at, info = parse_operand(operands[0])
        target = labels[info["label"]] if at == "LABEL" else parse_int(operands[0])
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0) + b32(target)

    if mnem in BRANCHES_REL:
        at, info = parse_operand(operands[0])
        target = labels[info["label"]] if at == "LABEL" else parse_int(operands[0])
        return make_opcode(lb, instr, itype, A_NONE, A_NONE, 0) + b16((target - (pc + 4)) & 0xFFFF)

    if mnem in ("in", "out"):
        a1t, a1 = parse_operand(operands[0])
        out = make_opcode(lb, instr, itype, a1t, A_NONE, 0) + emit_operand(a1t, a1)
        return out + [parse_int(operands[1]) & 0xFF]

    a1t, a1 = parse_operand(operands[0])
    a2t, a2 = parse_operand(operands[1]) if len(operands) > 1 else (A_NONE, {})
    is_addr_dest = 0
    if a2t in MEM_TYPES:
        a1t, a1, a2t, a2 = a2t, a2, a1t, a1
        is_addr_dest = 1
    return make_opcode(lb, instr, itype, a1t, a2t, is_addr_dest) + emit_operand(a1t, a1) + emit_operand(a2t, a2)


def assemble(text):
    parsed = [p for p in (parse_line(l) for l in text.splitlines()) if p]
    labels, pc = {}, 0
    for p in parsed:
        if p[0] == "label":
            labels[p[1]] = pc
        else:
            pc += instr_size(p[1], p[3])
    out, pc = [], 0
    for p in parsed:
        if p[0] == "label":
            continue
        code = gen_instr(p[1], p[2], p[3], labels, pc)
        out += code
        pc += len(code)
    return out


def disasm_map(text):
    parsed = [p for p in (parse_line(l) for l in text.splitlines()) if p]
    labels, pc = {}, 0
    for p in parsed:
        if p[0] == "label":
            labels[p[1]] = pc
        else:
            pc += instr_size(p[1], p[3])
    result, pc = {}, 0
    for p in parsed:
        if p[0] == "label":
            continue
        _, mnem, size, operands = p
        result[pc] = _mnemonic_text(mnem, size, operands)
        pc += instr_size(mnem, operands)
    return result


def _mnemonic_text(mnem, size, operands):
    no_sfx = NO_OPERANDS | BRANCHES_REL | BRANCHES_ABS | {"in", "out"}
    sfx = "." + size if mnem not in no_sfx else ""
    if operands:
        return f"{mnem}{sfx} " + ", ".join(operands)
    return f"{mnem}{sfx}"


def code_hex(text):
    parsed = [p for p in (parse_line(l) for l in text.splitlines()) if p]
    labels, pc = {}, 0
    for p in parsed:
        if p[0] == "label":
            labels[p[1]] = pc
        else:
            pc += instr_size(p[1], p[3])
    rows, pc = [], 0
    for p in parsed:
        if p[0] == "label":
            rows.append((None, None, p[1] + ":"))
            continue
        _, mnem, size, operands = p
        code = gen_instr(mnem, size, operands, labels, pc)
        hexcode = "".join(f"{b:02X}" for b in code)
        rows.append((pc, hexcode, _mnemonic_text(mnem, size, operands)))
        pc += len(code)
    width = max((len(h) for _, h, _ in rows if h), default=0)
    lines = []
    for addr, hexcode, mnem in rows:
        if addr is None:
            lines.append(mnem)
        else:
            lines.append(f"{addr:04X} - {hexcode:<{width}} - {mnem}")
    return "\n".join(lines)