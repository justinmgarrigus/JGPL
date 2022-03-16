import sys 
from lex import *


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

	
	def __str__(self): 
		out = str(self.head.indent) + ": " 
		for node in self.head:
			out += str(node) + " "
		return out 


# Groups the tokens together in terms of commands. For now, a Command is a line of code, or a block
# containing other lines of codes/more blocks. 
def syn(tokens): 
	command, next_node = Command.parse(tokens) # tokens represents the head of the list 
	head = command
	current = command
	while next_node is not None: 
		command, next_node = Command.parse(next_node) 
		current.next = command 
		current = current.next
	
	current = head
	while current is not None:
		print(current)
		current = current.next 
	

if __name__ == "__main__": 
	if len(sys.argv) != 3:
		print("Usage: python syn.py lex.py <file.jg>")
	else: 
		tokens = lex(sys.argv[2])
		syn(tokens) 
