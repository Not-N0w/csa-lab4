from processor_model.basic_elements import *
from processor_model.control_unit.control_unit import ControlUnit
import re

registers = {
    "d0": Register(),
    "d1": Register(),
    "d2": Register(),
    "d3": Register(),
    "a0": Register(),
    "a1": Register(),
    "a2": Register(),
    "a3": Register(),
    "sp": Register(),
    "fp": Register(),
    "dr": Register(),
    "ar": Register(),
    "br": Register(),
    "pc": Register(),
    "nzvc": Register(4),
    "op1": Register(),
    "op2": Register(),
    "alu_res": Register(),
}

muxes = {
    "mux1": Mux(),
    "mux2": Mux(),
    "mux3": Mux(),
    "mux4": Mux(),
    "mux5": Mux(),
    "mux6": Mux(),
}
alu = ALU(registers["nzvc"])
sums = {
    "sum1": Sum(),
    "sum2": Sum(),
}
memory_units = {
    "im": MemoryUnit(),
    "dm": MemoryUnit(),
    "io": IODevice(n=3, delay=5),
}


registers["d0"].set_source(registers["alu_res"])
registers["d1"].set_source(registers["alu_res"])
registers["d2"].set_source(registers["alu_res"])
registers["d3"].set_source(registers["alu_res"])
registers["a0"].set_source(registers["alu_res"])
registers["a1"].set_source(registers["alu_res"])
registers["a2"].set_source(registers["alu_res"])
registers["a3"].set_source(registers["alu_res"])
registers["sp"].set_source(registers["alu_res"])
registers["fp"].set_source(registers["alu_res"])

muxes["mux1"].set_options({
    "d0": registers["d0"],
    "d1": registers["d1"],
    "d2": registers["d2"],
    "d3": registers["d3"],
    "a0": registers["a0"],
    "a1": registers["a1"],
    "a2": registers["a2"],
    "a3": registers["a3"],
    "sp": registers["sp"],
    "fp": registers["fp"],
    "ar": registers["ar"],
    "mux4": muxes["mux4"]
})
muxes["mux2"].set_options({
    "d0": registers["d0"],
    "d1": registers["d1"],
    "d2": registers["d2"],
    "d3": registers["d3"],
    "a0": registers["a0"],
    "a1": registers["a1"],
    "a2": registers["a2"],
    "a3": registers["a3"],
    "sp": registers["sp"],
    "fp": registers["fp"],
    "ar": registers["ar"],
    "mux4": muxes["mux4"]
})
muxes["mux3"].set_options({
    "pc": registers["pc"],
    "alu_res": registers["alu_res"],
    "dm": memory_units["dm"],
    "io": memory_units["io"],
})
muxes["mux4"].set_options({
    "br": registers["br"],
    "dr": registers["dr"],
})
muxes["mux5"].set_options({
    "br": registers["br"],
    "dr": registers["dr"],
    "1": NumberSource(1),
    "2": NumberSource(2),
    "4": NumberSource(4),
})

registers["op1"].set_source(muxes["mux1"])
registers["op2"].set_source(muxes["mux2"])
alu.set_op1(registers["op1"])
alu.set_op2(registers["op2"])
registers["alu_res"].set_source(alu)
registers["ar"].set_source(registers["alu_res"])

memory_units["im"].set_addr_source(registers["pc"])
registers["br"].set_source(memory_units["im"])

memory_units["dm"].set_addr_source(registers["ar"])
memory_units["io"].set_port_source(registers["br"])
registers["dr"].set_source(muxes["mux3"])

def _im_size():
    sel = muxes["mux5"].signal
    return {"1": 1, "2": 2, "4": 4}.get(sel, 4)

def _dm_size():
    return 4 if control_unit.is_long() else 1

memory_units["im"].set_size_source(_im_size)
memory_units["dm"].set_size_source(_dm_size)

sums["sum1"].set_op1(registers["pc"])
sums["sum1"].set_op2(muxes["mux5"])
registers["pc"].set_source(sums["sum1"])

registers["nzvc"].set_source(alu)

control_unit = ControlUnit()

