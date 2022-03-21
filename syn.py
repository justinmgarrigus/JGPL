import sys 
from lex import *


# Note: iteration needs to be done keeping track of the previously-sent node instead of the 
# next node to send. This is because the current node to send may be updated in the logic for
# distinguishing blocks between other commands. 
class CommandIterator: 
	def __init__(self, command):
		self.command = command
		self.previous = None 


	def __next__(self): 
		if self.previous is None: 
			self.previous = self.command 
			return self.command
		else: 
			if self.previous.next is None:
				raise StopIteration 
			else: 
				self.previous = self.previous.next
				return self.previous 


class Command: 
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
		# then this command is a block. Adjust the commands so blocks are considered. .
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
	

	def str(self, recursive = False, include_indent_number = False): 
		out = (str(self.head.indent) + ": " if include_indent_number else "")
		for node in self.head:
			out += str(node) + " "
		if recursive and self.contents is not None:
			contents_str = "" 
			for child in self.contents: 
				contents_str += "\n" + child.str(recursive, include_indent_number)
			contents_str = contents_str.replace("\n", "\n--") 
			out += contents_str
		return out 


	def __str__(self): 
		return self.str()  

	
	def __iter__(self): 
		return CommandIterator(self)


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
		return f"<{self.type}>"

	
	def __iter__(self):
		return Parameter.Iterator(self)


class Function: 
	def __init__(self): 
		self.head = None 
		self.tail = None
		self.return_type = None 
		pass

	
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
		return out


def syn(tokens, display_mode = "-none"): 
	commands = Command.group(tokens, display_mode)
	productions = [] 
	for command in commands: 
		if command[0].lexeme == "func": 
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
			productions.append(func) 
	if display_mode == "-productions":
		for production in productions:
			print(" ", production) 


if __name__ == "__main__": 
	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print("Usage: python syn.py lex.py <file.jg> <output mode>")
		print("Output modes: -commands, -blocks, -productions")  
	else: 
		if len(sys.argv) == 4:
			display_mode = sys.argv[3] 
		else: 
			display_mode = "-blocks"

		if display_mode not in ["-commands", "-blocks", "-productions"]:
			print("Unrecognized display mode:", display_mode)
		else: 
			tokens = lex(sys.argv[2])
			syn(tokens, display_mode) 
