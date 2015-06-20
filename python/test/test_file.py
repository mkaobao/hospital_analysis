file = open('input', 'r');

# str = file.read(28)
# print len(str)
# print str

# str = file.readline()
# print line

# the same as readline
for line in file:
	print '- ' + line.strip('\n')

