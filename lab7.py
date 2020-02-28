import pyrtl
from pyrtl import *

# basic less than function. Taken from corecircuits.py
def _basic_lt(a, b):
	assert len(a) == len(b)
	a_msb = a[-1]
	b_msb = b[-1]
	if len(a) == 1:
			return (b_msb & ~a_msb)
	small = _basic_lt(a[:-1], b[:-1])
	return (b_msb & ~a_msb) | (small & ~(a_msb ^ b_msb))


	# ALU(data0, data1, shamt, funct)
	# Inuts:
	#		data0, data1: 16 bit WireVectors containing input values
	#		shamt: Optional WireVector shift amount for bit shift operations
	#		funct: WireVector containing specified function for ALU to peform
	#	Output: WireVector containing 16 bit computed value
	#	Note: right now we are not worrying about carry out/overflow bits

def ALU(data0, data1, shamt, funct):
	#alu_o = WireVector(bitwidth = 16, name = 'alu_o')
	with conditional_assignment:
		with funct == 0x20:
			return signed_add(data0, data1)
		with funct == 0x24:
			return data0 & data1
		with funct == 0x25:
			return data0 | data1
		with funct == 0x00:
			return shift_left_logical(data1, shamt)
		with funct == 0x03:
			return shift_right_arithmetic(data1, shamt)
		with funct == 0x02:
			return shift_right_logical(data1, shamt)
		with funct == 0x2a:
			return signed_lt(data0, data1)
		with funct == 0x22:
			data1 = ~data1 + 1 # twos complement on data1
			return signed_add(data0, data1) # add data0 + (-data1)
		with funct == 0x26:
			return data0 ^ data1

rf = MemBlock(bitwidth=16, addrwidth=5, name='rf')
# assume the instructions are already given. Just decode them
# instruction is fed through a 32 bit input wire named instr
# for testing, implement your own PC and romblock or something idk
# for now, assume you have the 32 bit instruction and your task is to 
# decode and run the instruction on the appropriate hardware 

def top(instr):
	# Initialize the registers?
	#w_data = WireVector(bitwidth = 16, name = 'w_data')

	# Define some additional wires
	# data0/1 are write ports for the memory block, data0 <=> rs, data1 <=> rt
	data0 = WireVector(bitwidth = 16, name = 'data0')
	data1 = WireVector(bitwidth = 16, name = 'data1')


	# write enable bit, set to 1 as default (write is enabled)
	# we pass this bit whenever we want to write to the memory block
	#we_bit = WireVector(1, 'we_bit')
	# the write enable tuple
	# when we want to pass an input to write into the memory blocl
	# we pass in this tuple with the data and the write enable bit
	#WE = rf.EnabledWrite


	# decode the instruction:
	op = WireVector(bitwidth = 6, name = 'op')
	rs = WireVector(bitwidth = 5, name = 'rs')
	rt = WireVector(bitwidth = 5, name = 'rt')
	rd = WireVector(bitwidth = 5, name = 'rd')
	shamt = WireVector(bitwidth = 5, name = 'shamt')
	funct = WireVector(bitwidth=6, name = 'funct')
	# We are only decoding R-type instructions for now
	#imm = WireVector(bitwidth=16, name='imm')
	#addr = WireVector(bitwidth=26, name='addr')

	op <<= instr[26:32] 
	rs <<= instr[21:26]
	rt <<= instr[16:21]
	rd <<= instr[11:16]
	shamt <<= instr[6:11] # shamt -> ALU
	funct <<= instr[0:6] # funct -> ALU
	#imm <<= instr[0:16]
	#addr <<= instr[0:26]


	# alright now we're gonna hook all the stuff up together
	# and pray that it works 

	w_data = WireVector(bitwidth = 16, name = 'w_data')

	data0 <<= rf[rs]
	data1 <<= rf[rt]

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
	
	rf[rd] <<= w_data

	return w_data

instr = Input(bitwidth = 32, name = "instr")
alu_out = WireVector(bitwidth = 16, name = 'alu_out')
alu_out <<= top(instr)
