import pyrtl
from pyrtl import *


#This function is sus lmao - ok, I know that this doesn't work now
# def ALU(data0, data1, alu_op):
# 	with conditional_assignment:
# 		with alu_op == 0:
# 			return signed_add(data0, data1)
# 		with alu_op == 1:
# 			return data0 & data1
# 		with alu_op == 2:
# 			return data0 | data1
# 		with alu_op == 4:
# 			data1 = ~data1 + 1
# 			return signed_add(data0, data1)

PC = Register(bitwidth=32, name='PC')
rf = MemBlock(bitwidth=32, addrwidth=5, name='rf', asynchronous=True)
d_mem = MemBlock(bitwidth=32, addrwidth=32, name='d_mem', asynchronous=True)
i_mem = MemBlock(bitwidth=32, addrwidth=32, name='i_mem')
instr = WireVector(bitwidth=32, name='instr')
# assume the instructions are already given. Just decode them
# instruction is fed through a 32 bit input wire named instr
# for testing, implement your own PC and romblock or something idk
# for now, assume you have the 32 bit instruction and your task is to 
# decode and run the instruction on the appropriate hardware 

	# Initialize the registers?
	#w_data = WireVector(bitwidth = 16, name = 'w_data')
# Define some additional wires
# data0/1 are write ports for the memory block, data0 <=> rs, data1 <=> rt
data0 = WireVector(bitwidth = 32, name = 'data0')
data1 = WireVector(bitwidth = 32, name = 'data1')
data2 = WireVector(bitwidth = 32, name = 'data2')

instr <<= i_mem[PC]

# decode the instruction:
op = WireVector(bitwidth = 6, name = 'op')
rs = WireVector(bitwidth = 5, name = 'rs')
rt = WireVector(bitwidth = 5, name = 'rt')
rd = WireVector(bitwidth = 5, name = 'rd')
funct = WireVector(bitwidth=6, name = 'funct')
imm = WireVector(bitwidth=16, name='imm')
sign_extended_imm = WireVector(bitwidth=32, name='sign_extended_imm')
branch_addr = WireVector(bitwidth=32, name='branch_addr')

zero = WireVector(bitwidth=1, name='zero')
we = Input(1, 'we')

reg_dst = WireVector(bitwidth=1, name='reg_dst')
branch = WireVector(bitwidth=1, name='branch')
reg_write = WireVector(bitwidth=1, name='reg_write')
mem_write = WireVector(bitwidth=1, name='mem_write')
mem_to_reg = WireVector(bitwidth=1, name='mem_to_reg')
alu_src = WireVector(bitwidth=1, name='alu_src')

op <<= instr[26:32] 
rs <<= instr[21:26]
rt <<= instr[16:21]
rd <<= instr[11:16]
funct <<= instr[0:6] # funct -> ALU
imm <<= instr[0:16]
sign_extended_imm <<= imm.sign_extended(32)

# pass op and func to control unit
alu_op = pyrtl.WireVector(bitwidth=3, name='alu_op')
control_signals = pyrtl.WireVector(bitwidth=9, name='control_signals')
with pyrtl.conditional_assignment:
   with op == 0:
      with funct == 0x20: # add 
         control_signals |= 0x140
      with funct == 0x24: # and
         control_signals |= 0x141
      with funct == 0x2a: # slt
         control_signals |= 0x144
   with op == 0x8: # addi
      control_signals |= 0x60
   with op == 0xf: # load upper immediate
      control_signals |= 0x62
   with op == 0xd: # ori 
      control_signals |= 0x62
   with op == 0x23: # this one's probably load word
      control_signals |= 0x68
   with op == 0x2b: # uhhhh sw
      control_signals |= 0x30
   with op == 0x4: # beq
      control_signals |= 0x84

reg_dst <<= control_signals[-1]
branch <<= control_signals[-2]
reg_write <<= control_signals[-3]
alu_src <<= control_signals[-4]
mem_write <<= control_signals[-5]
mem_to_reg <<= control_signals[-6]
alu_op <<= control_signals[0:3]
   
