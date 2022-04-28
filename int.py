import sys 
from collections import defaultdict 


global functions
global variables 
global stack 
global program 
global pc


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
			stack.append(pc)
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
				destination_var = program[stack[-1]].var_name 
				variables[destination_var] = variables[self.var_name] 
			pc = stack.pop()


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


	class Assign: 
		def __init__(self, args): 
			parts = args.split(', ') 
			self.var_name_indirect = parts[0][0] == '@'
			self.var_name = parts[0][1:] if self.var_name_indirect else parts[0] 
			self.value_indirect = parts[1][0] == '@'
			self.value = parts[1][1:] if self.value_indirect else parts[1] 
			if self.value.isnumeric(): 
				self.value = int(self.value) 


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
			self.result = parts[0]
			self.arg1_indirect = parts[1][0] == '@' 
			self.arg1 = parts[1][1:] if self.arg1_indirect else parts[1] 
			self.arg2_indirect = parts[2][0] == '@' 
			self.arg2 = parts[2][1:] if self.arg2_indirect else parts[2] 


		def __str__(self): 
			return "ADD " + self.result + ", " + ('@' if self.arg1_indirect else '') + self.arg1 + ", " + ('@' if self.arg2_indirect else '') + self.arg2


		def __repr__(self): 
			return str(self)


		def execute(self):
			arg1 = variables[self.arg1].value if self.arg1_indirect else self.arg1 
			arg2 = variables[self.arg2].value if self.arg2_indirect else self.arg2 
			variables[self.result].value = variables[arg1].value + variables[arg2].value 


	class Print: 
		def __init__(self, args): 
			self.var_name_indirect = args[0] == '@' 
			self.var_name = args[1:] if self.var_name_indirect else args 


		def __str__(self):
			return "PRINT " + ('@' if self.var_name_indirect else '') + self.var_name 


		def __repr__(self): 
			return str(self) 


		def execute(self): 
			var_name = variables[self.var_name].value if self.var_name_indirect else self.var_name 
			print(variables[var_name].value) 


	# Given a list of string objects, returns an associated list of Code objects 
	def parse(lines): 
		# global functions 

		program = [] 
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
				elif command == "IINPUT":
					program.append(Code.Input(arguments))
				elif command == "IADD": 
					program.append(Code.Add(arguments))
				elif command == "PRINT":
					program.append(Code.Print(arguments))
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
			pc = pc + 1 
