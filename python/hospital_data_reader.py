import database as DB
import datetime
import json

DB.setDBFile('wanfang.db')

def two_digit_number(number):
	number = int(number)
	if number < 10:
		return '0' + str(number)
	return str(number)

def transfer_minute(second):
	out_sec = second%60
	second = second/60
	out_min = second%60
	out_hr = second/60
	return '%s:%s:%s' % (two_digit_number(out_hr), two_digit_number(out_min), two_digit_number(out_sec))

def printUsage():
	print 'please enter command:'
	print 'list                                             list all doctor name and info'
	print 'doc    [name]                                    list the doctor\'s pacient data'
	print '       -date [YYYY-MM-DD]                        list on the date'
	print '       -weekday [1-7]                            list with the same weekday'
	print '       -interval [Morning|Afternoon|Night]       list with the interval'

def listAll():
	result = DB.listAll()
	for row in result:
		print '%s\t%s' % (unicode(row[0]), unicode(row[1]))


def listDoctor(params):
	result = DB.searchByParams(params)
	for row in result:
		# Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
		date 		= row[1]
		week 		= datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		week += 1
		if 2 != week:
			continue
		name 		= row[2]
		dept 		= row[3]
		room      	= row[4]
		interval 	= row[5]
		if row[6] == '{"over":true}':
			comment = "(PASS)"
		else:
			comment = '\t'
		curnumber 	= row[7]
		start 		= datetime.datetime.fromtimestamp( int(row[8]) ).strftime('%Y-%m-%d %H:%M:%S')
		duration 	= transfer_minute(row[10])
		print '%s (%d)\t%s\t%s\t%s\t%s%s\t%s\t%s' % (date, week, name, dept, interval, two_digit_number(curnumber), comment, start, duration)


usage = True

while True:
	if usage:
		printUsage()
		usage = False
	line = raw_input('Enter Command: ')
	token = line.split(' ')

	if token[0] == 'list':
		listAll()
	elif token[0] == 'doc':
		data = {}
		data['name'] = token[1]
		for i in range(2,len(token)):
			if i%2==0:
				para = token[i].split('-')

				if para == 'date' or para == 'interval' or para == 'weekday':
					data[para] = token[i+1]
				else:
					print 'error param: ' + para
			else:
				continue
		listDoctor(data)
	else:
		print 'unknow command'
		usage = True
