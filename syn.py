import sys 
from lex import *
from collections import defaultdict

class Command: 
	# Note: iteration needs to be done keeping track of the previously-sent node instead of the 
	# next node to send. This is because the current node to send may be updated in the logic for
	# distinguishing blocks between other commands. 
	class CommandIterator: 
		def __init__(self, command, recursive):
			self.command = command
			self.previous = None 
			self.stack = [] 
			self.recursive = recursive 
	
	
		def __next__(self): 
			if self.previous is None: 
				self.previous = self.command 
				return self.command
			else: 
				if self.recursive:
					if self.previous.contents is not None: 
						self.stack.append(self.previous) 
						self.previous = self.previous.contents
						return self.previous
					elif self.previous.next is None: 
						if len(self.stack) != 0: 
							self.previous = self.stack.pop().next 
							if self.previous is None and len(self.stack) != 0:
								self.previous = self.stack.pop().next # TODO this only supports two iterations 
							return self.previous 
						else: 
							raise StopIteration 
					else:
						self.previous = self.previous.next 
						return self.previous 
				elif self.previous.next is None:
					raise StopIteration 
				else: 
					self.previous = self.previous.next
					return self.previous


		def __iter__(self): 
			return self 


	# Groups the tokens together in terms of commands. For now, a Command is a line of code, or a block
	# containing other lines of codes/more blocks. 
	def group(tokens, display_mode = "-none"): 
		# Basically separates out each line as its own command. These commands will be separated out
		# in the future under sub-commands
		command, next_node = Command.parse(tokens) # tokens represents the head of the list 
		command_head = command
		current = command
		while next_node is not None: 
			command, next_node = Command.parse(next_node) 
			current.next = command 
			current = current.next
	
		if display_mode == "-commands": 
			for command in command_head: 
				print(command)
			
		# Now, each node is grouped into commands. If the next line after a command is indented, 
		# then this command is a block. Adjust the commands so blocks are considered.
		for command in command_head:
			if command.is_block():
				command.set_block() 
		
		if display_mode == "-blocks": 
			current = command_head
			while current is not None:
				print(current.str(True, True))
				current = current.next
		
		return command_head


	# Node: the first Lex object categorizing this command. 
	# Returns a tuple containing a Command object and the next Lex object following this one. 
	# The next object can be None, if this command is the last in the file. 
	def parse(node): 
		if node is None:
			return None, None
		
		while node.token == Token.INDENT or node.token == Token.NEWLINE: 
			node = node.next
			if node is None: 
				return None, None

		# node is now the first non-indent non-newline token 
		head = node
		while node.next is not None and node.next.token != Token.NEWLINE: 
			node = node.next

		# node is the last non-none non-newline token 
		next_node = node.next 
		node.next = None
		return Command(head), next_node 
		

	# Head: the token that defines the start of this command. 
	def __init__(self, head): 
		self.head = head
		self.next = None
		self.contents = None


	# Returns: true if we're the header for a block, false otherwise. 
	def is_block(self):
		return self.next is not None and self.head.indent < self.next.head.indent

	
	# Given the fact that this command is the header for a block, set our "contents"
	# to be the commands underneath us (at a higher indent level) 
	def set_block(self): 
		current = self.next
		indent = self.head.indent 
		while current.next is not None and indent < current.next.head.indent:
			if current.is_block(): 
				current.set_block() 
			else: 
				current = current.next

		# Current = last node inside this block
		self.contents = self.next 
		self.next = current.next
		current.next = None
	

	def str(self, raw = False, recursive = False, include_indent_number = False): 
		out = (str(self.head.indent) + ": " if include_indent_number else "")
		for node in self.head:
			if len(out) >= 2 and out[-2:] == ', ': out = out[:-3] + ", " 
			out += node.str(raw) + " "
		if recursive and self.contents is not None:
			contents_str = "" 
			for child in self.contents: 
				contents_str += "\n" + child.str(raw, recursive, include_indent_number)
			contents_str = contents_str.replace("\n", "\n--") 
			out += contents_str
		return out[:-1] 


	def __str__(self): 
		return self.str()  

	
	def __iter__(self): 
		return self.iter() 


	def iter(self, recursive=False): 
		return Command.CommandIterator(self, recursive)


	def __getitem__(self, key): 
		node = self.head 
		for i in range(key): 
			node = node.next 
		return node


