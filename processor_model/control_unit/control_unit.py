from processor_model.control_unit.common import *

signal_order = [
    "m3_dm", "m3_io", "m3_alu_res", "m3_pc",
    "m4_br", "m4_dr",
    "m5_1", "m5_2", "m5_4", "m5_br", "m5_dr",
    "m1_d0", "m1_d1", "m1_d2", "m1_d3",
    "m1_a0", "m1_a1", "m1_a2", "m1_a3",
    "m1_sp", "m1_fp", "m1_ar", "m1_mux4",
    "m2_d0", "m2_d1", "m2_d2", "m2_d3",
    "m2_a0", "m2_a1", "m2_a2", "m2_a3",
    "m2_sp", "m2_fp", "m2_mux4",
    "sum_shrt", "sum_load",
    "alu_cmp", "alu_add", "alu_sub", "alu_mul",
    "alu_div", "alu_not", "alu_or", "alu_and",
    "alu_xor", "alu_asl", "alu_asr", "alu_lsl",
    "alu_lsr", "alu_pass", "alu_inc_lb", "alu_dec_lb",

    "latch_op1", "latch_op2",
    "latch_br", "latch_ir", "latch_reg_br",
    "latch_alu_res", "latch_nzvc",
    "latch_ar", "latch_dr", "latch_pc",
    "latch_d0", "latch_d1", "latch_d2", "latch_d3",
    "latch_a0", "latch_a1", "latch_a2", "latch_a3",
    "latch_sp", "latch_fp",
    "latch_ja1", "latch_ja2",

    "im_read", "dm_read", "dm_write", "io_read", "io_write",
]

signal_priority = {s: i for i, s in enumerate(signal_order)}

def sort_signals(signals):
    return sorted(signals, key=lambda s: signal_priority[s])

class ControlUnit:

    def is_long(self):
        return self.get_from_ir("lb") == "1"

    def decode(self, line, size):
        num = int(line, 2)
        return bin(1 << (size - 1 - num))[2:].zfill(size)[-size:]

    def is_jmp_condition(self, jmp_type: str, template: str, im_ready: bool, dm_ready: bool, io_ready: bool):
        if jmp_type == "n":
            return self.nzvc_register_value[0] == template[-1]
        if jmp_type == "z":
            return self.nzvc_register_value[1] == template[-1]
        if jmp_type == "v":
            return self.nzvc_register_value[2] == template[-1]
        if jmp_type == "c":
            return self.nzvc_register_value[3] == template[-1]
        if jmp_type == "arg1":
            arg1_type = "0" + self.get_from_ir("arg1")
            return arg1_type == template
        if jmp_type == "arg2":
            arg2_type = "0" + self.get_from_ir("arg2")
            return arg2_type == template
        if jmp_type == "instr":
            instr = self.get_from_ir("instr")
            return instr == template
        if jmp_type == "instr_type":
            instr_type = "0" + self.get_from_ir("instr_type")
            return instr_type == template
        if jmp_type == "simple":
            return True
        if jmp_type == "not_im_rdy":
            return im_ready == False
        if jmp_type == "not_dm_rdy":
            return dm_ready == False
        if jmp_type == "not_io_rdy":
            return io_ready == False 
        if jmp_type == "dest":
            return self.get_from_ir("is_addr_dest") == "1"
        raise Exception("Unknown jmp type: " + jmp_type)

    def get_jmp_type(self, jmp_type_bin: str):
        for key, value in jmp_types.items():
            if value == jmp_type_bin:
                return key
        raise Exception("Unknown jmp type: " + jmp_type_bin)

    def tick(self, nzvc:int, im_ready:bool, dm_ready:bool, io_ready:bool, br_value:int=0):
        self.nzvc_register_value = bin(nzvc)[2:].zfill(4)
        self.ir_latched = False

        mc_instr = self.microinstructions[self.pc]
        mc_instr_type = mc_instr[0]

        signals = []

        if mc_instr_type == "1": # simple
            self.pc += 1
            signals_line = mc_instr[5:]
            instr_mode = mc_instr[1:5]
            if instr_mode == "0001": # latch registers by reg:4
                signals_line = self.decode(self.reg, 10) + signals_line[10:]
            if instr_mode == "0010": # latch mux1 by reg:4
                signals_line = signals_line[:10] + self.decode(self.reg, 12) + signals_line[22:]
            if instr_mode == "0100": # latch mux2 by reg:4
                signals_line = signals_line[:22] + self.decode(self.reg, 11) + signals_line[33:]
            if instr_mode == "1000": # latch alu by instr from opcode ([instr:5])
                signals_line = signals_line[:33] + self.decode(self.get_from_ir("instr"), 16) + signals_line[49:]

            for i in range(len(all_signals)):
                if signals_line[i] == "1":
                    signals.append(all_signals[i])

            handled = set()
            if "latch_ir" in signals:
                self.ir = bin(br_value & 0xFFFF)[2:].zfill(16)
                self.ir_latched = True
                handled.add("latch_ir")
            if "latch_reg_br" in signals:
                self.reg = bin(br_value & 0xF)[2:].zfill(4)
                handled.add("latch_reg_br")
            if "latch_ja1" in signals:
                self.ja1 = self.pc + 1
                handled.add("latch_ja1")
            if "latch_ja2" in signals:
                self.ja2 = self.pc + 1
                handled.add("latch_ja2")

            signals = [s for s in signals if s not in handled]
            return sort_signals(signals)

        else: # jump
            jmp_type = self.get_jmp_type(mc_instr[1:16])
            template = mc_instr[16:20]
            addr = mc_instr[20:29]

            if jmp_type == "ja1":
                self.pc = self.ja1
            elif jmp_type == "ja2":
                self.pc = self.ja2
            elif jmp_type == "simple":
                self.pc = int(addr, 2)
            elif self.is_jmp_condition(jmp_type, template, im_ready, dm_ready, io_ready):
                self.pc = int(addr, 2)
            else:
                self.pc += 1
            return []

    def get_from_ir(self, sec):
        if sec == "lb": return self.ir[0]
        if sec == "instr": return self.ir[1:5]
        if sec == "instr_type": return self.ir[5:8]
        if sec == "arg1": return self.ir[8:11]
        if sec == "arg2": return self.ir[11:14]
        if sec == "is_addr_dest": return self.ir[14]
        else: raise Exception("Unknown ir section: " + sec)

    def reset(self):
        self.pc = 0
        self.ja1 = 0
        self.ja2 = 0
        self.reg = "0" * 4
        self.ir = "0" * 16
        self.nzvc_register_value = "0" * 4
        self.ir_latched = False

    def __init__(self):
        self.reset()
        self.microinstructions = []
        with open(microinstructions_file, "rb") as file:
            while chunk := file.read(11):
                bits = bin(int.from_bytes(chunk, byteorder="big"))[2:]
                bits = bits.zfill(88)
                instr = bits[-84:]
                self.microinstructions.append(instr)