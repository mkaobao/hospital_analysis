#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import database as DB
import datetime
import sys
import math
import json
import numpy

class NumberRange:
    _average = None
    _STD = None
    _count = None

    def __init__(self, average, std, count):
        self._average = average
        self._STD = std
        self._count = count
    def getHigh(self, week):
        return self._average[week] + (2 * self._STD[week])
    def getLow(self, week):
        ret = self._average[week] - (2 * self._STD[week])
        if ret < 0:
            return 0
        else:
            return ret
    def getAverage(self, week):
        return self._average[week]
    def getSTD(self, week):
        return self._STD[week]
    def getCount(self, week):
        return self._count[week]
    def getAverages(self):
        return self._average
    def getSTDs(self):
        return self._STD
    def includes(self, week, value):
        if self.getHigh(week) == 0:
            return True
        if value == self.getHigh(week) or value == self.getLow(week) or (value < self.getHigh(week) and value > self.getLow(week)):
            return True
        else:
            return False
    def isAveragesEqual(self, values):
        for i in range(1,8):
            if values[i] != self._average[i]:
                return False
        return True
    def isSTDsEqual(self, values):
        for i in range(1,8):
            if values[i] != self._STD[i]:
                return False
        return True

def two_digit_number(number):
    number = int(number)
    if number < 10:
        return '0'+str(number)
    else:
        return str(number)

def transfer_minute(second):
    out_sec = second%60
    second = second/60
    out_min = second%60
    out_hr = second%60
    return '%s:%s:%s' % (two_digit_number(out_hr), two_digit_number(out_min), two_digit_number(out_sec))

def getDoctorWeekAverageStd(docName, numberRange):
    result = DB.searchByParams({'name':docName})

    weekDurations = {1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[]}
    weekSum = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}
    weekCount = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}

    lastInterval = ''
    lastday = ''
    lastweek = 0
    timeList = []

    for row in result:
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = row[1]
        week        = datetime.datetime.strptime(row[1], '%Y-%m-%d').weekday() + 1
        interval    = row[5]

        if row[6] == '{"over":true}':
            continue

        duration = row[10]
        if duration < 50:
            continue

        if numberRange.getHigh(week) != 0 and duration > numberRange.getHigh(week):
            continue
        if numberRange.getLow(week) > duration:
            continue

        if lastday != date or lastInterval != interval:
            # print '==========%s(%s)===========' % (lastday, lastweek)
            timeList = sorted(timeList)
            length = len(timeList)
            percent = int(length * 0.15)

            for i in range(0,percent):
                timeList.pop()
                timeList.pop(0)

            for i in timeList:
                weekDurations[lastweek].append(i)
                weekSum[lastweek] += i
                weekCount[lastweek] += 1

            lastday = date
            lastweek = week
            lastInterval = interval
            timeList = []

        timeList.append(duration)

    #     weekDurations[week].append(duration)
    #     weekSum[week] += duration
    #     weekCount[week] += 1

    # for i in range(1,8):
    #     tempList = sorted(weekDurations[i])
    #     length = len(tempList)
    #     percent = length / 10

    #     for j in range(0,percent):
    #         tempList.pop()
    #         tempList.pop(0)

    #     weekDurations[i] = tempList
    #     weekCount[i] = len(tempList)
    #     weekSum[i] = 0
    #     for j in tempList:
    #         weekSum[i] += j

    weekAverage = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}
    weekSTD = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}
    for week in range(1,8):
        if weekCount[week] == 0:
            continue
        weekAverage[week] = weekSum[week]/weekCount[week]
        weekSTD[week] = numpy.std(weekDurations[week])
        # print 'week %d: average: %d, STD: %d' % (week, weekAverage[week], weekSTD[week])
    return NumberRange(weekAverage, weekSTD, weekCount)

