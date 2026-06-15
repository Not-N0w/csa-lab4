# ISA

Разделеннаыя память для инструкций и данных (harv)

D0-D3 - Data registers - 4 bytes
A0-A3 - Address registers - 4 bytes
SP - Stack pointer - 4 bytes
FP - Frame pointer - 4 bytes
PC - Program counter - 4 bytes
PS - Program state NZVC - 4 bits


# Instruction formats
0. [opcode : 16]
1. [opcode : 16][op : 4][emp : 4]
2. [opcode : 16][op : 4][emp : 4][disp : 16]
3. [opcode : 16][op : 4][emp : 4][op : 4][emp : 4][disp : 16]
4. [opcode : 16][op : 4][emp : 4][op : 4][emp : 4]
5. [opcode : 16][imm : 32][op : 4][emp : 4]
6. [opcode : 16][op : 4][emp : 4][disp : 16][op : 4][emp : 4]
7. [opcode : 16][op : 4][emp : 4][disp : 16][imm : 32]
8. [opcode : 16][op : 4][emp : 4][op : 4][emp : 4][disp : 16][op : 4][emp : 4]
9. [opcode : 16][op : 4][emp : 4][op : 4][emp : 4][disp : 16][imm : 32]
10. [opcode : 16][disp : 16]
11. [opcode : 16][abs_addr : 32]

12. [opcode : 16][op : 4][emp : 4][port : 8]
13. [opcode : 16][imm : 32][port : 8]
14. [opcode : 16][op : 4][emp : 4][disp : 16][port : 8]
15. [opcode : 16][op : 4][emp : 4][op : 4][emp : 4][disp : 16][port : 8]


## Addressing modes
0. `1000, Dx`  - Immediate
1. `Ax, Dy`    - Register direct
2. `(Ax)`     - Address Register Indirect
3. `d(Ax)`    - Address Register Indirect with Displacement
4. `(Ax)+`    - Address Register Indirect with Postincrement
5. `-(Ax)`    - Address Register Indirect with Predecrement
6. `d(Ax, Yx)`- Address Register Indirect with Index

# ISA 

All instructions that have arguments as registers have 2 modes: `.l` - long data mode (4 bytes), `.b` - byte data mode (1 byte). 
Ex: `mov.l d0 d1`; `add.b d0 d1`


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

- Compare (set nzvc for A - B)
cmp.l A B

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
jmp abs_addr : abs_addr -> PC

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


- Call procedure (FP -> -(SP) SP -> FP ; PC -> -(SP) ; abs_addr -> PC)
call abs_addr

- Return from procedure ( (FP-4) -> PC ; FP+4 -> SP ; (FP) -> FP)
ret

# Sys

- Halt
hlt

# IO

- Read from IO
in A #port

- Write to IO
out A #port

