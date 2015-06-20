import time

count = 0
timestamp = time.time()
print '%s' % timestamp


while True:
	count = count + 1
	print count
	time.sleep(3)

	if(3 == count):
		break
