from processor_model.basic_elements import *
from processor_model.control_unit.control_unit import ControlUnit

registers = {name: Register() for name in
             ("d0", "d1", "d2", "d3", "a0", "a1", "a2", "a3", "sp", "fp",
              "dr", "ar", "br", "pc", "op1", "op2", "alu_res")}
registers["nzvc"] = Register(4)

muxes = {f"mux{i}": Mux() for i in range(1, 6)}
alu = ALU(registers["nzvc"])
sums = {"sum1": Sum()}
memory_units = {
    "im": MemoryUnit(),
    "dm": MemoryUnit(),
    "io": IODevice(n=3, delay=5),
}

for r in ("d0", "d1", "d2", "d3", "a0", "a1", "a2", "a3", "sp", "fp"):
    registers[r].set_source(registers["alu_res"])

_mux12_opts = {r: registers[r] for r in
               ("d0", "d1", "d2", "d3", "a0", "a1", "a2", "a3", "sp", "fp", "ar")}
_mux12_opts["mux4"] = muxes["mux4"]
muxes["mux1"].set_options(dict(_mux12_opts))
muxes["mux2"].set_options(dict(_mux12_opts))
muxes["mux3"].set_options({
    "pc": registers["pc"],
    "alu_res": registers["alu_res"],
    "dm": memory_units["dm"],
    "io": memory_units["io"],
})
muxes["mux4"].set_options({"br": registers["br"], "dr": registers["dr"]})
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
    return {"1": 1, "2": 2, "4": 4}.get(muxes["mux5"].signal, 4)


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
        name = signal[6:]
        if name == "nzvc":
            registers["nzvc"].value = alu.get_nzvc()
        elif name in ["d0", "d1", "d2", "d3", "a0", "a1", "a2", "a3", "sp", "fp"]:
            registers[name].fill(control_unit.is_long())
        else:
            registers[name].value = registers[name].get_source_value()
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


LOG_REGS = ["d0", "d1", "d2", "d3", "a0", "a1", "a2", "a3",
            "sp", "fp", "br", "ar", "dr", "pc", "nzvc"]
INSTRUCTION_FETCH_UPC = 1


def _reg_str():
    parts = []
    for name in LOG_REGS:
        r = registers[name]
        w = (r.size + 3) // 4
        parts.append(f"{name}={r.get():0{w}x}")
    return " ".join(parts)


def _io_in_str():
    lines = []
    for i, p in enumerate(memory_units["io"].ports):
        if p.in_buffer:
            hexs = " ".join(f"{w:08x}" for w in p.in_buffer)
            s = "".join(chr(w & 0xFF) for w in p.in_buffer if (w & 0xFF))
            lines.append(f"  io[{i}] in : hex=[{hexs}] str=\"{s}\"")
    return lines


def _io_out_str():
    lines = []
    for i, p in enumerate(memory_units["io"].ports):
        if p.out_buffer:
            hexs = " ".join(f"{w:08x}" for w in p.out_buffer)
            s = "".join(chr(w & 0xFF) for w in p.out_buffer if (w & 0xFF))
            lines.append(f"  io[{i}] out: hex=[{hexs}] str=\"{s}\"")
    return lines

def run(im, dm, io_data, steps=200000, log_path="journal.log", disasm=None):
    for r in registers.values():
        r.value = 0
    for mu in memory_units.values():
        if hasattr(mu, "ports"):
            for p in mu.ports:
                p.in_buffer = []
                p.out_buffer = []
                p.in_word = 0
                p.rdy = False
                p.counter = -1
        else:
            mu.data = {}
            mu.ready = False
            mu.inner_counter = -1
            mu.pending_write = None
            mu.read_size = 4
    for m in muxes.values():
        m.signal = ""
    control_unit.reset()

    memory_units["im"].set_data(im)
    memory_units["dm"].set_data(dm)
    for port, data in io_data.items():
        words = [ord(x) if isinstance(x, str) and x.isalpha() else x for x in data]
        memory_units["io"].ports[port].feed(words)

    disasm = disasm or {}
    log = open(log_path, "w")

    log.write("=== IO INPUT ===\n")
    for line in _io_in_str():
        log.write(line + "\n")
    log.write("=== TRACE (tick: signals | registers | mnemonic) ===\n")

    pc_at_fetch = 0
    for i in range(steps):
        memory_units["im"].tick()
        memory_units["dm"].tick()
        memory_units["io"].tick()

        upc_before = control_unit.pc
        if upc_before == INSTRUCTION_FETCH_UPC:
            pc_at_fetch = registers["pc"].get()

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

        mnem = ""
        if control_unit.ir_latched:
            mnem = "  ; " + disasm.get(pc_at_fetch, "?")
        log.write(f"{i:6} {' '.join(signals):40} | {_reg_str()}{mnem}\n")

        if not signals and control_unit.pc == upc_before:
            log.write(f"; HALT (uPC={control_unit.pc}) at tick {i}\n")
            break

    log.write("=== IO OUTPUT ===\n")
    out_lines = _io_out_str()
    for line in out_lines:
        log.write(line + "\n")
    log.close()

    print("=== IO OUTPUT ===")
    for line in out_lines:
        print(line)