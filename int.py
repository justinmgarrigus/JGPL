import sys 
from collections import defaultdict 


global functions
global variables 
global stack 
global program 
global labels 
global pc
global blocks 
global progress_program_counter


class Code:
	class Variable: 
		def __init__(self, var_type = "EMPTY", value = None): 
			self.type = var_type 
			self.value = value 


		def __str__(self): 
			return f"{self.type}={str(self.value)}"


		def __repr__(self): 
			return str(self)


	class Func: 
		def __init__(self, args): 
			comma = args.find(',') 
			if comma > 0: 
				self.label = args[:comma]
				self.var_name = args[comma+2:]
			else:
				self.label = args 
				self.var_name = None 

		
		def execute(self):
			global pc 
			stack.append((pc, self.label))
			pc = functions[self.label] - 1


		def __str__(self): 
			return "FUNC " + self.label + (", " + self.var_name if self.var_name is not None else "")


		def __repr__(self):
			return str(self) 


	class Return:
		def __init__(self, args): 
			if len(args) > 0:  
				self.var_name = args 
			else:
				self.var_name = None 


		def __str__(self): 
			return "RETURN" + (" " + self.var_name if self.var_name is not None else "")


		def __repr__(self):
			return str(self) 


		def execute(self):
			global pc 
			if self.var_name is not None: 
				destination_var = program[stack[-1][0]].var_name 
				variables[destination_var] = variables[self.var_name] 
			pc = stack.pop()[0]


	class Insert: 
		def __init__(self, args): 
			parts = args.split(', ')
			self.var_name_indirect = parts[0][0] == '@' 
			self.var_name = parts[0][1:] if self.var_name_indirect else parts[0]
			self.type_indirect = parts[1][0] == '@'
			self.type = parts[1][1:] if self.type_indirect else parts[1] 


		def __str__(self): 
			return "INSERT " + ('@' if self.var_name_indirect else "") + self.var_name + ", " + ('@' if self.type_indirect else "") + self.type 


		def __repr__(self): 
			return str(self) 


		def execute(self): 
			if self.var_name_indirect: 
				var_name = variables[self.var_name].value
			else:
				var_name = self.var_name 

			if self.type_indirect: 
				var_type = variables[self.type].value
			else: 
				var_type = self.type 

			variables[var_name].type = var_type
			variables[var_name].value = None
			#print(var_name, "is", var_type) 


	class Assign: 
		def __init__(self, args): 
			parts = args.split(', ') 
			self.var_name_indirect = parts[0][0] == '@'
			self.var_name = parts[0][1:] if self.var_name_indirect else parts[0] 
			self.value_indirect = parts[1][0] == '@'
			self.value = parts[1][1:] if self.value_indirect else parts[1] 
			if self.value.isnumeric(): 
				self.value = int(self.value)
			
			self.type = parts[2] if len(parts) == 3 else None 


		def __str__(self):
			return "ASSIGN " + ('@' if self.var_name_indirect else "") + self.var_name + ", " + ('@' if self.value_indirect else "") + str(self.value)


		def __repr__(self): 
			return str(self) 


		def execute(self):
			if self.value_indirect: 
				value = variables[self.value].value
			else:
				value = self.value

			if self.var_name_indirect: 
				var_name = variables[self.var_name].value 
			else: 
				var_name = self.var_name 
			
			variables[var_name].value = value
			if self.type is not None: 
				variables[var_name].type = self.type 

			#print(var_name, "=", value)


	class Input: 
		def __init__(self, args):
			self.var_name = args 


		def __str__(self):
			return "IINPUT " + self.var_name 


		def __repr__(self): 
			return str(self) 


		def execute(self):
			variables[self.var_name].value = int(input())


	class Add: 
		def __init__(self, args):	
			parts = args.split(', ')
			self.result_indirect = parts[0][0] == '@'
			self.result = parts[0][1:] if self.result_indirect else parts[0] 
			self.arg1_indirect = parts[1][0] == '@' 
			self.arg1 = parts[1][1:] if self.arg1_indirect else parts[1] 
			self.arg2_indirect = parts[2][0] == '@' 
			self.arg2 = parts[2][1:] if self.arg2_indirect else parts[2] 


		def __str__(self): 
			return "ADD " + ('@' if self.result_indirect else '') + self.result + ", " + ('@' if self.arg1_indirect else '') + self.arg1 + ", " + ('@' if self.arg2_indirect else '') + self.arg2


		def __repr__(self): 
			return str(self)


		def execute(self):
			result = variables[self.result].value if self.result_indirect else self.result 
			arg1 = variables[self.arg1].value if self.arg1_indirect else self.arg1 
			arg2 = variables[self.arg2].value if self.arg2_indirect else self.arg2 
			if isinstance(arg1, str) and arg1.isidentifier(): arg1 = variables[arg1].value
			if isinstance(arg2, str) and arg2.isidentifier(): arg2 = variables[arg2].value
			#print(self.arg1, arg1, self.arg2, arg2, self.result, result, variables[result])
			variables[result].value = int(arg1) + int(arg2)


	class Sub: 
		def __init__(self, args):	
			parts = args.split(', ')
			self.result = parts[0]
			self.arg1_indirect = parts[1][0] == '@' 
			self.arg1 = parts[1][1:] if self.arg1_indirect else parts[1] 
			self.arg2_indirect = parts[2][0] == '@' 
			self.arg2 = parts[2][1:] if self.arg2_indirect else parts[2] 


		def __str__(self): 
			return "SUB " + self.result + ", " + ('@' if self.arg1_indirect else '') + self.arg1 + ", " + ('@' if self.arg2_indirect else '') + self.arg2


		def __repr__(self): 
			return str(self)


		def execute(self):
			arg1 = variables[self.arg1].value if self.arg1_indirect else self.arg1 
			arg2 = variables[self.arg2].value if self.arg2_indirect else self.arg2 
			#print(arg1, arg2, variables[arg1], variables[arg2]) 
			variables[self.result].value = arg1 - arg2 



	class Print: 
		def __init__(self, args): 
			self.var_name_indirect = args[0] == '@' 
			self.var_name = args[1:] if self.var_name_indirect else args 


		def __str__(self):
			return "PRINT " + ('@' if self.var_name_indirect else '') + self.var_name 


		def __repr__(self): 
			return str(self) 


		def execute(self): 
			value = variables[self.var_name].value if self.var_name_indirect else self.var_name 
			print(value)


	class ExecuteContentsZero: 
		def __init__(self, args): 
			self.var_name_indirect = args[0] == '@' 
			self.var_name = args[1:] if self.var_name_indirect else args


		def __str__(self): 
			return "EXCONZERO " + ('@' if self.var_name_indirect else "") + self.var_name 


		def __repr__(self): 
			return str(self) 


		def execute(self):
			global pc
			global progress_program_counter 

			if self.var_name_indirect: 
				var_name = variables[self.var_name].value
			else:
				var_name = self.var_name 
			
			if variables[var_name].value == 0:
				blocks.append((program[stack[-1][0]].contents_end, pc))
				#print("Branching", pc, "to new pc", program[stack[-1][0]].contents_start)
				pc = program[stack[-1][0]].contents_start + 1 
				progress_program_counter = False 
			else: 
				#print("Branching", pc, "to new pc", program[stack[-1][0]].contents_end)
				pc = program[stack[-1][0]].contents_end


	class ExecuteContents: 
		def __init__(self, args): 
			pass


		def __str__(self): 
			return "EXCON"


		def __repr__(self): 
			return str(self) 


		def execute(self):
			global pc
			global progress_program_counter 

			blocks.append((program[stack[-1][0]].contents_end, pc))
			#print("Branching", pc, "to new pc", program[stack[-1][0]].contents_start)
			pc = program[stack[-1][0]].contents_start + 1 
			progress_program_counter = False 


	class Copy: 
		def __init__(self, args):	
			parts = args.split(', ')
			self.dest_var_indirect = parts[0][0] == '@' 
			self.dest_var = parts[0][1:] if self.dest_var_indirect else parts[0] 
			self.source_var_indirect = parts[1][0] == '@' 
			self.source_var = parts[1][1:] if self.source_var_indirect else parts[1]


		def __str__(self): 
			return "COPY " + ('@' if self.dest_var_indirect else '') + self.dest_var + ", " + ('@' if self.source_var_indirect else '') + self.source_var


		def __repr__(self): 
			return str(self)


		def execute(self):
			dest_var = variables[self.dest_var].value if self.dest_var_indirect else self.dest_var 
			source_var = variables[self.source_var].value if self.source_var_indirect else self.source_var
			variables[dest_var].value = variables[source_var].value

	
	class Branch: 
		def __init__(self, args): 
			self.label = args


		def __str__(self): 
			return "BR " + self.label 


		def __repr__(self):
			return str(self)


		def execute(self): 
			global pc 
			#print("Branch from", pc, "to", labels[stack[-1][1]][self.label])
			pc = labels[stack[-1][1]][self.label]


	class BranchGreaterEqual:
		def __init__(self, args): 
			parts = args.split(', ') 
			self.arg1_indirect = parts[0][0] == '@'
			self.arg1 = parts[0][1:] if self.arg1_indirect else parts[0] 
			self.arg2_indirect = parts[1][0] == '@' 
			self.arg2 = parts[1][1:] if self.arg2_indirect else parts[1] 
			self.label = parts[2]


		def __str__(self): 
			return "BRGE " + ('@' if self.arg1_indirect else "") + self.arg1 + ", " + ('@' if self.arg2_indirect else "") + self.arg2 + ", " + self.label 

		
		def __repr__(self): 
			return str(self) 


		def execute(self): 
			global pc 
			arg1 = variables[self.arg1].value if self.arg1_indirect else self.arg1
			arg2 = variables[self.arg2].value if self.arg2_indirect else self.arg2 
			#print("BRGE :::", arg1, arg2, variables[arg1], variables[arg2])
			if variables[arg1].value >= variables[arg2].value: 
				pc = labels[stack[-1][1]][self.label] 


	# Given a list of string objects, returns an associated list of Code objects 
	def parse(lines): 
		program = [] 
		block = [] 
		label_created = False 
		label_name = "" 
		for line in lines: 
			if Code.is_label(line):
				label_created = True
				label_name = line[:-1]
			else: 
				space = line.find(' ')
				if space == -1: space = len(line)

				command = line[0:space]
				arguments = line[space+1:] 
				
				if command == "FUNC": 
					program.append(Code.Func(arguments))
				elif command == "RETURN": 
					program.append(Code.Return(arguments)) 
				elif command == "INSERT":
					program.append(Code.Insert(arguments)) 
				elif command == "ASSIGN": 
					program.append(Code.Assign(arguments))
				elif command == "COPY":
					program.append(Code.Copy(arguments))
				elif command == "BR":
					program.append(Code.Branch(arguments)) 
				elif command == "BRGE": 
					program.append(Code.BranchGreaterEqual(arguments)) 
				elif command == "IINPUT":
					program.append(Code.Input(arguments))
				elif command == "IADD": 
					program.append(Code.Add(arguments))
				elif command == "ISUB":
					program.append(Code.Sub(arguments)) 
				elif command == "PRINT":
					program.append(Code.Print(arguments))
				elif command == "EXCONZERO":
					program.append(Code.ExecuteContentsZero(arguments))
				elif command == "EXCON":
					program.append(Code.ExecuteContents(arguments)) 
				elif command == "ENTERBLOCK":
					block.append(len(program) - 1) # the index of the head of the block
				elif command == "EXITBLOCK": 
					program[block[-1]].contents_start = block[-1] 
					program[block[-1]].contents_end = len(program) - 1
					block.pop()
				elif command == "LABEL": 
					labels[label_name][arguments] = len(program) - 1
					#print("Label created:", label_name, len(program)-1)
				elif len(command) > 0: 
					print(f"ERROR: Command '{command}' not recognized")

				if label_created:
					functions[label_name] = len(program) - 1
					label_created = False
		return program 


	def is_label(line): 
		return len(line) > 1 and line[-1] == ':'


	def __init__(line):
		pass 


