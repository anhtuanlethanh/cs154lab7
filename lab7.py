import pyrtl
from pyrtl import *

#This function is sus lmao
def ALU(data0, data1, alu_op):
	with conditional_assignment:
		with alu_op == 0:
			return signed_add(data0, data1)
		with alu_op == 1:
			return data0 & data1
		with alu_op == 2:
			return data0 | data1
		with alu_op == 4:
			data1 = ~data1 + 1
			return signed_add(data0, data1)

rf = MemBlock(bitwidth=16, addrwidth=5, name='rf')
# assume the instructions are already given. Just decode them
# instruction is fed through a 32 bit input wire named instr
# for testing, implement your own PC and romblock or something idk
# for now, assume you have the 32 bit instruction and your task is to 
# decode and run the instruction on the appropriate hardware 

def top(instr):
	# Initialize the registers?
	#w_data = WireVector(bitwidth = 16, name = 'w_data')
	PC = pyrtl.wire.Register(bitwidth=32, name='PC')
	# Define some additional wires
	# data0/1 are write ports for the memory block, data0 <=> rs, data1 <=> rt
	data0 = WireVector(bitwidth = 16, name = 'data0')
	data1 = WireVector(bitwidth = 16, name = 'data1')

	# decode the instruction:
	op = WireVector(bitwidth = 6, name = 'op')
	rs = WireVector(bitwidth = 5, name = 'rs')
	rt = WireVector(bitwidth = 5, name = 'rt')
	rd = WireVector(bitwidth = 5, name = 'rd')
	shamt = WireVector(bitwidth = 5, name = 'shamt')
	funct = WireVector(bitwidth=6, name = 'funct')
	imm = WireVector(bitwidth=16, name='imm')
	branch_addr = WireVector(bitwidth=32, name='branch_addr')

	zero = WireVector(bitwidth=1, name='zero')
	reg_dst = WireVector(bitwidth=1, name='reg_dst')
	branch = WireVector(bitwidth=1, name='branch')
	reg_write = WireVector(bitwidth=1, name='reg_write')
	alu_src = WireVector(bitwidth=1, name='alu_src')
	mem_write = WireVector(bitwidth=1, name='mem_write')
	mem_to_reg = WireVector(bitwidth=1, name='mem_to_reg')

	op <<= instr[26:32] 
	rs <<= instr[21:26]
	rt <<= instr[16:21]
	rd <<= instr[11:16]
	shamt <<= instr[6:11] # shamt -> ALU
	funct <<= instr[0:6] # funct -> ALU
	imm <<= instruc[0:15]
	imm.sign_extended(32)
	#imm <<= shift_right_arithmetic(instr[0:16], 16) # sign extend immediate

	# pass op and func to control unit
	alu_op = pyrtl.WireVector(bitwidth=3, name='alu_op')
	control_signals = pyrtl.WireVector(bitwidth=9, name='control_signals')
	with pyrtl.conditional_assignment:
		with op == 0:
			with funct == 0x20: # add 
				control_signals |= 0x140
				#alu_op |= 0 
			with funct == 0x24: # and
				control_signals |= 0x141
				#alu_op |= 1
			with funct == 0x2a: # slt
				control_signals |= 0x144
				#alu_op |= 4
		with op == 0x8: # addi
			control_signals |= 0x160
			#alu_op |= 0
		with op == 0xf: # load upper immediate
			control_signals |= 0x162
			#alu_op |= 2
		with op == 0xd: # ori 
			control_signals |= 0x163
			#alu_op |= 2
		with op == 0x23: # this one's probably load word
			control_signals |= 0x168
			#alu_op |= 0
		with op == 0x2b: # uhhhh sw
			control_signals |= 0x30
			#alu_op |= 0
		with op == 0x4: # beq
			control_signals |= 0x80
			#alu_op |= 4

	reg_dst <<= control_signals[-1]
	branch <<= control_signals[-2]
	reg_write <<= control_signals[-3]
	alu_src <<= control_signals[-4]
	mem_write <<= control_signals[-5]
	alu_op <<= control_signals[0:3]
		
	w_data = WireVector(bitwidth = 16, name = 'w_data')

	data0 <<= rf[rs]

	#Mux for ALU Source
	with pyrtl.conditional_assignment:
		with alu_src == 0:
			data1 |= rf[rt]
		with alu_src == 1:
			data1 |= imm
	
	#Mux for ALU OP
	with conditional_assignment:
		with alu_op == 0:
			w_data |= signed_add(data0, data1)
			zero = 0
		with alu_op == 1:
			w_data |= data0 & data1
			zero = 0
		with alu_op == 2:
			w_data |= data0 | data1
			zero = 0
		with alu_op == 4:
			w_data |= signed_add(data0, ~data1 + 1)
			with w_data == 0:
				zero = 1
	#Mux for Register Destination and Register WRite
	with pyrtl.conditional_assignment:
		with reg_write == 1:
			with reg_dst == 0:
				rf[rt] |= w_data
			with alu_src == 1:
				rf[rd] |= w_data

	#Branching Instr
	branch_addr <<= shift_left_logical(imm, 2)
	PC.next <<= signed_add(PC, 0x0004)

	with pyrtl.conditional_assignment: 
		with (branch & zero) == 1:
			PC.next <<= signed_add(PC.next[28:32], branch_addr)
			
	return w_data
	
instr = Input(bitwidth = 32, name = "instr")
alu_out = WireVector(bitwidth = 16, name = 'alu_out')
alu_out <<= top(instr)
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
