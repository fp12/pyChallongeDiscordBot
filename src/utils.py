def print_array(title, header, iterable, func):
	vertSep = '|'
	arraySep = '='
	headerSep = '-'
	lineLen = len(header)
	arrayLineSeparators = ''.ljust(lineLen, arraySep)
	headerLineSeparators = '|'.ljust(lineLen-1, headerSep) + '|'

	print(arrayLineSeparators)
	print('| ' + title.ljust(lineLen-3) + '|')
	print(headerLineSeparators)
	print(header)
	print(headerLineSeparators)
	for x in iterable:
	    print(func(x))
	print(arrayLineSeparators)