
variables = {}
functions = {}
current_params = None
 
STRING_BASE = 0x1000
strings = {}
_str_next = [STRING_BASE]
def string_addr(text):
    if text not in strings:
        strings[text] = _str_next[0]
        _str_next[0] += (len(text) + 1) * 4
    return strings[text]
 
_label_n = [0]
def new_label(prefix):
    _label_n[0] += 1
    return f"{prefix}_{_label_n[0]}"
 
def var_addr(name):
    if name not in variables:
        variables[name] = len(variables) * 4
    return variables[name]
 
 
BINOPS = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div",
    "and": "and",
    "or": "or",
}
 
 
def is_atom(node):
    return not isinstance(node, list)
 
 
def is_number(node):
    return isinstance(node, int)
 
 
def gen(node):
    global current_params
    if is_atom(node):
        if is_number(node):
            return [f"mov.l #{node}, D0"]
        if isinstance(node, str) and node.startswith('"'):
            text = node[1:-1]
            addr = string_addr(text)
            return [f"mov.l #{addr}, D0"]
        if current_params and node in current_params:
            off = current_params[node]
            return [f"mov.l {off}(FP), D0"]
        addr = var_addr(node)
        return [f"mov.l #{addr}, A0",
                f"mov.l (A0), D0"]
 
    op = node[0]
 
    if op in BINOPS:
        a, b = node[1], node[2]
        mnem = BINOPS[op]
        code = []
       
        code += gen(b)
        code += ["mov.l D0, -(SP)"]
        code += gen(a)
        code += ["mov.l (SP)+, D1"]
        code += [f"{mnem}.l D1, D0"]
        return code
 
    if op == "setq":
        name, expr = node[1], node[2]
        addr = var_addr(name)
        code = []
        code += gen(expr)
        code += [f"mov.l #{addr}, A0",
                 f"mov.l D0, (A0)"]
        return code
 
    if op in ("=", "<"):
        a, b = node[1], node[2]
        code = []
        code += gen(b)
        code += ["mov.l D0, -(SP)"]
        code += gen(a)
        code += ["mov.l (SP)+, D1"]
        code += ["cmp.l D1, D0"]
        true_l = new_label("true")
        end_l = new_label("cend")
        if op == "=":
            code += [f"beq {true_l}"]
        else:
            code += [f"bmi {true_l}"]
        code += ["mov.l #0, D0"]
        code += [f"jmp {end_l}"]
        code += [f"{true_l}:"]
        code += ["mov.l #1, D0"]
        code += [f"{end_l}:"]
        return code
 
    if op == "if":
        cond, then_exp, else_exp = node[1], node[2], node[3]
        else_l = new_label("else")
        end_l = new_label("endif")
        code = []
        code += gen(cond)
        code += ["cmp.l #0, D0"]
        code += [f"beq {else_l}"]
        code += gen(then_exp)
        code += [f"jmp {end_l}"]
        code += [f"{else_l}:"]
        code += gen(else_exp)
        code += [f"{end_l}:"]
        return code
 
    if op == "while":
        cond, do = node[1], node[2:]
        loop_l = new_label("loop")
        exit_l = new_label("exit")
        code = []
        code += [f"{loop_l}:"]
        code += gen(cond)
        code += ["cmp.l #0, D0"]
        code += [f"beq {exit_l}"]
        for i in do:
            code += gen(i)
        code += [f"jmp {loop_l}"]
        code += [f"{exit_l}:"]
        return code
 
    if op == "defun":
        name, params, body = node[1], node[2], node[3:]
        n = len(params)
        param_table = {p: (n - i) * 4 for i, p in enumerate(params)}
        functions[name] = param_table
 
        over_l = new_label("over")
        code = [f"jmp {over_l}"]
        code += [f"{name}:"]
        prev = current_params
        current_params = param_table
        for form in body:
            code += gen(form)
        current_params = prev
        code += ["ret"]
        code += [f"{over_l}:"]
        return code
 
    if op == "print":
        code = gen(node[1])
        code += ["out D0, #1"]
        return code
 

    if op == "prints":
        code = gen(node[1])
        lp = new_label("ploop")
        ep = new_label("pend")
        code += ["mov.l D0, A0"]
        code += [f"{lp}:"]
        code += ["mov.l (A0)+, D1"]
        code += ["cmp.l #0, D1"]
        code += [f"beq {ep}"]
        code += ["out D1, #1"]
        code += [f"jmp {lp}"]
        code += [f"{ep}:"]
        return code
 
    if op == "read":
        return ["in D0, #0"]
 
    if op in functions:
        args = node[1:]
        code = []
        for a in args:
            code += gen(a)
            code += ["mov.l D0, -(SP)"]
        code += [f"call {op}"]
        if args:
            code += [f"add.l #{len(args) * 4}, SP"]
        return code
 
    raise NotImplementedError(f"unknown form: {op}")
 

def get_lexems(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c in "()":
            out.append(c); i += 1; continue
        if c == '"':
            j = i + 1
            while j < len(s) and s[j] != '"': j += 1
            out.append(s[i:j+1]); i = j + 1; continue
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

def parse_program(lexems):
    """Возвращает СПИСОК форм верхнего уровня: [form1, form2, ...]."""
    stack = [[]]
    for t in lexems:
        if t == "(":
            new = []; stack[-1].append(new); stack.append(new)
        elif t == ")":
            stack.pop()
        else:
            stack[-1].append(atom(t))
    return stack[0]

def parse(text):
    return parse_program(get_lexems(text))
 
def generate_asm(input):
    tree = parse(input)

    variables.clear()
    functions.clear()
    strings.clear()
    _str_next[0] = STRING_BASE
    _label_n[0] = 0
    code = ["mov.l #0xF000, SP", "mov.l #0xF000, FP"]
    for form in tree:
        code += gen(form)
    code += ["hlt"]
    return string_data(), "\n".join(code)
 


def string_data():
    dm = {}
    for text, addr in strings.items():
        a = addr
        for ch in text:
            w = ord(ch)
            dm[a]   = (w >> 24) & 0xFF
            dm[a+1] = (w >> 16) & 0xFF
            dm[a+2] = (w >> 8) & 0xFF
            dm[a+3] = w & 0xFF
            a += 4
        dm[a] = 0; dm[a+1] = 0; dm[a+2] = 0; dm[a+3] = 0
    return dm