class Parameter: 
	class Iterator: 
		def __init__(self, node): 
			self.node = node


		def __next__(self): 
			if self.node is None:
				raise StopIteration
			else: 
				node = self.node 
				self.node = self.node.next 
				return node


	# Creates a parameter object given the start bracket Lex object found in the function
	# declaration. 
	def __init__(self, start_bracket): 
		self.type = start_bracket.next.lexeme
		self.alias = start_bracket.next.next.lexeme
		self.next = None 

	
	def __str__(self): 
		return f"P<{self.alias}={self.type}>"

	
	def __iter__(self):
		return Parameter.Iterator(self)


class Function: 
	counter = 1

	def __init__(self): 
		self.head = None 
		self.tail = None
		self.return_type = None
		self.name = "F" + str(Function.counter)
		Function.counter += 1
		pass


	def is_function(command): 
		return command[0].lexeme == 'func' or command[0].lexeme == 'block'


	# Interprets command as a function and returns the created function object. 
	# Precondition: is_function must be True. 
	def create_function(command): 
		# This is a function, so re-contextualize the parts of the function. 
		# If there's <a b c ...>, that's a parameter, and all words outside
		# those brackets are terminals.
		func = Function() 
		current = command[1]
		previous = None 
		while current is not None: 
			if current.lexeme == "<":
				func.append(Parameter(current))
				current = current.next.next.next.next # skips <, type, alias, >
				previous = current 
			elif current.lexeme == ":":
				if current.next is not None: 
					func.return_type = current.next.lexeme
				previous.next = None 
				break
			else:
				func.append(current) 
				previous = current 
				current = current.next
		return func 	

	
	def append(self, node): 
		if self.head is None: 
			self.head = node 
			self.tail = self.head
		else: 
			self.tail.next = node 
			self.tail = self.tail.next

	
	def __str__(self): 
		if self.head is None:
			return ""

		out = (self.return_type if self.return_type is not None else "_") + ": "
		for node in self.head:
			if isinstance(node, Lex): 
				out += node.lexeme + " "
			else: 
				out += str(node) + " "
		return out[:-1]


	def __repr__(self): 
		return self.__str__()


class Reduction:
	class PassedParameter: 
		# Alias is the name of the variable inside the next function as a string. 
		# Value is either a string (another variable to copy) or a Reduction (a function to invoke)
		def __init__(self, alias, value): 
			self.value = value 
			self.alias = alias 


		def code(self):
			if isinstance(self.value, Reduction): 
				return self.value.code(is_parameter=True) + f"ASSIGN {self.alias}, result"
			else: 
				return f"ASSIGN {self.alias}, {self.value}" # self.value must already be a string 


		def __str__(self): 
			return f"({self.alias}, {str(self.value)})"


		def __repr__(self): 
			return str(self) 


	def __init__(self, production): 
		self.production = production

		# A list of a list of PassedParameters that must be completed sequentially. 
		# An index represents a list of possible PassedParameters that could occur to yield a parameter. 
		self.parameters = []
	
	
	def __str__(self):
		return "{" + str(self.production) + "|params=" + str(self.parameters) + "}"

	
	def __repr__(self): 
		return str(self)

	
	# Turns us into a code representation 
	# is_parameter: True if we are returning a value in "result", false if we are a standalone statement. 
	def code(self, is_parameter=False):
		code = "FUNC " + self.production.name + (", result" if is_parameter else "") + "\n" 
		for parameter in self.parameters: 
			if len(parameter) != 0: # TODO: need to resolve ambiguity 
				pass 
			parameter = parameter[0] # for now, just take the first choice 
			
			code = parameter.code() + "\n" + code 
		return code 


