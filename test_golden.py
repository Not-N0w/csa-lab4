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

JOURNAL = "/tmp/journal.log"


def _block_str(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _block_str, Dumper=yaml.SafeDumper)


def clean(text):
    return "".join(c if c == "\n" or 32 <= ord(c) < 127 else "." for c in text)


def parse_stdin(stdin, mode):
    if mode == "numbers":
        return [int(x.strip(), 0) for x in str(stdin).replace(",", " ").split()]
    return [ord(c) for c in stdin]


def strip_io(text):
    out, skip = [], False
    for line in text.splitlines():
        if line.startswith("=== IO INPUT ==="):
            skip = True
        elif line.startswith("=== TRACE"):
            skip = False
            out.append(line)
        elif line.startswith("=== IO OUTPUT ==="):
            skip = True
        elif not skip:
            out.append(line)
    return "\n".join(out)


def clip_journal(text, head=100, tail=100):
    lines = text.splitlines()
    if len(lines) <= head + tail:
        return text
    omitted = len(lines) - head - tail
    return "\n".join(lines[:head] + [f"... ({omitted} строк опущено) ..."] + lines[-tail:])


def pipeline(source, stdin, in_mode, run_mode):
    if run_mode == "asm":
        asm_text, dm = source, {}
    else:
        asm_text, dm = generate_asm(source), string_data()
    code = assemble(asm_text)
    words = parse_stdin(stdin, in_mode)
    io_in = {0: words} if words else {}
    buf = io.StringIO()
    with redirect_stdout(buf):
        model.run(code, dm, io_in, log_path=JOURNAL, disasm=disasm_map(asm_text))
    journal = clip_journal(strip_io(open(JOURNAL).read()))
    return code_hex(asm_text), clean(buf.getvalue()), clean(journal)


@pytest.mark.parametrize("path", CASES, ids=[os.path.basename(p) for p in CASES])
def test(path):
    c = yaml.safe_load(open(path))
    hexlist, stdout, journal = pipeline(
        c["in_source"], c.get("in_stdin", ""),
        c.get("in_mode", "str"), c.get("run_mode", "lisp"),
    )
    if UPDATE:
        c["out_code_hex"] = hexlist
        c["out_stdout"] = stdout
        c["out_log"] = journal
        yaml.safe_dump(c, open(path, "w"), allow_unicode=True, sort_keys=False)
    else:
        assert hexlist.strip() == c["out_code_hex"].strip(), "дизассемблер не совпал"
        assert stdout.strip() == c["out_stdout"].strip(), "вывод не совпал"
        assert journal.strip() == c["out_log"].strip(), "журнал не совпал"