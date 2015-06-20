

try:							# check point
	raise IOError, 'haha'
	print 'haha'
except:							# error
	print 'IO Error happened' 
else:							# success
	print 'else'
finally:						# always
	print 'final'




