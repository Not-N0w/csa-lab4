from translator.asm.translator import assemble

variables = {}
functions = {}
current_params = None

STRING_BASE = 0x1000
ARRAY_BASE = 0x2000
strings = {}
arrays = {}
_str_next = [STRING_BASE]
_arr_next = [ARRAY_BASE]
_label_n = [0]

BINOPS = {"+": "add", "-": "sub", "*": "mul", "/": "div", "and": "and", "or": "or"}
CMP = {"=": "beq", "!=": "bne", "<": "bmi"}


def new_label(p):
    _label_n[0] += 1
    return f"{p}_{_label_n[0]}"


def var_addr(name):
    if name not in variables:
        variables[name] = len(variables) * 4
    return variables[name]


def string_addr(text):
    if text not in strings:
        strings[text] = _str_next[0]
        _str_next[0] += (len(text) + 1) * 4
    return strings[text]


def alloc_array(name, n):
    if name not in arrays:
        arrays[name] = _arr_next[0]
        _arr_next[0] += n * 4
    return arrays[name]


def gen(node):
    global current_params
    if not isinstance(node, list):
        if isinstance(node, int):
            return [f"mov.l #{node}, D0"]
        if isinstance(node, str) and node.startswith('"'):
            return [f"mov.l #{string_addr(node[1:-1])}, D0"]
        if current_params and node in current_params:
            return [f"mov.l {current_params[node]}(FP), D0"]
        return [f"mov.l #{var_addr(node)}, A0", "mov.l (A0), D0"]

    op = node[0]

    if op in BINOPS:
        return (gen(node[2]) + ["mov.l D0, -(SP)"] + gen(node[1])
                + ["mov.l (SP)+, D1", f"{BINOPS[op]}.l D1, D0"])

    if op == "setq":
        return gen(node[2]) + [f"mov.l #{var_addr(node[1])}, A0", "mov.l D0, (A0)"]

    if op in CMP:
        t, e = new_label("true"), new_label("cend")
        return (gen(node[2]) + ["mov.l D0, -(SP)"] + gen(node[1])
                + ["mov.l (SP)+, D1", "cmp.l D1, D0", f"{CMP[op]} {t}",
                   "mov.l #0, D0", f"jmp {e}", f"{t}:", "mov.l #1, D0", f"{e}:"])

    if op == "progn":
        code = []
        for e in node[1:]:
            code += gen(e)
        return code

    if op == "if":
        el, end = new_label("else"), new_label("endif")
        return (gen(node[1]) + ["cmp.l #0, D0", f"beq {el}"] + gen(node[2])
                + [f"jmp {end}", f"{el}:"] + gen(node[3]) + [f"{end}:"])

    if op == "while":
        lp, ex = new_label("loop"), new_label("exit")
        code = [f"{lp}:"] + gen(node[1]) + ["cmp.l #0, D0", f"beq {ex}"]
        for e in node[2:]:
            code += gen(e)
        return code + [f"jmp {lp}", f"{ex}:"]

    if op == "defun":
        name, params, body = node[1], node[2], node[3:]
        n = len(params)
        table = {p: (n - i) * 4 for i, p in enumerate(params)}
        functions[name] = table
        over = new_label("over")
        code = [f"jmp {over}", f"{name}:"]
        prev, current_params = current_params, table
        for form in body:
            code += gen(form)
        current_params = prev
        return code + ["ret", f"{over}:"]

    if op == "print":
        return gen(node[1]) + ["out D0, #1"]

    if op == "prints":
        lp, ep = new_label("ploop"), new_label("pend")
        return (gen(node[1]) + ["mov.l D0, A0", f"{lp}:", "mov.l (A0)+, D1",
                "cmp.l #0, D1", f"beq {ep}", "out D1, #1", f"jmp {lp}", f"{ep}:"])

    if op == "read":
        return ["in D0, #0"]

    if op == "alloc":
        alloc_array(node[1], node[2])
        return []

    if op == "lget":
        base = alloc_array(node[1], 0)
        return (gen(node[2]) + ["mov.l #4, D1", "mul.l D1, D0",
                f"mov.l #{base}, D1", "add.l D1, D0", "mov.l D0, A0", "mov.l (A0), D0"])

    if op == "lset":
        base = alloc_array(node[1], 0)
        return (gen(node[3]) + ["mov.l D0, -(SP)"] + gen(node[2])
                + ["mov.l #4, D1", "mul.l D1, D0", f"mov.l #{base}, D1", "add.l D1, D0",
                   "mov.l D0, A0", "mov.l (SP)+, D0", "mov.l D0, (A0)"])

    if op in functions:
        args = node[1:]
        code = []
        for a in args:
            code += gen(a) + ["mov.l D0, -(SP)"]
        code += [f"call {op}"]
        if args:
            code += [f"add.l #{len(args) * 4}, SP"]
        return code

    raise NotImplementedError(f"unknown form: {op}")


def get_lexems(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == ";":
            while i < len(s) and s[i] != "\n":
                i += 1
        elif c.isspace():
            i += 1
        elif c in "()":
            out.append(c); i += 1
        elif c == '"':
            j = i + 1
            while j < len(s) and s[j] != '"':
                j += 1
            out.append(s[i:j + 1]); i = j + 1
        else:
            j = i
            while j < len(s) and not s[j].isspace() and s[j] not in "()":
                j += 1
            out.append(s[i:j]); i = j
    return out


def atom(tok):
    if tok.startswith('"'):
        return tok
    try:
        return int(tok)
    except ValueError:
        return tok


def parse(text):
    stack = [[]]
    for t in get_lexems(text):
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        else:
            stack[-1].append(atom(t))
    return stack[0]


def _reset():
    variables.clear()
    functions.clear()
    strings.clear()
    arrays.clear()
    _str_next[0] = STRING_BASE
    _arr_next[0] = ARRAY_BASE
    _label_n[0] = 0


def generate_asm(text):
    _reset()
    code = ["mov.l #0xF000, SP", "mov.l #0xF000, FP"]
    for form in parse(text):
        code += gen(form)
    code += ["hlt"]
    return "\n".join(code)


def string_data():
    dm = {}
    for text, addr in strings.items():
        a = addr
        for ch in text:
            w = ord(ch)
            dm[a], dm[a + 1], dm[a + 2], dm[a + 3] = (w >> 24) & 0xFF, (w >> 16) & 0xFF, (w >> 8) & 0xFF, w & 0xFF
            a += 4
        dm[a] = dm[a + 1] = dm[a + 2] = dm[a + 3] = 0
    return dm

