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


	def __str__(self): 
		out = str(self.head.indent) + ": " 
		for node in self.head:
			out += str(node) + " "
		if self.contents is not None:
			contents_str = "" 
			for child in self.contents: 
				contents_str += "\n" + str(child)
			contents_str = contents_str.replace("\n", "\n--") 
			out += contents_str
		return out 

	
	def __iter__(self): 
		return CommandIterator(self)


# Groups the tokens together in terms of commands. For now, a Command is a line of code, or a block
# containing other lines of codes/more blocks. 
def syn(tokens, display_mode = "-none"): 
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
		return
		
	# Now, each node is grouped into commands. If the next line after a command is indented, 
	# then this command is a block. Adjust the commands so blocks are considered. .
	for command in command_head:
		if command.is_block():
			command.set_block() 
	
	if display_mode == "-blocks": 
		current = command_head
		while current is not None:
			print(current)
			current = current.next
	
	return command_head
	

if __name__ == "__main__": 
	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print("Usage: python syn.py lex.py <file.jg> <output mode>")
		print("Output modes: -commands, -blocks")  
	else: 
		if len(sys.argv) == 4:
			display_mode = sys.argv[3] 
		else: 
			display_mode = "-blocks"

		if display_mode not in ["-commands", "-blocks"]:
			print("Unrecognized display mode:", display_mode)
		else: 
			tokens = lex(sys.argv[2])
			syn(tokens, display_mode) 