def signal_execute(signal):
    if signal.startswith("latch_"):
        reg_name = signal[6:]
        if reg_name == "nzvc":
            registers["nzvc"].value = alu.get_nzvc()
        elif reg_name in registers:
            registers[reg_name].value = registers[reg_name].get_source_value()
    elif signal.startswith("m1_"):
        muxes["mux1"].set_signal(signal[3:])
    elif signal.startswith("m2_"):
        muxes["mux2"].set_signal(signal[3:])
    elif signal.startswith("m3_"):
        muxes["mux3"].set_signal(signal[3:])
    elif signal.startswith("m4_"):
        muxes["mux4"].set_signal(signal[3:])
    elif signal.startswith("m5_"):
        muxes["mux5"].set_signal(signal[3:])
    elif signal.startswith("alu_"):
        alu.set_signal(signal)
    elif signal.startswith("sum_"):
        sums["sum1"].set_signal(signal)
    elif signal == "im_read":
        memory_units["im"].start_read()
    elif signal == "dm_read":
        memory_units["dm"].start_read()
    elif signal == "dm_write":
        memory_units["dm"].start_write(registers["dr"].get())
    elif signal == "io_read":
        memory_units["io"].start_read()
    elif signal == "io_write":
        memory_units["io"].start_write(registers["dr"].get())



INSTRUCTION_FETCH_UPC = 1


def load_conf(path="simulation.conf"):
    with open(path) as f:
        lines = [l.rstrip("\n") for l in f]
    mode = lines[0].strip().upper()
    main, start, end = [], [], []
    cur = main
    for line in lines[1:]:
        s = line.strip()
        if s == ".start:":
            cur = start; continue
        if s == ".end:":
            cur = end; continue
        cur.append(line)
    return mode, main, start, end


def reg_hex(name):
    if name in registers:
        r = registers[name]
        width = (r.size + 3) // 4
        return format(r.get(), f"0{width}x")
    if name == "ir": return format(int(control_unit.ir, 2), "04x")
    if name == "reg": return format(int(control_unit.reg, 2), "01x")
    if name == "ja1": return format(control_unit.ja1, "03x")
    if name == "ja2": return format(control_unit.ja2, "03x")
    if name == "upc": return format(control_unit.pc, "03x")
    return "?"


def data_dump(x, y):
    mem = memory_units["dm"].data
    return " ".join(format(mem.get(a, 0), "08x") for a in range(x, y))


def io_field(port, what, fmt=None):
    p = memory_units["io"].ports[port]
    if what == "rdy":
        return "1" if p.rdy else "0"
    if what == "in":
        data = p.in_buffer
    elif what == "out":
        data = p.out_buffer
    else:
        return "?"
    if fmt == "str":
        return "".join(chr(w & 0xFF) for w in data if (w & 0xFF) != 0)
    return " ".join(format(w, "08x") for w in data) if data else ""


def render(templates, signals):
    out = []
    for line in templates:
        s = line.replace("${signals}", " ".join(signals))
        s = re.sub(r"io\[(\d+):(rdy)\]",
                   lambda m: io_field(int(m.group(1)), m.group(2)), s)
        s = re.sub(r"io\[(\d+):(in|out):(str|hex)\]",
                   lambda m: io_field(int(m.group(1)), m.group(2), m.group(3)), s)
        s = s.replace("data[rdy]", "1" if memory_units["dm"].is_ready() else "0")
        s = re.sub(r"data\[(\d+):(\d+)\]",
                   lambda m: data_dump(int(m.group(1)), int(m.group(2))), s)
        s = re.sub(r"\$\{(\w+)\}", lambda m: reg_hex(m.group(1)), s)
        out.append(s)
    return "\n".join(out)


def run(im, dm, io_data, steps=200, conf_path="simulation.conf"):
    memory_units["im"].set_data(im)
    memory_units["dm"].set_data(dm)

    for port, data in io_data.items():
        memory_units["io"].ports[port].feed(data)
    
    mode, main, start, end = load_conf(conf_path)

    if start:
        rendered = render(start, [])
        if rendered != "": print(rendered)

    for i in range(steps):
        memory_units["im"].tick()
        memory_units["dm"].tick()
        memory_units["io"].tick()

        upc_before = control_unit.pc
        signals = control_unit.tick(
            registers["nzvc"].get(),
            memory_units["im"].is_ready(),
            memory_units["dm"].is_ready(),
            memory_units["io"].is_ready(),
            registers["br"].value,
        )

        alu.set_lb(control_unit.is_long())

        for signal in signals:
            signal_execute(signal)

        if mode == "TICK":
            rendered = render(main, signals)
            if rendered != "": print(rendered)
        elif mode == "INSTR" and control_unit.ir_latched:
            rendered = render(main, signals)
            if rendered != "": print(rendered)

        if not signals and control_unit.pc == upc_before:
            print(f"; HALT (uPC={control_unit.pc}) at step {i}")
            break

    if end:
        print(render(end, []))


if __name__ == "__main__":
    run()