def getDoctorStableAverageSTD(docName):
    DoctorData = NumberRange({1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}, {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}, {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0})

    lastAverage = DoctorData.getAverages()
    lastSTD = DoctorData.getSTDs()

    while True:
        DoctorData = getDoctorWeekAverageStd(docName, DoctorData)
        # print "======================"
        # for i in range(1,8):
        #     print "week: %d, average: %d, std: %d, count: %d" % (i, DoctorData.getAverage(i), DoctorData.getSTD(i), DoctorData.getCount(i))
        if DoctorData.isAveragesEqual(lastAverage) and DoctorData.isSTDsEqual(lastSTD):
            break
        lastAverage = DoctorData.getAverages()
        lastSTD = DoctorData.getSTDs()
    return DoctorData

def generateData(doctorName):
    result = DB.searchByParams({'name':doctorName})

    today = None
    lastNumber = None
    lastStartTime = None
    lastInterval = None
    lastweek = None

    recordNumber = None
    increaseTimeList = None
    weeksData = {1:{}, 2:{}, 3:{}, 4:{}, 5:{}, 6:{}, 7:{}}

    breakFlag = False

    debugFile = open('debug.txt', 'a')

    for row in result:
        # use struct data instead of
        # Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration
        date        = row[1]
        week        = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() + 1
        interval    = row[5]
        curNumber   = row[7]
        start       = int(row[8])
        duration    = row[10]

        line = '%s %s %s(%d) %s %s %s' % (doctorName, interval, date, week, curNumber, datetime.datetime.fromtimestamp( start ).strftime('%H:%M:%S'), duration)
        debugFile.write(line.encode('utf-8') + '\n')

        # remove data
        if row[6] == '{"over":true}':
            continue
        if duration < 50:
            continue

        if today != date or lastInterval != interval:
            if lastweek != None:
                if today not in weeksData[lastweek]:
                     weeksData[lastweek][today] = {}
                if lastInterval.encode('utf-8') == '上午診':
                    name_interval = 'morning'
                elif lastInterval.encode('utf-8') == '下午診':
                    name_interval = 'afternoon'
                else:
                    name_interval = 'night'                    
                weeksData[lastweek][today][name_interval] = increaseTimeList
            today = date
            lastInterval = interval
            lastNumber = curNumber
            lastStartTime = start
            lastweek = week
            recordNumber = 1
            increaseTimeList = {}
            continue

        timeDiff = start - lastStartTime
        numberDiff = curNumber - lastNumber
        if numberDiff==0:
            breakFlag = True
            break
        increaseTime = (float) (timeDiff) / numberDiff;
        for i in range(recordNumber, curNumber+1):
            increaseTimeList[i] = increaseTime
        recordNumber = curNumber

        lastNumber = curNumber
        lastStartTime = start

    ###test

    if breakFlag==False:
        f = open('temp/%s.txt' % doctorName, 'w')
        for k in range(1,8):
            store_n = {"morning":{}, "afternoon":{},"night":{}}
            #f.write("=====(%d)======\n" %k)
#            for k in range(len(weeksData[lastweek][today]))
            for i in weeksData[k]:
                for interval in weeksData[k][i]:
                    for j in weeksData[k][i][interval]:
                        if j not in store_n[interval] :
                            store_n[interval][j] = []
                            store_n[interval][j].append(weeksData[k][i][interval][j]) 
                        else:
                            store_n[interval][j].append(weeksData[k][i][interval][j]) 
            #print(store_n)
            for inn in store_n:
                f.write("=====(%d %s)======\n" %(k,inn))
                for num in range(len(store_n[inn])):
                    #print (num+1, len(store_n[inn][num+1]))
                    store_n[inn][num+1].sort()
                    size_num = len(store_n[inn][num+1])
                    f.write('%d\t%.2f\t%d\t%s\n' %(num+1,store_n[inn][num+1][int(size_num/2)], size_num,inn))
        f.close()
    debugFile.close()
##########################
## main
##########################
DB.setDBFile('wanfang.db')
result = DB.listAll()
for doctor in result:
    generateData(doctor[1])
