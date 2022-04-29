import sys 
import enum 


class Token(enum.Enum): 
	ID = "id"
	NUMBER = "number"
	TERMINAL = "terminal"
	INDENT = "indent"
	NEWLINE = "newline"
	PARAMETER = "parameter"
	STRING = "string"

	def __str__(self): 
		return str(self.value) 


class NodeIterator: 
	def __init__(self, node): 
		self.node = node

	def __next__(self): 
		if self.node is None:
			raise StopIteration
		else: 
			node = self.node 
			self.node = self.node.next 
			return node


class Lex: 
	def __init__(self, token = None, lexeme = None, indent = 0):
		self.token = token
		self.lexeme = lexeme
		self.indent = indent
		self.next = None


	def str(self, raw=False): 
		if self.token == Token.INDENT:
			lex_str = str(self.indent) 
		elif self.token == Token.NEWLINE: 
			lex_str = "\\n" 
		else: 
			lex_str = self.lexeme 
		
		if raw: 
			return lex_str
		else: 
			return f"<{self.token}, {lex_str}>"

	def __str__(self):
		return self.str() 


	def __iter__(self): 
		return NodeIterator(self) 


# Returns a linked list of Token nodes representing the lexical analysis step of compilation
def lex(filenames):
	if isinstance(filenames, str):
		filenames = [filenames] 

	head = Lex()
	current = head
	for filename in filenames: 
		with open(filename) as f: 
			ch = f.read(1)
			lexeme = ""
			isLetter = False 
			isNumber = False 
			isIndent = False 
			isString = False 
			indent = 0 
			while ch != "":
				if isString: 
					if ch == '"':
						isString = False 
						current.token = Token.STRING
						current.indent = indent 
						current.lexeme = lexeme 
						current.next = Lex() 
						current = current.next
						lexeme = ""
					else: 
						lexeme += ch 
				elif ch.isalpha() or ch == "_":
					if len(lexeme) > 0 and (isNumber or isIndent):
						# We were previously reading numbers/indents
						if isNumber:
							current.token = Token.NUMBER 
							isNumber = False 
						elif isIndent:
							current.token = Token.INDENT
							indent = len(lexeme) 
							isIndent = False 
						current.lexeme = lexeme 
						current.indent = indent
						current.next = Lex() 
						current = current.next
						isLetter = True 
						lexeme = "" 
					# This is our first letter for this lexeme, or we were previously also reading letters 
					lexeme += ch
					isLetter = True
				elif ch.isdigit():
					if len(lexeme) == 0: 
						isNumber = True
					elif isIndent: 
						current.token = Token.INDENT
						indent = len(indent) 
						current.indent = indent 
						current.lexeme = lexeme 
						current.next = Lex() 
						current = current.next 
						isIndent = False 
						isNumber = True 
						lexeme = ""
					lexeme += ch
				elif ch == "\t":
					if isLetter or isNumber:
						raise SyntaxError
					lexeme += ch
					isIndent = True 
				elif ch == "\n" or ch == "\r":
					if len(lexeme) > 0: 
						if isNumber: 
							current.token = Token.NUMBER
							isNumber = False 
						elif isIndent: 
							current.token = Token.INDENT
							indent = len(lexeme)
							isIndent = False 
						elif isLetter: 
							current.token = Token.ID
							isLetter = False 
						current.lexeme = lexeme 
						current.indent = indent 
						current.next = Lex()
						current = current.next
					current.token = Token.NEWLINE
					current.lexeme = "\n"
					indent = 0 
					current.indent = indent 
					current.next = Lex() 
					current = current.next 
					lexeme = ""
				elif ch == '"': 
					isString = True 
				elif not ch.isspace(): 
					# ch is a symbol 
					if len(lexeme) > 0: 
						if isNumber: 
							current.token = Token.NUMBER 
							isNumber = False
						elif isIndent: 
							current.token = Token.INDENT
							indent = len(lexeme) 
							isIndent = False
						else: 
							current.token = Token.ID
							isLetter = False 
						current.lexeme = lexeme 
						current.indent = indent 
						current.next = Lex() 
						current = current.next 
					# Symbols can only be a single character long
					current.token = Token.TERMINAL
					current.lexeme = ch 
					current.indent = indent 
					current.next = Lex() 
					current = current.next
					lexeme = ""
				else: 
					# ch is whitespace 
					if len(lexeme) > 0: 
						if isNumber: 
							current.token = Token.NUMBER
							isNumber = False
						elif isLetter: 
							current.token = Token.ID
							isLetter = False
						elif isIndent: 
							current.token = Token.INDENT 
							indent = len(lexeme) 
							isIndent = False 
						current.lexeme = lexeme 
						current.indent = indent 
						current.next = Lex() 
						current = current.next 
						lexeme = "" 
				ch = f.read(1)
		if isNumber: 
			current.token = Token.NUMBER
		elif isLetter: 
			current.token = Token.ID 
		elif isIndent: 
			current.token = Token.INDENT
			indent = len(indent) 
		current.lexeme = lexeme 
		current.indent = indent 

		current.next = Lex(token=Token.NEWLINE, lexeme='\n', indent=indent)
		current = current.next
		current.next = Lex()
		current = current.next
			
		#if filename == filenames[-1]: current.next = None 
		#else: current.next = Lex()
	
	# if last node's token is None, remove it
	current = head 
	while current is not None and current.next is not None: 
		if current.next.token is None: 
			current.next = current.next.next 
		current = current.next 

	return head


# Given the -oneline flag, display the tokens on a single line.  
def lex_display_oneline(tokens): 
	for node in tokens: 
		print(node, end = " ") 


# Given the -format flag, display the tokens in a neatly formatted list. 
def lex_display_formatted(tokens): 
	for node in tokens:
		if node.token == Token.INDENT: 
			print("\t" * node.indent, end = "")
		elif node.token == Token.NEWLINE: 
			print("\n", end = "")
		else: 
			print(node, end = " ")


# Given the -indent flag, display the token and indent amount of each Lex object. 
def lex_display_indent(tokens): 
	for node in tokens:
		if node.token == Token.INDENT: 
			print("\t" * node.indent, end = "")
			print(f"<{node.token}, {node.indent}>", end = " ") 
		elif node.token == Token.NEWLINE: 
			print("\n", end = "")
		else: 
			print(f"<{node.token}, {node.indent}>", end = " ")


if __name__ == "__main__": 
	if len(sys.argv) < 2:
		print("Usage: python lex.py <file.jg> <file2.jg> <...> <output mode>")
		print("Output modes: -oneline, -format, -indent") 
	else:
		print(sys.argv) 
		if sys.argv[-1][0] != '-': 
			sys.argv.append('-')
		tokens = lex(sys.argv[1:-1]) 
		if sys.argv[-1] == "-oneline":
			lex_display_oneline(tokens)
		elif sys.argv[-1] == "-indent":
			lex_display_indent(tokens) 
		else: 
			lex_display_formatted(tokens)
		print("\n")
