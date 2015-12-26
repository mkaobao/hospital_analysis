# This Python file uses the following encoding: utf-8
import database as DB
import datetime
import json
import sys
import math
import codecs

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
    print 'export_order [filePath]                          export all daoctor data with ordering'
    print 'calculate                                        calculate doctor prepare data'

def listAll():
    result = DB.listAll()
    for row in result:
        print '%s\t%s' % (unicode(row[0]), unicode(row[1]))

def sessionDataIndex(haystack,column,needle):
    for i in range(0, len(haystack)):
        if haystack[i][column] == needle:
            return i
    return -1


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


def listDoctorForOrderExport(params):
    #Exporting format:
    #number, date, time, interval, order(actual order meeting doctor), isPassed(whether the patient is late, 0 == False, 1 == True), passedCount(including missing ones), lateCount, lateOriginalOrder: 遲到者原本的Order, Duration, diffEst, Est

    output = None
    result = DB.searchByParams(params)
    curInterval = u''
    curDate = ''
    lastRegularStart = None #last start time datetime object
    lastRegularNumber = 0
    order = 1
    passedCount = 0
    curDate = ''
    curInterval = ''
    signBook = [] #record the number that did came to the doctor
    lateSignBook = {} #record the passed patients' original order
    sessionData = []
    summary = []
    peopleSeconds = 0 #record the people*seconds of passed patients, as the denominator for the frequeny of late person showing up
    totalPassedCount = 0
    durationSum = 0 #As the denominator for calculating average session time
    # TODO: 應該要把每個Interval每一個小時都填上0或1
    #以每小時紀錄略過號碼的比例
    #Format: 診次:{小時:{pass:A, total:X}}
    passProbHour = {u'上午診':{}, u'下午診':{}, u'夜間診':{}}
    #以每小時紀錄遲到者出現的比例
    #Format: 診次:{小時:{appeared:A, denominator:X}}
    recoverProbHour = {u'上午診':{}, u'下午診':{}, u'夜間診':{}}

    #Signal as EOF
    result.append(['','1970-1-1','','','','','',0,0,0,0])

    for row in result:
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = unicode(row[1])
        week        = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() + 1
        #if week != 2:
        #    continue
        name        = row[2]
        dept        = row[3]
        room        = row[4]
        interval    = row[5]
        #if row[6] != '{"over":true}':
        #    continue
        number   = int(row[7])
        time = datetime.datetime.fromtimestamp(int(row[8]))
        start       = time.strftime('%H:%M:%S')
        duration    = transfer_minute(row[10])
        durationSeconds = row[10]

        if output == None:
            line = u'%s/%s-%s.txt' % (params['filePath'].encode('utf-8').decode('utf-8'), dept.encode('utf-8').decode('utf-8'), name.encode('utf-8').decode('utf-8'))
            output = open(line, 'w')
            output.write('number\tdate\ttime\tinterval\torder\tisPassed\tpassedCount\tlateCount\tlateOriginalOrder\tduration\n')

        #Initialization for each intervals, and the outputting of data when each interval is processed
        #1. Read everything into sessionData.
        #2. Add lateCount before processing the next interval
        if curInterval != interval or curDate != date:
            if len(signBook) > 0:
                lastRegularNumber = 0
                for i in range( 0 , len(sessionData)):
                    if i == 0:
                        lastLateCount = 0
                    else:
                        lastLateCount = sessionData[i-1]['lateCount']
                    if sessionData[i]['isPassed'] == 0:
                        delta = sessionData[i]['number'] - lastRegularNumber
                        if delta > 1:
                            for steps in range(1, delta):
                                index = sessionDataIndex(sessionData, 'number', sessionData[i]['number'] - steps)
                                if index != -1 and sessionData[index]['number'] in signBook:
                                   lastLateCount += 1
                        sessionData[i]['lateCount'] = lastLateCount
                        lastRegularNumber = sessionData[i]['number']
                    else:
                        sessionData[i]['lateCount'] = lastLateCount - 1
                for p in sessionData:
                    output.write('%d\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%s\n' % (p['number'] , p['date'] , p['start'] ,p['interval'] , p['order'] , p['isPassed'] , p['passedCount'], p['lateCount'], p['lateOriginalOrder'], p['duration']))

            if len(sessionData) > 1:
                summary.append([sessionData[len(sessionData)-1]['number'],sessionData[len(sessionData)-1]['passedCount']])

            if interval == '': # EOF
                break

            #Formatting the dictionary for each Interval
            sessionData = []
            signBook = []
            lateSignBook = {}
            curInterval = interval
            curDate = date
            lastRegularNumber = 0
            order = 1
            passedCount = 0
            lastRegularStart = None

        # TODO: 把後一號（後幾號）都解釋成過號，篩掉太短duration的
        if number in signBook:########### WHAT TO DO WITH THESE GUYS WHO JUST WON'T LEAVE!!??? (Some of them with good reasons maybe)###############
            continue

        #PASSED : decrease passedCount
        #if row[6] == '{"over":true}': # <== This is problematic. Some times patients were skipped too fast that regular patient would be viewed as passed by SYSTEM
        elif number < lastRegularNumber:
            passedCount -= 1
            if time.hour in recoverProbHour[interval]:
                recoverProbHour[interval][time.hour]['appeared'] += 1
                recoverProbHour[interval][time.hour]['denominator'] += passedCount * (time - lastRegularStart).total_seconds()
            else:
                recoverProbHour[interval][time.hour] = {'appeared': 1, 'denominator': passedCount * (time - lastRegularStart).total_seconds()}
            sessionData.append({'number':number,'date':date.encode('utf-8'),'start':start.encode('utf-8'),'interval':interval.encode('utf-8'),'order':order,'isPassed':1,'passedCount':passedCount,'lateCount':0, 'lateOriginalOrder':lateSignBook[number], 'duration':duration})

        #Regular: might encounter passing
        else:
            delta = number - lastRegularNumber
            passedCount += delta - 1
            if time.hour in passProbHour[interval]:
                passProbHour[interval][time.hour]['pass'] += delta -1
                passProbHour[interval][time.hour]['total'] += delta
            else:
                passProbHour[interval][time.hour] = {'pass':delta - 1, 'total': delta}
            if time.hour in recoverProbHour[interval] and passedCount > 0 and order > 1:
                recoverProbHour[interval][time.hour]['denominator'] += passedCount * (time - lastRegularStart).total_seconds()
            elif time.hour not in recoverProbHour[interval] and passedCount > 0 and order > 1:
                recoverProbHour[interval][time.hour] = {'appeared': 0, 'denominator': passedCount * (time - lastRegularStart).total_seconds()}
            for steps in range(1, delta):
                lateSignBook[number - steps] = order

            lastRegularNumber = number
            lastRegularStart = time
            sessionData.append({'number':number,'date':date.encode('utf-8'),'start':start.encode('utf-8'),'interval':interval.encode('utf-8'),'order':order,'isPassed':0,'passedCount':passedCount,'lateCount':0, 'lateOriginalOrder':0, 'duration':duration})

        signBook.append(number)
        order += 1
        peopleSeconds += sessionData[len(sessionData)-1]['passedCount'] * durationSeconds
        totalPassedCount += sessionData[len(sessionData)-1]['isPassed']
        durationSum += durationSeconds

    if output != None:
        output.close()

    #Estimating session time for patients with order > 10
    #Target: Whenever meeting a guy with order > skip+vision, and who was not a late patient, we trace back [vision] patients and try using the information back then to estimate his session time. This way we make sure we got the actual answer for on time patients, as we expected of the end-user.
    skipping = 0
    total = 0
    for p in summary:
        #output.write('%d\t%d\n' % (p[0], p[1]))
        skipping += p[1]
        total += p[0]
    averageTime = durationSum / total

    with open(line,'r+') as fp:
        content = fp.readlines()
        fp.seek(0)
        fp.truncate()
        #Write back the header from the input stream and adding another column for difference between estimation and acutal session time
        fp.write(content[0].rstrip() + '\tdiffForEst\test\n')

        #lastOrder = 0
        #lastDate = ''
        #lastInterval = ''
        lastRegularNumber = 0
        skip = 10 #How many patients skipped before start estimating
        vision = 10 #How far we are trying to estimate
        for i in range(1, len(content)):# Starting from 1 skipping the header
        #Column format: 0:number\1:date\2:time\3:interval\4:order\5:isPassed\6:passedCount\7:lateCount\8:lateOriginalOrder\9:duration\10:answer-etimation\11:estimation
            items = content[i].rstrip().split('\t')
            if int(items[4]) < skip + vision or int(items[5]) == 1:
                fp.write(content[i].rstrip() + '\tNA\tNA\n')
                continue
            else:
                j = i-vision
                pastItems = content[j].rstrip().split('\t')
                pastInterval = pastItems[3].decode('utf-8')
                pastHour = datetime.datetime.strptime(pastItems[2], '%H:%M:%S').hour
                try:
                    averageSkip = (float(passProbHour[pastInterval][pastHour]['pass']) / passProbHour[pastInterval][pastHour]['total'])
                    #其實這是計算完全消失的比例而非跳號的可能性，時間會高估。但是也可以說假設這些短期遲到的馬上都跑回來看了
                    reappearanceFrequency = float(recoverProbHour[pastInterval][pastHour]['appeared']) / recoverProbHour[pastInterval][pastHour]['denominator']
                except KeyError:
                    print 'KeyError, time=', pastItems[2], 'date=', pastItems[1], 'Keys are:', recoverProbHour[pastInterval].keys(), 'Interval is:', pastInterval
                    sys.stdout.flush()
                lastRegularNumber = int(pastItems[0])
                isPassed = int(pastItems[5])
                while isPassed == 1:#Finding the closest regular patient near the start of vision
                    j -= 1
                    backTraceItems = content[j].rstrip().split('\t')
                    isPassed = int(backTraceItems[5])
                    lastRegularNumber = int(backTraceItems[0])
                #預期準時扣掉會遲到的人
                estimatedRegular = math.floor((int(items[0]) - lastRegularNumber) * (1.0 - averageSkip))
                #預期已經遲到但是又會再出現的人
                estimatedReappearance = math.floor(int(pastItems[6]) * averageTime * estimatedRegular * reappearanceFrequency)
                estimation = (estimatedRegular + estimatedReappearance) * averageTime
                answer = (datetime.datetime.strptime(items[2], '%H:%M:%S') - datetime.datetime.strptime(pastItems[2],'%H:%M:%S')).total_seconds()
                diff = answer - estimation
                fp.write(content[i].rstrip() + '\t%d\t%d\n' % (diff, estimation))

def export(filePath):
    doctorList = DB.getDoctorList()
    for doctor in doctorList:
        data = {}
        data['name'] = doctor
        data['filePath'] = filePath
        listDoctorForExport(data)

def export_order(filePath):
    #doctorList = DB.getDoctorList()
    #for doctor in doctorList:
    #    data = {}
    #    data['name'] = doctor
    #    data['filePath'] = filePath
    #    listDoctorForOrderExport(data)
    data = {'name':'蕭炳昆', 'filePath':filePath}
    listDoctorForOrderExport(data)

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
    line = line.decode('utf-8')
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
    elif token[0] == 'export_order':
        export_order(token[1])
    elif token[0] == 'ca':
        # for i in range(1,30):
        calculate(10);
    else:
        print 'unknow command'
        usage = True
