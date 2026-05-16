# ISA

Separated memory for instructions and data (harv)

D0-D3 - Data registers - 4 bytes
A0-A3 - Address registers - 4 bytes
SP - Stack pointer - 4 bytes
FP - Frame pointer - 4 bytes
PC - Program counter - 4 bytes
PS - Program state ????_NZVC - 1 byte


# Instruction formats

0. [2 bytes | opcode]
1. [2 bytes | opcode][1 byte | op]
2. [2 bytes | opcode][1 byte | op1][1 byte | op2]
3. [2 bytes | opcode][2 bytes | disp][1 byte | op1][1 byte | op2]
4. [2 bytes | opcode][2 bytes | disp][1 byte | op1][2 bytes | disp][1 byte | op1]
5. [2 bytes | opcode][1 byte | op1][1 byte | op1][2 bytes | disp][1 byte | op2]
6. [2 bytes | opcode][1 byte | op1][1 byte | op1][2 bytes | disp][1 byte | op1][1 byte | op1][2 bytes | disp] # ex: mov.l 2(A0, D0) 3(A0, D1)
7. [2 bytes | opcode][4 bytes | disp]


# Addressing modes

0. 1000.Dx  - Immidiate
1. Ax.Dy    - Register direct

2. (Ax)   - Address Register Indirect
3. d(Ax)  - Address Register Indirect with Displacement
4. (Ax)+  - Address Register Indirect with Postincrement
5. -(Ax)  - Address Register Indirect with Predecrement
6. d(Ax, Yx)

01
02
03
04
05
06

11
12
13
14
15
16

21
31
41
51
61

для mov+:
22 23 24 25 26
32 33 34 35 36
42 43 44 45 46
52 53 54 55 56
62 63 64 65 66

[opcode:16]: [lb:1][addr_save:1][instr:5][arg1:3][arg2:3]
    


# ISA 

All instructions that have arguments as registers have 2 modes: `.l` - long data mode (4 bytes), `.b` - byte data mode (1 byte). 
Ex: `mov.l d0 d1`; `add.b d0 d1`

## Addressing modes

0. `1000 Dx`  - Immediate
1. `Ax Dy`    - Register direct
2. `(Ax)`     - Address Register Indirect
3. `d(Ax)`    - Address Register Indirect with Displacement
4. `(Ax)+`    - Address Register Indirect with Postincrement
5. `-(Ax)`    - Address Register Indirect with Predecrement
6. `d(Ax, Yx)`- Address Register Indirect with Index

## Instructions

*Note: In each instruction only one addressing operand is allowed. The examples below use the `.l` (long) suffix for demonstration, but `.b` is also applicable where data manipulation occurs.*

### Data movement

- Move 
mov.l A B : A -> B

### Arithmetics

- Add
add.l A B : A + B -> B

- Subtract
sub.l A B : B - A -> B

- Multiply
mul.l A B : A * B -> B

- Divide
div.l A B : B / A -> B

### Bitwise

- Not (Bitwise inversion)
not.l A : ~A -> A

