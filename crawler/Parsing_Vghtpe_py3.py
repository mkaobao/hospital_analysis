#simple parsing with BeaytifulSoup
# -*- coding: utf8 -*-

from bs4 import BeautifulSoup
import time 
import datetime
import re
import os, sys, urllib.request, urllib.parse, urllib.error

#setting filename

dir_path  = '/Users/eeder/workplace/hospital_analysis/crawler/'    #mac
#dir_path  = '/home/eeder/workplace/hospital_analysis/crawler/' #ubuntu
hospital = 'vghtpe'

logFile = 'error_vghtpe.log'
#syslog = open('/home/eeder/workplace/hospital_analysis/code/system_vghtpe.log','a')
syslog = open('system_vghtpe.log','a')

#get url
url0 = "https://www6.vghtpe.gov.tw/opd/servlet/opd.Roomsta2?sect="
url1 ={'91|一般體檢科','01|一般內科暨職業醫學','G0|整合門診 17診','GA|整合門診 18診(週一)','GB|整合門診 18診(週二)','GB|整合門診 18診(週二)','GD|整合門診 18診(週四)','GF|整合門診 18診(週五)','55|家庭醫學科','57|高齡醫學門診','13|神經內科','12|胸腔內科','27|氣喘特別門診','03|心臟內科','30|心律不整特診','60|成人先天心臟','04|腸胃科','G4|鏡檢中心門診','07|腎臟科','21|過敏免疫風濕','06|新陳代謝科','02|感染科','16|血液腫瘤科','79|臨床腫瘤門診','26|運動醫學科','50|骨病科','78|一般骨科','37|骨折科','38|脊椎外科','53|關節重建科','40|手外科','35|神經外科','19|神經修復','29|神經復健','24|神經泌尿','59|一般外科','46|乳房疾病門診','33|胸腔外科','34|心臟外科','43|主動脈瘤門診','25|心臟移植門診','32|器官移植門診','G5|導管瓣膜特診','G6|減重外科門診','39|泌尿外科','44|直腸外科','36|整型外科','45|周邊血管門診','73|急診外傷門診','51|醫學美容門診','82|婦產科','63|兒童內科','64|兒童心臟科','65|兒童神內癲癇','69|兒童血液科','70|兒童腸胃科','67|兒童腎臟科','71|兒童過敏感染','75|兒童內分泌','76|早產兒門診','62|兒童外科','49|兒童牙科','74|兒童骨科','61|兒童神經外科','10|眼科','PJ|學童護眼門診','52|耳科','80|鼻科','81|喉科','E7|助聽器特診','09|牙科','85|矯正牙科','28|身心失眠門診','G7|睡眠障礙門診','77|一般精神科','14|老年精神科','15|青少年心理','G9|兒青心智障礙門診','53|青少年保健門診','08|皮膚科','18|皮膚美容門診','83|中醫內科','89|針灸傷科','41|復健醫學','17|疼痛控制科','20|肌無力','54|老人流感','42|放射線治療科','90|放射線部診療','48|癌葯物治療科','56|營養諮詢','72|身障重建門診','22|急診內科門診','G2|抗凝藥師門診','92|大我內科','93|大我外科','94|大我家醫科','95|大我眼科','96|大我皮膚科','97|大我耳鼻喉科'}
url2 = "&itval="
url3 = {'0|上午','1|下午','2|夜間'}
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
def getFilename(hospital):
    if not os.path.exists(dir_path + hospital) :
        os.makedirs(dir_path + hospital )
    date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
    file_name = dir_path + hospital + '/' + hospital + '_' + date  # file_path/file_name
    return file_name


def ParseDoctorData(url,file_ptr,t_interval):
    try :
        handle   = urllib.request.urlopen(url)
        page = handle.read()
        html_get = page.decode('big5','ignore')
        soup = BeautifulSoup(html_get,"html.parser")
        
    except:
        log = open(logFile, 'a')
        log.write("%s [err] get web failed.\n " %(Get_datetime()))
        log.close()
        print(Get_datetime() , " : get web failed")
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
                file_ptr.write('%s診 '%(t_interval[2:4]))
                file_ptr.write('%s ' %(title))
            if(count != 3):
                if(count == 1):
                    file_ptr.write('%s ' %(row.string.replace("　","")))
                else:
                    file_ptr.write('%s ' %(row.string))
            else:
                file_ptr.write('\n')
            count = (count+1)%4
        else:
            count2 += 1
            
    return 20

#main start

syslog.write("%s [start] vghtpe.\n " %(Get_datetime()))


file_name         = getFilename(hospital)
file_count        = 0

var = 0
while True:
    if file_count == 0:
        file_count = 180
        if file_name != getFilename(hospital):
            print("%s qq\n" %file_name)
            file_edit = open(file_name)
            print("here? \n")
            row = []
            for a in file_edit:
                asp = a.split()
                if (len(asp) != 5 and asp[5] != '施工中' and asp[5] != '看診結束'):
                    row.append(a)
            file_write = open(file_name,'w')
            print("or Here? \n")
            for k in row:
                file_write.write(k)
            syslog.write("%s [end] vghtpe is complete.\n " %(Get_datetime()))
            print('vghtpe, %s is complete' %file_name)
            break
    file_count -= 1

    file_ptr = open(file_name, 'a')
    for i in url1:
        k = i
        i = urllib.parse.quote(i.encode('big5'))
        for j in url3:
            t = j
            j = urllib.parse.quote(j.encode('big5'))
            url = url0 + i + url2 + j
            var = ParseDoctorData(url,file_ptr,t)
    time.sleep(var)
    file_ptr.close()