def syn(tokens, display_mode = "-none"): 
	commands = Command.group(tokens, display_mode)
	
	code = "" 
	productions = defaultdict(list) # key is the type, value is the production
	current_command = commands
	stack = [] # read the data from top to bottom, turning it into code 
	return_specified = False # Functions must have a return specified 
	while current_command is not None: 
		if Function.is_function(current_command): 
			func = Function.create_function(current_command) 
			productions[func.return_type].append(func)
			code += func.name + ":\n" 
			return_specified = False 
		elif current_command[0].lexeme == "return": 
			if current_command.next is not None: 
				print("ERROR: command following return must be None") 
			code += "RETURN " + current_command[1].lexeme + "\n"
			return_specified = True 
		elif current_command[0].lexeme == '~': # This is a terminal command, which can be translated directly.  
			code += current_command.str(raw=True)[2:] + "\n"
		else: 
			valid_reductions = reduce_statement(productions, current_command.head) 
			if len(valid_reductions) > 0: 
				code += valid_reductions[0].code() 
			else: 
				print("ERROR: no valid reductions")

		if current_command.contents is not None: 
			if not Function.is_function(current_command): 
				code += "ENTERBLOCK\n"	
			stack.append(current_command) 
			current_command = current_command.contents
		else: 
			# If we've reached the end of a command chain, we need to see if we're inside a block.
			# If we are inside a block, keep popping outwards until we see more commands next
			while current_command.next is None and len(stack) > 0: 
				current_command = stack.pop()
				if Function.is_function(current_command): 
					if not return_specified: 
						code += "RETURN\n"
				else: 
					code += "EXITBLOCK\n"
			current_command = current_command.next

	if display_mode == "-productions":
		for return_type, return_list in productions.items():
			for production in return_list: 
				print(" ", production)
	elif display_mode == "-code": 
		print(code)

	f = open("out.jgc", "w") 
	f.write(code) 
	f.close() 


def reduce_statement(global_productions, head_token): 
	valid_reductions = []
	for production in global_productions[None]: 
		result = try_reduce(head_token, production, True, global_productions)
		if result is not None: # it's valid 
			valid_reductions.append(result) 
	return valid_reductions


def try_reduce(head_token, production, statement, global_productions): 
	current_token = head_token 
	production_node = production.head 
	reduction = Reduction(production)
	while current_token is not None and current_token.lexeme != ")" and production_node is not None: 
		if isinstance(production_node, Parameter):
			if current_token.lexeme == "(": # we're reducing to something else 
				current_token = current_token.next 
				reduction.parameters.append([]) # adding a new parameter 
				if production_node.type in global_productions: # the return type is something a production yields 
					for possible_production in global_productions[production_node.type]: 
						parameter_reduction = try_reduce(current_token, possible_production, False, global_productions)
						if parameter_reduction is not None:
							reduction.parameters[-1].append(Reduction.PassedParameter(production_node.alias, parameter_reduction))
					while current_token.lexeme != ")": # TODO: does not support nested parenthesis 
						current_token = current_token.next 
					current_token = current_token.next 
					production_node = production_node.next 
				elif production_node.type == "identifier": 
					if current_token.token == Token.ID: 
						reduction.parameters[-1].append(Reduction.PassedParameter(production_node.alias, current_token.lexeme)) 
						current_token = current_token.next
						production_node = production_node.next 
					else: 
						return None
				else:
					print("Return type not recognized:", production_node.type) 
			else: # this is a parameter, but the next node alone must be the ENTIRE reduction. 
				reduction.parameters.append([]) 
				if current_token.token == Token.ID: 
					# "ID" is basically a wildcard, it can be any type at runtime. 
					reduction.parameters[-1].append(Reduction.PassedParameter(production_node.alias, current_token.lexeme))
					current_token = current_token.next 
					production_node = production_node.next 
				elif current_token.token == Token.NUMBER and production_node.type == "int": 
					# It's expecting a number and the current token is a number 
					reduction.parameters[-1].append(Reduction.PassedParameter(production_node.alias, current_token.lexeme))
					current_token = current_token.next 
					production_node = production_node.next 
				else: 
					# The current token is something the parameter won't accept.
					return None 
		else: # it's a keyword 
			if current_token.lexeme != production_node.lexeme: 
				# they don't equal, so the production isn't valid.
				return None 
			else: 
				current_token = current_token.next
				production_node = production_node.next 
	
	if current_token is not None and current_token.lexeme == ")": 
		if statement: 
			return None # throw error, unmatched parenthesis
		else: 
			return reduction
	else: 
		if current_token == None and production_node == None: 
			return reduction
		else: 
			return None 


if __name__ == "__main__": 
	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print("Usage: python syn.py lex.py <file.jg> <output mode>")
		print("Output modes: -commands, -blocks, -productions, -code")  
	else: 
		if len(sys.argv) == 4:
			display_mode = sys.argv[3] 
		else: 
			display_mode = "-code"

		display_modes = ["-commands", "-blocks", "-productions", "-code"] 
		if display_mode not in display_modes:
			print("Unrecognized display mode:", display_mode)
			print("Valid display modes:", display_modes) 
		else: 
			tokens = lex(sys.argv[2])
			syn(tokens, display_mode) 