if __name__ == "__main__":
	if len(sys.argv) < 2 or len(sys.argv) > 3:
		print("Usage: python3 int.py <file.jgc> <display_mode>") 
	else: 
		display_mode = sys.argv[2] if len(sys.argv) == 3 else '-none'
		display_modes = ['-none', '-lines', '-code'] 
		if display_mode not in display_modes: 
			print('Unknown display_mode. Options are', display_modes) 

		f = open(sys.argv[1], 'r')
		lines = f.read().split('\n') 
		f.close()
		
		functions = {}
		variables = defaultdict(Code.Variable) 
		stack = []
		labels = defaultdict(dict) # key is the name of the function, value is the PC 
		blocks = [] 
		progress_program_counter = True 

		program = Code.parse(lines)
		if display_mode == '-code':
			counter = 0
			while counter < len(program): 
				print(counter, '\t', program[counter])
				counter += 1

		pc = functions['main'] 
		while pc < len(program):
			if display_mode == '-lines': print(program[pc]) 
			program[pc].execute() 
			if progress_program_counter: 
				if len(blocks) > 0 and blocks[-1][0] == pc: # we've just finished executing a block we were scanning for 
					pc = blocks[-1][1]
					blocks.pop()
				elif hasattr(program[pc], 'contents_end'): 
					#print("Skipping function", pc, "to new pc", program[pc].contents_end) 
					pc = program[pc].contents_end # skip the contents, the function should invoke this manually
			
			if progress_program_counter: pc = pc + 1
			else: progress_program_counter = True