- Negate (Two's complement)
neg.l A : -A -> A

- Clear
clr.l A : 0 -> A

- Or (Bitwise OR)
or.l A B : A | B -> B

- And (Bitwise AND)
and.l A B : A & B -> B

- Xor (Bitwise Exclusive OR)
xor.l A B : A ^ B -> B

### Shifts

- Arithmetic Shift Left
asl.l A B : B << A -> B

- Arithmetic Shift Right
asr.l A B : B >> A (arithmetic) -> B

- Logical Shift Left
lsl.l A B : B << A (logical) -> B

- Logical Shift Right
lsr.l A B : B >> A (logical) -> B

### Control flow

*Note: Branch and jump instructions typically operate on the Program Counter (PC) and evaluate status flags (N=Negative, Z=Zero, V=Overflow, C=Carry).*

- Jump (Unconditional)
jmp A : A -> PC

- Branch on Equal (Z = 1)
beq A : if (Z == 1) A -> PC

- Branch on Not Equal (Z = 0)
bne A : if (Z == 0) A -> PC

- Branch on Minus / Negative (N = 1)
bmi A : if (N == 1) A -> PC

- Branch on Plus / Positive (N = 0)
bpl A : if (N == 0) A -> PC

- Branch on Overflow Set (V = 1)
bvs A : if (V == 1) A -> PC

- Branch on Overflow Clear (V = 0)
bvc A : if (V == 0) A -> PC

- Branch on Carry Set (C = 1)
bcs A : if (C == 1) A -> PC

- Branch on Carry Clear (C = 0)
bcc A : if (C == 0) A -> PC


## Control Unit

RA - return address

### All latches and signals list

[reg] = 4 bits
d0, d1, d2, d3,
a0, a1, a2, a3,
sp, fp,

[mux1] = 3 bits
mux1_dr, mux1_imm, mux1_d0, mux1_d1, mux1_d2, mux1_d3,

[mux2] = 4 bits
mux2_d0, mux2_d1, mux2_d2, mux2_d3,
mux2_disp,
mux2_a0, mux2_a1, mux2_a2, mux2_a3,

[mux3] = 3 bits
mux3_a0, mux3_a1, mux3_a2, mux3_a3, mux3_ar,

[alu] = 3 bits
alu_op0, alu_op1, alu_op2, alu_op3,

[agu] = 1 bit
agu_sum,

[nzvc] = 4 bits
n, z, v, c,

[pc] = 1 bit
pc,

[mux4] = 2 bit
mux4_disp, mux4_imm, mux4_dr,

[dr] = 1 bit
dr, 

[ar] = 1 bit
ar,

[instr_mem_rdy] = 1 bit
instr_mem_rdy, 

[data_mem_rdy] = 1 bit
data_mem_rdy,

[cl] = 1 bit
cl, 

[sum_cl] = 2 bit
sum_cl_1, sum_cl_2, sum_cl_4,

[wp] = 1 bit
wp, 

[sum_wp] = 1 bit
sum_wp_4,

[rp] = 1 bit
rp, 

[sum_rp] = 2 bit
sum_rp_1, sum_rp_2, sum_rp_3,

[pq_byte_0] = 3 bits 
[pq_byte_1] = 3 bits 
[pq_byte_2] = 3 bits 
[pq_byte_3] = 3 bits 
pq_0_1, pq_0_2, pq_0_3, pq_0_4,
pq_1_1, pq_1_2, pq_1_3, pq_1_4,
pq_2_1, pq_2_2, pq_2_3, pq_2_4,
pq_3_1, pq_3_2, pq_3_3, pq_3_4,
pq_4_1, pq_4_2, pq_4_3, pq_4_4,
pq_5_1, pq_5_2, pq_5_3, pq_5_4,
pq_6_1, pq_6_2, pq_6_3, pq_6_4,
pq_7_1, pq_7_2, pq_7_3, pq_7_4,

[mux5] = 3 bits
mux5_0, mux5_1, mux5_2, mux5_3, mux5_4, mux5_5, mux5_6, mux5_7,
[mux6] = 3 bits
mux6_0, mux6_1, mux6_2, mux6_3, mux6_4, mux6_5, mux6_6, mux6_7,
[mux7] = 3 bits
mux7_0, mux7_1, mux7_2, mux7_3, mux7_4, mux7_5, mux7_6, mux7_7,
[mux8] = 3 bits
mux8_0, mux8_1, mux8_2, mux8_3, mux8_4, mux8_5, mux8_6, mux8_7,

[ir] = 1 bit
ir,
[mc_pcir] = 1 bit
mc_pc,
[mc_mem_rdy] = 1 bit
mc_mem_rdy





1[reg:4][mux1:3][mux2:4][mux3:3][alu:3][agu:1][nzvc:4][pc:1][mux4:2][dr:1][ar:1][instr_mem_rdy:1][data_mem_rdy:1][cl:1][sum_cl:2][wp:1][sum_wp:1][rp:1][sum_rp:2][pq0:3][pq1:3][pq2:3][pq3:3][mux5:3][mux6:3][mux7:3][mux8:3][ir:1][mc_pc:1][mc_mem_rdy:1]

    


opcode:
[lb:1][instr:4][instr_type:3][arg1:4][arg2:4]

instr_type:
    - 001 - alu
    - 010 - control flow
    - 100 - move




1[mode:5][latches:?]
[mode]:    
    - 00000 - simple latch
    - 00001 - latch regs (input) by reg
    - 00010 - latch mux1 by reg
    - 00100 - latch mux2 by reg
    - 01000 - latch mux3 by reg
    - 10000 - latch alu by instr from opcode


0[type:8][template:4][addr:X]

[type]:
    - 00000001 - nzvc==template
    - 00000010 - arg1==template
    - 00000100 - arg2==template
    - 00001000 - instr==template
    - 00010000 - 0instr_type==template
    - 00100000 - jmp
    - 01000000 - jmp ja1
    - 10000000 - jmp ja2

# 000 - no arg1, 001 - (Ax), 010 - d(Ax), 011 - d(Ax, Yx), 100 - imm, 101 - r, 
# -(Ax) - 110, 111 - (Ax)+




# Control Unit

Обеспечивает форммированияе управляющих сигналов. Основан на работе микроопераций, которые хранятся в MICROCODE MEMORY.

Перед рассмотренем микроопераций стоит рассмотреть opcode команды:

opcode:
[lb:1][instr:4][itype:3][arg1:4][arg2:4]

lb: long or byte

itype:
    - 001 - alu
    - 010 - control flow
    - 100 - move

arg1/arg2 - типы аргкметов
000 - no arg1, 001 - (Ax), 010 - d(Ax), 011 - d(Ax, Yx), 100 - imm, 101 - r, -(Ax) - 110, 111 - (Ax)+


Каждая микрооперация состоит из X бит. Есть 2 типа микроопераций:

Simple:
format: 1[mode:5][latches:X]
[mode]:    
    - 00000 - simple latch
    - 00001 - latch registers by reg:8
    - 00010 - latch mux1 by reg:8
    - 00100 - latch mux2 by reg:8
    - 01000 - latch mux3 by reg:8
    - 10000 - latch alu by instr from opcode ([instr:4])

Branch:
0[type:8][template:4][addr:X]

[type]:
    - 00000001 - if nzvc==template
    - 00000010 - if arg1==template
    - 00000100 - if arg2==template
    - 00001000 - if instr==template
    - 00010000 - if 0instr_type==template
    - 00100000 - jmp
    - 01000000 - jmp by ja1
    - 10000000 - jmp by ja2

Схема устройства управления представлена на картинке. 
Уточнения:
    - каждый регистр имеет свой latch
    - доп бит для itype (в opcode) добавляется путем подключения gnd на дорожку старшегно бита 
    - cmp: для каждой пары бит xor, затем инверсия результата и последовательный побитовый and (сначала по 2 соседних, затем резульататы итд до получения 2 бита в качестве резудбьата)
# Control Unit

Обеспечивает формирование управляющих сигналов.  
Основан на работе микроопераций, которые хранятся в `MICROCODE MEMORY`.

Перед рассмотрением микроопераций стоит рассмотреть `opcode` команды.

---

# Opcode

`[lb:1][instr:4][itype:3][arg1:4][arg2:4]`

`lb`:

- long or byte

`itype`:

- `001` - alu
- `010` - control flow
- `100` - move

`arg1/arg2` — типы аргументов:

- `000` - no arg
- `001` - `(Ax)`
- `010` - `d(Ax)`
- `011` - `d(Ax, Yx)`
- `100` - imm
- `101` - register
- `110` - `-(Ax)`
- `111` - `(Ax)+`

---

Каждая микрооперация состоит из X бит.

Есть 2 типа микроопераций:

- `Simple`
- `Branch`

---

# Simple

Формат:

`1[mode:5][latches:X]`

`mode`:

- `00000` - simple latch
- `00001` - latch registers by `reg:8`
- `00010` - latch mux1 by `reg:8`
- `00100` - latch mux2 by `reg:8`
- `01000` - latch mux3 by `reg:8`
- `10000` - latch alu by instr from opcode (`[instr:4]`)

---

# Branch

Формат:

`0[type:8][template:4][addr:X]`

`type`:

- `00000001` - if `nzvc == template`
- `00000010` - if `arg1 == template`
- `00000100` - if `arg2 == template`
- `00001000` - if `instr == template`
- `00010000` - if `instr_type == template`
- `00100000` - `jmp`
- `01000000` - `jmp by ja1`
- `10000000` - `jmp by ja2`

---

Схема устройства управления представлена на изображении.
# Уточнения

- Каждый регистр имеет собственный `latch`.
- Дополнительный бит для `itype` в `opcode` добавляется путем подключения GND к линии старшего бита.
- `cmp` реализуется следующим образом:
  1. Для каждой пары бит выполняется `XOR`.
  2. Результат `XOR` инвертируется.
  3. Далее выполняется последовательный побитовый `AND`:
     - сначала для соседних пар,
     - затем для полученных результатов,
     - пока не будет получен итоговый 1-битный результат.