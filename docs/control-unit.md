# Control Unit

Обеспечивает форммированияе управляющих сигналов. Основан на работе микроопераций, которые хранятся в MICROCODE MEMORY.
Подразумивается, что результатом работы CU является лишь набор управляющих сигналов. Далее результат работы CU - большое двоичное число, каждый бит которого - какой-то сигнал (описано ниже).  

Перед рассмотренем микроопераций стоит рассмотреть opcode команды:

opcode:
[lb:1][instr:4][instr_type:3][arg1_type:3][arg2_type:3][is_addr_dest:1][reserved:1]

lb: 
  - 1 - long 
  - 0 - byte

instr_type:
  - 000 - system (hlt + nop)
  - 001 - alu
  - 010 - control
  - 011 - io

arg1_type/arg2_type - типы аргуметов
  - 000 - no arg1, 
  - 001 - (Ax), 
  - 010 - d(Ax), 
  - 011 - d(Ax, Yx), 
  - 100 - imm, 
  - 101 - r, 
  - 110 - -(Ax), 
  - 111 - (Ax)+

is_addr_dest: 
  - 1 - arg1 == destenation
  - 0 - arg2 == destenation

instr:  
  instr_type == system (000)
    0000 - hlt
    
  instr_type == alu (001)
    0000 - cmp
    0001 - add
    0010 - sub
    0011 - mul
    0100 - div
    0101 - not (op1)
    0110 - or
    0111 - and
    1000 - xor
    1001 - asl
    1010 - asr
    1011 - lsl
    1100 - lsr 
    1101 - pass (op1)
    1110 - inc (op1)
    1111 - dec (op1)


  instr_type == control (010)
    0000 - jmp
    
    0001 - beq
    0010 - bne
    0011 - bmi
    0100 - bpl
    0101 - bvs
    0110 - bcs
    0111 - bcc
    
    1000 - call
    1001 - ret

  instr_type == io (011)
    0000 - in
    0001 - out
    



Результат работы [CU]:
[latch_reg:10][mux1:12][mux2:11]
[alu_op:16]
[latch_op1][latch_op2][latch_alu_res][latch_nzvc]
[latch_pc][latch_br][latch_ir][latch_reg_br][latch_ja1][latch_ja2][latch_dr][latch_ar]
[mux3:4][mux4:2][mux5:5]
[sum:2]
[im_read][dm_read][dm_write][io_read][io_write] 

: 79 бит

Каждая микрооперация состоит из X бит. Есть 2 типа микроопераций:

Simple:
format: 1[mode:4][signals:79] : 84
[mode]:    
    - 0000 - simple signals
    - 0001 - latch registers by reg:4
    - 0010 - latch mux1 by reg:4
    - 0100 - latch mux2 by reg:4
    - 1000 - latch alu by instr from opcode ([instr:5])

Branch:
0[type:15][template:4][addr:9][oth:55] : 84

[type]:
    - 000000000000001 - if 000n==template
    - 000000000000010 - if 000z==template
    - 000000000000100 - if 000v==template
    - 000000000001000 - if 000c==template
    - 000000000010000 - if 0arg1_type==template
    - 000000000100000 - if 0arg2_type==template
    - 000000001000000 - if instr==template
    - 000000010000000 - if 0instr_type==template
    - 000000100000000 - jmp
    - 000001000000000 - jmp by ja1
    - 000010000000000 - jmp by ja2
    - 000100000000000 - if not_im_rdy
    - 001000000000000 - if not_dm_rdy
    - 010000000000000 - if not_io_rdy
    - 100000000000000 - if is_addr_dest

# Микрокод (БОЛЬ)

Писать микрокод оказалось тяжко, даже с учетом упрощений isa и cu. Было принято решение зафиксировать синтаксис описания микроинструкций и затем странслировать его в бинарник, который после будет исполняться.

Собственно синтаксис повторяет форматы микрокоманд: 
sig [t.<type>] <signal> [<signal>]
jmp [t.<type>] [<template>] [<addr>]

Ну и конечно есть лейблы, вместо которых при трансляции подсталяется адрес (номер) микроинструкции.

См. processor_model/control_unit/microcode_generator.py и processor_model/control_unit/microcode/microcode.txt