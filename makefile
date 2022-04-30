file=NO_FILE_SPECIFIED
test:
	@python3 syn.py lex.py lib.jg $(file)
	@python3 int.py out.jgc 
