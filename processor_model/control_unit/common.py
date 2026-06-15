sig_modes = {
    "simple":   "0000",
    "reg":      "0001",
    "mux1":     "0010",
    "mux2":     "0100",
    "alu":      "1000"
}

jmp_types = {
    "n":                "000000000000001",
    "z":                "000000000000010",
    "v":                "000000000000100",
    "c":                "000000000001000",
    "arg1":             "000000000010000",
    "arg2":             "000000000100000",
    "instr":            "000000001000000",
    "instr_type":       "000000010000000",
    "simple":           "000000100000000",
    "ja1":              "000001000000000",
    "ja2":              "000010000000000",
    "not_im_rdy":       "000100000000000",
    "not_dm_rdy":       "001000000000000",
    "not_io_rdy":       "010000000000000",
    "dest":             "100000000000000"
}

all_signals = [
    "latch_d0", "latch_d1", "latch_d2", "latch_d3",
    "latch_a0", "latch_a1", "latch_a2", "latch_a3",
    "latch_sp", "latch_fp",

    "m1_d0", "m1_d1", "m1_d2", "m1_d3",
    "m1_a0", "m1_a1", "m1_a2", "m1_a3",
    "m1_sp", "m1_fp", "m1_ar", "m1_mux4",

    "m2_d0", "m2_d1", "m2_d2", "m2_d3",
    "m2_a0", "m2_a1", "m2_a2", "m2_a3",
    "m2_sp", "m2_fp", "m2_mux4",

    "alu_cmp", "alu_add", "alu_sub", "alu_mul",
    "alu_div", "alu_not", "alu_or", "alu_and",
    "alu_xor", "alu_asl", "alu_asr", "alu_lsl",
    "alu_lsr", "alu_pass", "alu_inc_lb", "alu_dec_lb",

    "latch_op1", "latch_op2", "latch_alu_res", "latch_nzvc",

    "latch_pc", "latch_br", "latch_ir", "latch_reg_br",
    "latch_ja1", "latch_ja2", "latch_dr", "latch_ar",

    "m3_dm", "m3_io", "m3_alu_res", "m3_pc",

    "m4_br", "m4_dr",

    "m5_1", "m5_2", "m5_4", "m5_br", "m5_dr",

    "sum_shrt", "sum_load",

    "im_read", "dm_read", "dm_write", "io_read", "io_write",
]

microinstructions_file = "./processor_model/control_unit/microcode/microcode-res.bin"

