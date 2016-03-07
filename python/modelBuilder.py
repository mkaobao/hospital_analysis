# This Python file uses the following encoding: utf-8

import datetime
import sys
import math
import collections
import database as DB
import delta

DB.setDBFile('wanfang.db')
#DB.setDBFile('vghtpe.db')


def two_digit_number(number):
    # Add '0' if number is less than 10

    number = int(number)
    if number < 10:
        return '0' + str(number)
    return str(number)


def sec_to_timestamp(second):
    # Naively convert integer seconds to time string

    out_sec = second%60
    second = second/60
    out_min = second%60
    out_hr = second/60
    return '%s:%s:%s' % (two_digit_number(out_hr), two_digit_number(out_min), two_digit_number(out_sec))


def timestamp_to_sec(timeString):
    # Naively convert time string to integer seconds

    curTimeTuple = timeString.split(':')
    return int(curTimeTuple[0]) * 3600 + int(curTimeTuple[1]) * 60 + int(curTimeTuple[2])


def interpolation(table, x = None, y = None):
    # TODO: 其實目前處理邊界條件還是有點問題
    maxKey = 0
    if x != None:
        for key, value in table.items():
            if key > maxKey:
                maxKey = key
        if x > maxKey:
            return (table[maxKey] - table[maxKey - 1]) * (x - maxKey)
        elif x < 1:
            return table[1] - (1-x) * (table[2] - table[1])
        else:
            return table[int(x)] + (x - math.floor(x)) * (table[int(math.ceil(x))] - table[int(x)])
    elif y != None:
        cap = 0
        for key, value in table.items():
            if key > maxKey:
                maxKey = key
        for i in range(1, len(table)):
            if table[i] >= y:
                cap = i
                break
        if cap > 1:
            return cap - 1 + float(y - table[cap - 1]) / (table[cap] - table[cap - 1])
        elif cap == 1:
            return 1
        else: # cap == 0
            return maxKey + float(y - table[maxKey]) / (table[maxKey] - table[maxKey - 1])
    else:
        return None


