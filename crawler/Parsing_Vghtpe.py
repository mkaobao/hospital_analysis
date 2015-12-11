#simple parsing with BeaytifulSoup
# -*- coding: utf8 -*-

from bs4 import BeautifulSoup
import time 
import datetime
import re
import os, sys, urllib, urllib2

#reload system with utf-8
reload(sys)
sys.setdefaultencoding('utf8')

#setting filename
logFile = 'error.log'
file_name = 'test'


#get url
url0 = "https://www6.vghtpe.gov.tw/opd/servlet/opd.Roomsta2?sect="
url1 ={u'91|一般體檢科',u'01|一般內科暨職業醫學',u'G0|整合門診 17診',u'GA|整合門診 18診(週一)',u'GB|整合門診 18診(週二)',u'GB|整合門診 18診(週二)',u'GD|整合門診 18診(週四)',u'GF|整合門診 18診(週五)',u'55|家庭醫學科',u'57|高齡醫學門診',u'13|神經內科',u'12|胸腔內科',u'27|氣喘特別門診',u'03|心臟內科',u'30|心律不整特診',u'60|成人先天心臟',u'04|腸胃科',u'G4|鏡檢中心門診',u'07|腎臟科',u'21|過敏免疫風濕',u'06|新陳代謝科',u'02|感染科',u'16|血液腫瘤科',u'79|臨床腫瘤門診',u'26|運動醫學科',u'50|骨病科',u'78|一般骨科',u'37|骨折科',u'38|脊椎外科',u'53|關節重建科',u'40|手外科',u'35|神經外科',u'19|神經修復',u'29|神經復健',u'24|神經泌尿',u'59|一般外科',u'46|乳房疾病門診',u'33|胸腔外科',u'34|心臟外科',u'43|主動脈瘤門診',u'25|心臟移植門診',u'32|器官移植門診',u'G5|導管瓣膜特診',u'G6|減重外科門診',u'39|泌尿外科',u'44|直腸外科',u'36|整型外科',u'45|周邊血管門診',u'73|急診外傷門診',u'51|醫學美容門診',u'82|婦產科',u'63|兒童內科',u'64|兒童心臟科',u'65|兒童神內癲癇',u'69|兒童血液科',u'70|兒童腸胃科',u'67|兒童腎臟科',u'71|兒童過敏感染',u'75|兒童內分泌',u'76|早產兒門診',u'62|兒童外科',u'49|兒童牙科',u'74|兒童骨科',u'61|兒童神經外科',u'10|眼科',u'PJ|學童護眼門診',u'52|耳科',u'80|鼻科',u'81|喉科',u'E7|助聽器特診',u'09|牙科',u'85|矯正牙科',u'28|身心失眠門診',u'G7|睡眠障礙門診',u'77|一般精神科',u'14|老年精神科',u'15|青少年心理',u'G9|兒青心智障礙門診',u'53|青少年保健門診',u'08|皮膚科',u'18|皮膚美容門診',u'83|中醫內科',u'89|針灸傷科',u'41|復健醫學',u'17|疼痛控制科',u'20|肌無力',u'54|老人流感',u'42|放射線治療科',u'90|放射線部診療',u'48|癌葯物治療科',u'56|營養諮詢',u'72|身障重建門診',u'22|急診內科門診',u'G2|抗凝藥師門診',u'92|大我內科',u'93|大我外科',u'94|大我家醫科',u'95|大我眼科',u'96|大我皮膚科',u'97|大我耳鼻喉科'}
url2 = "&itval="
url3 = {u'0|上午',u'1|下午',u'2|夜間'}
def Get_datetime():
    date = datetime.datetime.today()
    return date
#-------------------------------------------------
#date = today.strftime("%Y.%m.%d %H:%M:%S %y %b")
  # %y : the year two digits
  # %Y : the all year
  # %m : the month number
  # %b : the month abbreviation
  # %d : the day number
  # %H : the hour number
  # %M : the minite number
  # $S : the second number

#-------------------------------------------------



def ParseDoctorData(url,file_ptr):
    try :
        handle   = urllib.urlopen(url)
        page = handle.read()
        html_get = page.decode('big5','ignore')
        soup = BeautifulSoup(html_get,"html.parser")
        
    except:
        log = open(logFile, 'a')
        log.write("%s [err] get web failed." %(Get_datetime()))
        log.close()
        print Get_datetime , " : get web failed"
        return 60

    count = 0
    count2 = 0
    title = ""
    tm = time.time()
   # print soup
    for row in soup.find_all('td'):
        if (count2 == 0):
            title = row.string.replace("\r\n","")
            title = title.replace("    ","")
        if(count2 > 4):
            if(count == 0):
                file_ptr.write('%.0f ' % (tm))
                file_ptr.write('%s ' %(title))
            if(count != 3):
                if(count == 1):
                    file_ptr.write('%s ' %(row.string.replace(u"　","")))
                else:
                    file_ptr.write('%s ' %(row.string))
            else:
                file_ptr.write('\n')
            count = (count+1)%4
        else:
            count2 += 1
            
    print Get_datetime() , ' OK'
    return 20

#main

var = 0
while True:
    file_ptr = open(file_name, 'a')
    for i in url1:
        i = urllib.quote(i.encode('big5'))
        for j in url3:
            j = urllib.quote(j.encode('big5'))
            url = url0 + i + url2 + j
            var = ParseDoctorData(url,file_ptr)
    time.sleep(20)
    file_ptr.close()
