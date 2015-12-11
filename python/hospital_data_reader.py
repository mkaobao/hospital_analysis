# This Python file uses the following encoding: utf-8
import database as DB
import datetime
import json
import sys
import math

DB.setDBFile('wanfang.db')
#DB.setDBFile('vghtpe.db')

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
    print '       -interval [M|A|N]                         list with the interval'
    print 'export [filePath]                                export all daoctor data'
    print 'calculate                                        calculate doctor prepare data'

def listAll():
    result = DB.listAll()
    for row in result:
        print '%s\t%s' % (unicode(row[0]), unicode(row[1]))


def listDoctor(params):
    result = DB.searchByParams(params)
    for row in result:
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = row[1]
        week        = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() + 1
        if 'weekday' in params:
            if int(params['weekday']) != week:
                continue
        name        = row[2]
        dept        = row[3]
        room        = row[4]
        interval    = row[5]
        if row[6] == '{"over":true}':
            comment = "(PASS)"
        else:
            comment = '\t'
        curnumber   = row[7]
        start       = datetime.datetime.fromtimestamp( int(row[8]) ).strftime('%Y-%m-%d %H:%M:%S')
        duration    = transfer_minute(row[10])

        line = '%s (%d)\t%s\t%s\t%s\t%s%s\t%s\t%s' % (date, week, unicode(name), unicode(dept), unicode(interval), two_digit_number(curnumber), comment, start, duration)
        print line

def listDoctorForExport(params):
    output = None
    result = DB.searchByParams(params)
    curInterval = ''
    curDate = ''
    lastNumber = ''
    segment = {}
    printTitle = True

    for row in result:
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = row[1]
        week        = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() + 1
        name        = row[2]
        dept        = row[3]
        room        = row[4]
        interval    = row[5]
        if row[6] != '{"over":true}':
            continue
        curnumber   = row[7]
        start       = datetime.datetime.fromtimestamp( int(row[8]) ).strftime('%H:%M:%S')
        duration    = transfer_minute(row[10])

        if output == None:
            line = '%s/%s-%s.txt' % (params['filePath'], dept, name)
            output = open(line, 'w')

        if printTitle == True:
            curInterval = interval
            curDate = date
            line = '%s (%d)\t%s\t%s\t%s' % (date, week, unicode(name), unicode(dept), unicode(interval))
            output.write(line.encode('utf-8') + '\n')
            printTitle = False

        if curInterval == interval and curDate == date:
            # segment[int(curnumber)] = start
            # lastNumber = curnumber
            # print '%s %s' % (curnumber, start)
            if row[6] == '{"over":true}':
                output.write('%d (over)\t%s\n' % (curnumber, start))
            else:
                output.write('%d\t%s\n' % (curnumber, start))
        else:
            printTitle = True
        # else:
        #     for i in range(1, int(lastNumber)):
        #         if i not in segment:
        #             segment[i] = ''
        #         output.write('%d\t%s\n' % (i, segment[i]))
        #     output.write('\n')
        #     segment = {}

    # for i in range(1, int(lastNumber)):
    #     if i not in segment:
    #         segment[i] = ''
    #     output.write('%d\t%s\n' % (i, segment[i]))
    if output != None:
        output.close()

def export(filePath):
    doctorList = DB.getDoctorList()
    for doctor in doctorList:
        data = {}
        data['name'] = doctor
        data['filePath'] = filePath
        listDoctorForExport(data)

def calculate(config):
    data = {}
    data['name'] = '林永國'
    result = DB.searchByParams(data)
    today = ''
    totalGap = 0
    lastNumber = 0
    count = 0
    gap = 0

    totalDelta = 0
    deltaCount = 0

    for row in result:
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = row[1]
        week        = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() + 1
        name        = row[2]
        dept        = row[3]
        room        = row[4]
        interval    = row[5]
        curnumber   = row[7]
        start       = datetime.datetime.fromtimestamp( int(row[8]) ).strftime('%H:%M:%S')
        duration    = row[10]

        if week != 4:
            continue

        if row[6] == '{"over":true}':
            continue

        if '' == today:
            today = date
        elif date != today:
            today = date
            # print 'totalGap: %d, count: %d, average gap: %.3f\n' % (totalGap, count, math.ceil((float)(totalGap)/count))
            totalGap = 0
            lastNumber = 0
            count = 0
            gap = 0

        if duration < 50:
            continue

        if lastNumber == 0:
            lastNumber = curnumber
            continue
        else:
            gap = curnumber - lastNumber
            totalGap += gap
            count += 1
            lastNumber = curnumber

        if curnumber == config:
            totalDelta += (float)(duration/gap)
            deltaCount += 1
            print '%s(%s)\t%s\t%d\t%d,\t\tgap:\t%s,\tdelta:\t%.3f' % (date, week, name, curnumber, duration, gap, (float)(duration)/gap)
    # if totalDelta != 0:
    #     print '%d\tavg delta: %.3f' % (config, (float)(totalDelta/deltaCount))
    # print 'totalGap: %d, count: %d, average gap: %.3f' % (totalGap, count, math.ceil((float)(totalGap)/count))

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
                para = token[i].split('-')[1]
                if para == 'date' or para == 'interval' or para == 'weekday':
                    data[para] = token[i+1]
                else:
                    print 'error param: ' + para
            else:
                continue
        listDoctor(data)
    elif token[0] == 'export':
        export(token[1])
    elif token[0] == 'ca':
        # for i in range(1,30):
        calculate(10);
    else:
        print 'unknow command'
        usage = True
