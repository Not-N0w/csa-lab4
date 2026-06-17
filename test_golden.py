import glob
import io
import os
from contextlib import redirect_stdout

import yaml
import pytest

from translator.lisp.translator import generate_asm, string_data
from translator.asm.translator import assemble, code_hex, disasm_map
import processor_model.model as model

UPDATE = os.environ.get("UPDATE") == "1"
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = sorted(glob.glob(os.path.join(HERE, "golden", "*.yml")))
assert CASES, "golden-тесты не найдены в golden/*.yml"

def parse_stdin(stdin, mode):
    if mode == "numbers":
        return [int(x.strip(), 0) for x in stdin.split(",") if x.strip()]
    return [ord(c) for c in stdin]

def pipeline(source, stdin, in_mode, run_mode):
    if run_mode == "lisp":
        asm_text = generate_asm(source)
        dm = string_data()
    else:  # asm
        asm_text = source
        dm = {}
    code = assemble(asm_text)
    words = parse_stdin(stdin, in_mode)
    io_in = {0: words} if words else {}
    buf = io.StringIO()
    with redirect_stdout(buf):
        model.run(code, dm, io_in,
                  log_path="/tmp/j.log", disasm=disasm_map(asm_text))
    return code_hex(asm_text), buf.getvalue()


@pytest.mark.parametrize("path", CASES, ids=[os.path.basename(p) for p in CASES])
def test(path):
    c = yaml.safe_load(open(path))
    hexlist, stdout = pipeline(c["in_source"], c.get("in_stdin", ""),c.get("in_mode", "str"), c.get("run_mode", "lisp"))
    if UPDATE:
        c["out_code_hex"] = hexlist
        c["out_stdout"] = stdout
        yaml.safe_dump(c, open(path, "w"), allow_unicode=True, sort_keys=False)
    else:
        assert hexlist.strip() == c["out_code_hex"].strip(), "дизассемблер не совпал"
        assert stdout.strip() == c["out_stdout"].strip(), "вывод не совпал"