alu_result = WireVector(bitwidth = 32, name = 'alu_result')

data0 <<= rf[rs]

#Mux for ALU Source
with pyrtl.conditional_assignment:
   with alu_src == 0:
      data1 |= rf[rt]
   with alu_src == 1:
      data1 |= sign_extended_imm

#Mux for ALU OP
with conditional_assignment:
   with alu_op == 0:
      alu_result |= signed_add(data0, data1)
      zero |= 0
   with alu_op == 1:
      alu_result |= data0 & data1
      zero |= 0
   with alu_op == 2:
      alu_result |= data0 | data1
      zero |= 0
   with alu_op == 4:
      alu_result |= signed_add(~data0 + 1, data1)
      probe(~data0 + 1, 'Subtracting FROM')
      probe(data1, 'Subtracting this')
      with alu_result == 0:
         zero |= 1

#Branching Instr
branch_addr <<= shift_left_logical(sign_extended_imm, Const(2))
with pyrtl.conditional_assignment: 
   with (branch & zero) == 1:
      PC.next |= signed_add(PC+1, branch_addr)
   with (branch & zero) == 0:
      PC.next |= PC+1

#Mux for Register Destination and Register Write
write_reg_temp = WireVector(5)
bits_temp = WireVector(32)

#Memory Instruction

with pyrtl.conditional_assignment:
   with reg_write == 1:
      with reg_dst == 0:
         write_reg_temp |= rt
      with reg_dst == 1:
         write_reg_temp |= rd

with pyrtl.conditional_assignment:
   with mem_to_reg == 1: #lw
      bits_temp |= d_mem[alu_result] 
   with mem_to_reg == 0:
      bits_temp |= alu_result

with pyrtl.conditional_assignment:
   with mem_write == 1:  #sw
      WE = MemBlock.EnabledWrite

d_mem[alu_result] <<= WE(rf[rt], we)

probe(write_reg_temp, 'Im writing to')
rf[write_reg_temp] <<= probe(bits_temp, 'Im writing')

we <<= we & 0

"""
	with conditional_assignment:
		with funct == 0x24:
			w_data |=  data0 & data1
		with funct == 0x20:
			w_data |= signed_add(data0, data1)
		with funct == 0x25:
			w_data |=  data0 | data1
		with funct == 0x00:
			w_data |=  shift_left_logical(data1, shamt)
		with funct == 0x03:
			w_data |=  shift_right_arithmetic(data1, shamt)
		with funct == 0x02:
			w_data |=  shift_right_logical(data1, shamt)
		with funct == 0x2a:
			w_data |=  signed_lt(data0, data1)
		with funct == 0x26:
			w_data |= data0 ^ data1
		with funct == 0x22:
			data1 = ~data1 + 1 # twos complement on data1
			w_data |= signed_add(data0, data1) # add data0 + (-data1)
	"""

if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. One assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory). Remember, each instruction
       is 4 bytes, so you must increment your addresses by 4!

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that the program has "finished" its business logic.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 4

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })
    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
       sim.step({})
       if (cycle == 29):
          sim_trace.render_trace()
          print(sim.inspect_mem(rf))
          print(sim.inspect_mem(d_mem))
    # Use render_trace() to debug if your code doesn't work.
    # sim_trace.render_trace()

    # You can also print out the register file or memory like so if you want to debug:
    # print(sim.inspect_mem(d_mem))
    # print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
   #  assert (sim.inspect_mem(rf)[16] == 65536)
   #  assert (sim.inspect_mem(rf)[17] == 1)
   #  assert (sim.inspect_mem(rf)[18] == 0)
   #  assert (sim.inspect_mem(rf)[19] == 5)
   #  assert (sim.inspect_mem(rf)[20] == 1)
   #  assert (sim.inspect_mem(rf)[21] == 65535)
    assert(sim.inspect_mem(d_mem)[0] == 10)
    assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    print('Passed!')
