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


class ProgramStack: 
	def __init__(self): 
		self.stack = [] # List of (int, str) tuples representing (PC, function name) 
		self.function = None


	# PC: the program counter we left off at. 
	# Label: the name of the function we are going to. 
	def push(self, pc, label): 
		self.stack.append((pc, label))

	
	# Returns the PC of where we left off. 
	def pop(self):
		return self.stack.pop()[0]


	# Returns the name of the function we are currently in. 
	def current_function(self): 
		return self.stack[-1][1]

	
	# Returns the PC of the statement we left off on (that initiated the branch). 
	def last_pc(self): 
		return self.stack[-1][0] 


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
	

		def __str__(self): 
			return "FUNC " + self.label + (", " + self.var_name if self.var_name is not None else "")


		def __repr__(self):
			return str(self) 


		def execute(self):
			global pc 
			stack.push(pc, self.label)
			pc = functions[self.label] - 1



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
				destination_var = program[stack.last_pc()].var_name 
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
			#print(var_name, "is", var_type) 


	class Assign: 
		def __init__(self, args): 
			parts = args.split(', ') 
			self.var_name = parts[0] 
			self.value = ', '.join(parts[1:])
			if self.value.isnumeric(): 
				self.value = int(self.value)
			
			self.type = parts[2] if len(parts) == 3 else None 


		def __str__(self):
			return f"ASSIGN {self.var_name}, {self.value}"


		def __repr__(self): 
			return str(self) 


		def execute(self):
			var_name = Code.var_at(self.var_name) 
			value = Code.var_at(self.value) 
			
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
			self.result = parts[0]
			self.arg1 = parts[1] 
			self.arg2 = parts[2] 


		def __str__(self): 
			return f"ADD {self.result}, {self.arg1}, {self.arg2}"


		def __repr__(self): 
			return str(self)


		def execute(self):
			arg1 = Code.int_value_of(self.arg1) 
			arg2 = Code.int_value_of(self.arg2)  
			result = Code.var_at(self.result) 
			variables[result].value = arg1 + arg2 


	class Sub: 
		def __init__(self, args):	
			parts = args.split(', ')
			self.result = parts[0]
			self.arg1 = parts[1] 
			self.arg2 = parts[2] 


		def __str__(self): 
			return f"SUB {self.result}, {self.arg1}, {self.arg2}"


		def __repr__(self): 
			return str(self)


		def execute(self):
			arg1 = Code.int_value_of(self.arg1) 
			arg2 = Code.int_value_of(self.arg2)  
			result = Code.var_at(self.result) 
			variables[result].value = arg1 - arg2 



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
			if isinstance(value, str) and '\\n' in value: 
				value = value.replace('\\n', '\n')
			print(value, end="")


	class ExecuteContentsCondition: 
		def __init__(self, args, cond): 
			self.var_name = args
			self.cond = cond 


		def __str__(self): 
			return f"EXCON{self.cond} {self.var_name}"


		def __repr__(self): 
			return str(self) 


		def execute(self):
			global pc
			global progress_program_counter 
			
			print("ERROR: DEPRECIATED CODE!!! ExecuteContentsCondition")


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
			
			#blocks.append((program[stack[-1][0]].contents_end, pc))
			top_statement = program[stack.last_pc()] # FUNC call
			
			# This statement must be a block, so block_start will be defined
			old_pc = pc 
			pc = top_statement.contents_start + 1

			bottom_statement = program[top_statement.contents_end] # last statement in block
			bottom_statement.block_end_branch_to = old_pc # when done with block, branch here 
			bottom_statement.block_end_func_name = stack.current_function() 
			bottom_statement.block_end_add_stack = stack.pop() # when done with block, add this back to the stack 

			#pc = program[stack[-1][0]].contents_start
			progress_program_counter = False 

			#print("Changing PC from", old_pc, "to", pc) 


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
			pc = labels[stack.current_function()][self.label]


	class BranchConditional:
		def __init__(self, args, cond): 
			parts = args.split(', ') 
			self.arg1 = parts[0] 
			self.arg2 = parts[1] 
			self.label = parts[2]
			self.cond = cond 


		def __str__(self): 
			return f"BR{self.cond.upper()} {self.arg1}, {self.arg2}, {self.label}" 

		
		def __repr__(self): 
			return str(self) 


		def execute(self): 
			global pc 
			arg1 = Code.int_value_of(self.arg1) 
			arg2 = Code.int_value_of(self.arg2) 
			#print(self.arg1, self.arg2, arg1, arg2, self.cond, Code.condition(arg1, arg2, self.cond)) 
			if Code.condition(arg1, arg2, self.cond): 
				#print("Branch taken:", pc, labels[stack[-1][1]][self.label])
				pc = labels[stack.current_function()][self.label] 


	class Compare: 
		def __init__(self, args, sign): 
			parts = args.split(', ') 
			self.result = parts[0] 
			self.arg1 = parts[1] 
			self.arg2 = parts[2]
			self.sign = sign 


		def __str__(self): 
			return f"{self.sign.upper()} {self.result}, {self.arg1}, {self.arg2}"


		def __repr__(self): 
			return str(self) 


		def execute(self):
			result = Code.var_at(self.result) 
			arg1 = Code.int_value_of(self.arg1) 
			arg2 = Code.int_value_of(self.arg2) 
			boolean = Code.condition(arg1, arg2, self.sign) 
			variables[result].value = 1 if boolean else 0
			variables[result].type = "bool"
			#print("Compare:", self.arg1, self.arg2, arg1, arg2, self.result, result, boolean, self.sign) 


	class Object: 
		counter = 0 

		def __init__(self, args): 
			self.result = args


		def __str__(self): 
			return f"OBJECT {self.result}" 


		def __repr__(self): 
			return str(self) 


		def execute(self): 
			result = Code.var_at(self.result) 
			name = variables[result].type + '_' + str(Code.Object.counter) 
			variables[name].value = {}
			variables[result].value = name
			Code.Object.counter += 1
			#print("Object:", name, result, variables[name])


	class Attribute: 
		def __init__(self, args):
			parts = args.split(', ')
			self.obj = parts[0] 
			self.var_name = parts[1] 
			self.value = parts[2] 


		def __str__(self): 
			return f"ATTRIBUTE {self.obj}, {self.var_name}, {self.value}" 


		def __repr__(self):
			return str(self) 


		def execute(self): 
			obj = variables[Code.var_at(self.obj)].value 
			var_name = Code.var_at(self.var_name) 
			value = Code.var_at(self.value)
			#print("Attribute test:", obj, var_name, value) 
			variables[obj].value[var_name] = value 	
			#print(obj, variables[obj].value)


	class Retrieve: 
		def __init__(self, args): 
			parts = args.split(', ') 
			self.result = parts[0] 
			self.obj = parts[1] 
			self.var_name = parts[2] 


		def __str__(self): 
			return f"RETRIEVE {self.result}, {self.obj}, {self.var_name}" 


		def __repr__(self):
			return str(self) 


		def execute(self): 
			result = Code.var_at(self.result) 
			obj = variables[Code.var_at(self.obj)].value
			var_name = Code.var_at(self.var_name) 
			#print("Retrieve:", result, obj, var_name, variables[obj].value)
			#print("All variables:", variables)
			variables[result].value = variables[obj].value[var_name]
			#print(obj, variables[obj].value) 


	# Returns the argument interpreted as an int. Leading @s represent indirection. 
	def int_value_of(arg): 
		#print("int_value_of(",arg,")")
		if isinstance(arg, int): 
			return arg 
		
		arg = Code.var_at(arg) 
		#print("var_at(",arg,")")

		if isinstance(arg, str) and not arg.isnumeric():
			arg = variables[arg].value 
		#print("int(",arg,")")
		return int(arg) 


	# Returns the variable pointed to by the argument. If the argument has no indirection, returns itself. 
	def var_at(arg):
		if isinstance(arg, str): 
			while arg[0] == '@':
				next_arg = variables[arg.replace('@', '')].value
				if not isinstance(next_arg, str): 
					arg = next_arg
					break 
				arg = '@' * (arg.count('@') - 1) + next_arg
		return arg


	def condition(arg1, arg2, sign):
		#print("Condition:", arg1, type(arg1), arg2, type(arg2), sign, arg1 == arg2)
		if sign == 'gt':   return arg1 > arg2
		elif sign == 'lt': return arg1 < arg2 
		elif sign == 'eq': return arg1 == arg2 
		elif sign == 'ge': return arg1 >= arg2 
		elif sign == 'le': return arg1 <= arg2 
		elif sign == 'ne': return arg1 != arg2 
		else: print("UNKNOWN OPERATION:", sign) 
	

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
				elif command.startswith("BR"): 
					program.append(Code.BranchConditional(arguments, command[2:].lower())) 
				elif command == "IINPUT":
					program.append(Code.Input(arguments))
				elif command == "IADD": 
					program.append(Code.Add(arguments))
				elif command == "ISUB":
					program.append(Code.Sub(arguments)) 
				elif command == "PRINT":
					program.append(Code.Print(arguments))
				elif command == "EXCON":
					program.append(Code.ExecuteContents(arguments))
				elif command[:5] == "EXCON":
					program.append(Code.ExecuteContentsCondition(arguments, command[5:].lower())) 
				elif command == 'OBJECT': 
					program.append(Code.Object(arguments))
				elif command == 'RETRIEVE':
					program.append(Code.Retrieve(arguments)) 
				elif command == 'ATTRIBUTE': 
					program.append(Code.Attribute(arguments)) 
				elif command in ['GT', 'LT', 'EQ', 'GE', 'LE', 'NE']:
					program.append(Code.Compare(arguments, command.lower()))
				elif command == "ENTERBLOCK":
					block.append(len(program) - 1) # the index of the head of the block
				elif command == "EXITBLOCK": 
					program[block[-1]].contents_start = block[-1] 
					program[block[-1]].contents_end = len(program) - 1
					block.pop()
				elif command == "LABEL": 
					labels[label_name][arguments] = len(program) - 1
					#print(labels)
					#print("Label created:", label_name, len(program)-1)
				elif len(command) > 0: 
					print(f"ERROR: Command '{command}' not recognized")

				if label_created and command != 'LABEL':
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
		stack = ProgramStack() 
		labels = defaultdict(dict) # key is the name of the function, value is the PC 
		blocks = [] 
		progress_program_counter = True 

		program = Code.parse(lines)
		#print(functions)
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
				if hasattr(program[pc], "block_end_branch_to"):
					# This command marks the end of a branch. 
					command = program[pc] 
					pc = command.block_end_branch_to 
					stack.push(command.block_end_add_stack, command.block_end_func_name) 					

					delattr(command, "block_end_branch_to") 
					delattr(command, "block_end_add_stack")
					delattr(command, "block_end_func_name")

					#print("   Reached the end of a branch. Going to", pc, "with stack", stack.stack) 
				elif hasattr(program[pc], "contents_start"): 
					# This is the start of a block. We shouldn't run this here, this should be invoked somewhere else. 
					pc = program[pc].contents_end 
					#print("   Skipped the start of a branch") 

				pc += 1 
			else: 
				progress_program_counter = True 