class ModelBuilder:

    __doctorName = None

    #lateSignBook = {} #record the passed patients' original order

    # Format: [date][shift] = List: [patient 1 dict, patient 2 dict, ...]
    __sessionData = {}
    # 計算總跳號
    __numberCount = 0
    # 計算總看診人次
    __orderCount = 0
    # 計算平均看診時間
    __durationSum = 0
    # 紀錄過號號碼的比例
    # Format: 星期:診次:{小時:{pass:A, total:X}}
    # Ex:[6][u'上午診']['09'] = {pass: 5, denominator: 300}
    __passProb = {}
    #以每小時紀錄遲到者出現的比例
    # Format: 星期:診次:{小時:{appeared:A, denominator:X}}
    # Ex:[6][u'上午診'][9] = {appeared: 1, denominator: 3000}
    __recoverProb = {}

    # 存date, shift中，某number的看診時間(in timeSeconds)
    __answerTime = {}

    def __init__(self, params):

        result = DB.searchByParams(params)
        # self.__doctorName = params['name'].encode('utf-8').decode('utf-8')
        self.__doctorName = params['name']
        lastDate = None
        lastShift = None
        lastRegularNumber = 0
        order = 1
        passedCount = 0
        
        for row in result:
            # DB row 1:Date, 2:Name, 3:Dept, 4:Room, 5:shift, 6:Comment, 7:CurNumber, 8:time, 9:End, 10:Duration
            curDate = unicode(row[1])
            curWeekday = datetime.datetime.strptime(curDate, '%Y-%m-%d').weekday() + 1
            curName = row[2].encode('utf-8').decode('utf-8')
            curDept = row[3]
            curShift = row[5].encode('utf-8').decode('utf-8')
            # Problematic flag for passed patients, deprecated in favor of simple decreasing number judging
            # if row[6] != '{"over":true}':
            #    continue
            curNumber = int(row[7])
            curDatetime = datetime.datetime.fromtimestamp(int(row[8]))
            curTime = curDatetime.strftime('%H:%M:%S')
            # 這不是真正計算時使用的調整過的等效duration
            durationSeconds = row[10]
            

            if not (curWeekday == 6 and curShift == u'上午診'):
                continue
            
            # TODO: 把後一號（後幾號）都解釋成過號，篩掉太短duration的
            ####### WHAT TO DO WITH THESE GUYS WHO JUST WON'T LEAVE!!??? (Some of them with good reasons maybe)
            if self.__number_came(curDate, curShift, curNumber):
                continue
            # TODO: Duration的篩選要切在多少？
            if durationSeconds < 30:
                continue

            if curShift != lastShift or curDate != lastDate:
                lastShift = curShift
                lastDate = curDate
                lastRegularNumber = 0
                order = 1
                passedCount = 0
            
            #PASSED patients:
            #if row[6] == '{"over":true}': # <== This is problematic. Some times patients were skipped too fast that regular patient would be viewed as passed by system
            if curNumber < lastRegularNumber:
                passedCount -= 1
                patient = {'number': curNumber, 'date': curDate.encode('utf-8'), 'time': curTime.encode('utf-8'), 'shift': curShift.encode('utf-8'), 'order': order, 'isPassed': 1, 'passedCount': passedCount}
                self.__session_append(curDate, curShift, patient)

            # REGULAR patients:
            else:
                numDiff = curNumber - lastRegularNumber
                passedCount += numDiff - 1
                lastRegularNumber = curNumber
                patient = {'number': curNumber, 'date': curDate.encode('utf-8'), 'time': curTime.encode('utf-8'), 'shift': curShift.encode('utf-8'), 'order': order, 'isPassed': 0, 'passedCount': passedCount}
                self.__session_append(curDate, curShift, patient)

            # answerTime[Date][shift][number] = answer in timeSeconds
            ModelBuilder.dict_update_recursive(self.__answerTime, {curDate: {curShift: {curNumber: timestamp_to_sec(curTime)}}})
            # End of iteration preparation
            order += 1
            

        for curDate, branch in self.__sessionData.items():
            for curShift, patients in branch.items():
                curWeekday = datetime.datetime.strptime(curDate, '%Y-%m-%d').weekday() + 1
                lastRegularNumber = 0
                
                # TESTing: 要drop最後一位，因為很可能是醫師放置play而已。當然也可能沒有這事
                patients.pop(len(patients) - 1)
                
                localMaxNumber = max(patients, key=lambda p:p['number'])['number']
                self.__numberCount += localMaxNumber
                self.__orderCount += len(patients)
                
                for i in range(1, len(patients)):
                    curHour = int(patients[i - 1]['time'].split(':')[0])
                    curDuration = timestamp_to_sec(patients[i]['time']) - timestamp_to_sec(patients[i - 1]['time'])
                    patients[i - 1]['duration'] = curDuration
                    self.__durationSum += curDuration
                    
                    # # TESTing inspecting
                    # if curDate == '2015-11-21':
                    #     print patients[i-1]['time'], patients[i-1]['number'], patients[i-1]['order'], patients[i-1]['isPassed']
                    
                    if patients[i - 1]['isPassed'] == 1:
                        try:
                            self.__recoverProb[curWeekday][curShift][curHour]['appeared'] += 1
                            self.__recoverProb[curWeekday][curShift][curHour]['denominator'] += patients[i - 1]['passedCount'] * curDuration
                        except KeyError:
                            branch = {curWeekday: {curShift: {curHour: {'appeared': 1, 'denominator': patients[i - 1]['passedCount'] * curDuration}}}}
                            ModelBuilder.dict_update_recursive(self.__recoverProb, branch)
                    elif patients[i - 1]['isPassed'] == 0:
                        numDiff = patients[i - 1]['number'] - lastRegularNumber
                        try:
                            self.__passProb[curWeekday][curShift][curHour]['pass'] += numDiff - 1
                            self.__passProb[curWeekday][curShift][curHour]['total'] += numDiff
                        except KeyError:
                            branch = {curWeekday: {curShift: {curHour: {'pass': numDiff - 1, 'total': numDiff}}}}
                            ModelBuilder.dict_update_recursive(self.__passProb, branch)
                        try:
                            self.__recoverProb[curWeekday][curShift][curHour]['denominator'] += patients[i - 1]['passedCount'] * curDuration
                        except KeyError:
                            branch = {curWeekday: {curShift: {curHour: {'appeared': 0, 'denominator': patients[i - 1]['passedCount'] * curDuration}}}}
                            ModelBuilder.dict_update_recursive(self.__recoverProb, branch)
                        lastRegularNumber = patients[i - 1]['number']

    def testing(self, outputPath = '', skip=1, vision=10):
        for curDate, branch in self.__sessionData.items():
            for curShift, patients in branch.items():
                curWeekday = datetime.datetime.strptime(curDate, '%Y-%m-%d').weekday() + 1
                
                # # TESTing 先用全部平均的方式算
                # appeared = 0
                # denominator = 0
                # for hour, hourData in self.__recoverProb[curWeekday][curShift].items():
                #     appeared += hourData['appeared']
                #     denominator += hourData['denominator']
                # reappFreq = float(appeared) / denominator
                
                passFreq = float(self.__orderCount) / self.__numberCount
                
                # i is the starting condition of prediction
                for i in range(0, len(patients)):
                    if i < skip:
                        continue
                    
                    # TESTing 其實應該是要從lastRegularNumber開始算，不過現在懶得區分XD
                    if patients[i]['isPassed'] == 1:
                        continue
                    
                    curTime = patients[i]['time']
                    curHour = int(curTime.split(':')[0])
                    try:
                        #其實這是計算完全消失的比例而非跳號的可能性，時間會高估。但是也可以說假設這些短期遲到的馬上都跑回來看了
                        # passFreq = 1.0 - float(self.__passProb[curWeekday][curShift][curHour]['pass']) / self.__passProb[curWeekday][curShift][curHour]['total']
                        reappFreq = float(self.__recoverProb[curWeekday][curShift][curHour]['appeared']) / self.__recoverProb[curWeekday][curShift][curHour]['denominator']
                        pass
                    except KeyError:
                        # TODO: why this happens?
                        print "KeyError"
                        try:
                            print self.__recoverProb[curWeekday][curShift][curHour]
                        except:
                            print "KeyError2"
                            # print curShift.encode('utf-8'), self.__recoverProb[curWeekday][curShift], curHour, curWeekday
                        continue
                    # j is the distance of prediction
                    for j in range(i + vision, len(patients)):
                        if patients[j]['isPassed'] == 1:
                            continue
                        
                        # # Limiting?
                        # if patients[j]['number'] - patients[i]['number'] > vision + 3:
                        #     continue
                        estimatedRegular = (patients[j]['number'] - patients[i]['number']) * passFreq
                        estimatedReappearance = math.floor(patients[i]['passedCount'] * self.get_average_time() * estimatedRegular * reappFreq)
                        estimation = (estimatedRegular + estimatedReappearance) * self.get_average_time()
                        answer = self.__answerTime[curDate][curShift][patients[j]['number']]
                        diff = answer - timestamp_to_sec(patients[i]['time']) - estimation
                        #Boring's Method
                        try:
                            diff2 = answer - timestamp_to_sec(patients[i]['time']) - self.BoringTest(patients[i]['number'], patients[j]['number'])
                        except KeyError:
                            continue
                        with open('%s/%s_test.txt' % (outputPath, self.__doctorName), 'a+') as ofp:
                            ofp.write('%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n' % (curDate.encode('utf-8'), curShift.encode('utf-8'), curTime.encode('utf-8'), patients[i]['passedCount'],
                                                                        patients[i]['number'], patients[j]['number'], diff, estimatedRegular, estimatedReappearance, j - i, diff2))
    
    def BoringTest(self, start, end):
        shiftDelta = 0
        for i in range(start, end):
            try:
                shiftDelta += delta.Delta[i]
            except KeyError:
                raise KeyError
        return shiftDelta

    @staticmethod
    def dict_update_recursive(d, u):
    # Ref: http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = ModelBuilder.dict_update_recursive(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def __session_append(self, date, shift, values):
        try:
            self.__sessionData[date][shift].append(values)
        except KeyError:
            branch = {date: {shift: [values]}}
            ModelBuilder.dict_update_recursive(self.__sessionData, branch)

    def __number_came(self, date, shift, number):
        try:
            if number in self.__answerTime[date][shift]:
                return True
            else:
                return False
        except KeyError:
            return False
    
    def get_average_time(self):
        return self.__durationSum / self.__orderCount


def prediction_test(params):
    pass

def max_abs(intArray):
    maxValue = max(intArray)
    minValue = min(intArray)
    if abs(maxValue) > abs(minValue):
        return maxValue
    else:
        return minValue


while True:
    # if usage:
    #     printUsage()
    #     usage = False
    line = raw_input('Enter path to the output folder: ')
    line = line.decode('utf-8')

    if len(line) != 0:
        #doctorList = DB.getDoctorList()
        #for doctor in doctorList:
        #    data = {}
        #    data['name'] = doctor
        #    data['filePath'] = filePath
        #    prediction_test(data)
        data = {'name':u'黃怡伶', 'filePath':line}
        testModel = ModelBuilder(data)
        testModel.testing(outputPath=line)
        print 'averageTime:', testModel.get_average_time()
    else:
        print 'unknow path'
        usage = True