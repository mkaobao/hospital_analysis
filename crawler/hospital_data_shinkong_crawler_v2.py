# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from log_manager import ERRORLOG
from log_manager import SYSLOG
import os
import urllib
import time
import datetime
import re

dir_path   = '/home/mkao/workplace/hospital_analysis/crawler/'
hospital   = 'shinkong'

# remove html tag
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub(' ', data)

# pinrt data into txt
def printer(item, date, dept, file_ptr):
    counter = 0
    for i in range(len(item)/6):
        timestamp     = time.time()
        if "即將開始看診" in item[counter+1] :
            return
        if "結束看診" in item[counter+1] :
            counter = counter + 3
            continue
        file_ptr.write('%.0f %s %s %s %s %s\n' % (timestamp, date, dept, item[counter], item[counter+1], item[counter+4]))
        counter = counter + 6
    
def parseDoctorData(url, file_ptr):
    try:
        handle       = urllib.urlopen(url)
        html_get     = handle.read()
        soup         = BeautifulSoup(html_get)
    except:
        ERRORLOG('shinkong', 'url read failed!')
        return 60

    lblDate = soup.find_all('span', {"id":"lblNoon"})
    lblDept = soup.find_all('span', {"id":"lblDept"})
    
    #看診時間 上午 下午 夜間, 以及科別
    resign_Date = striphtml(str(lblDate)).split()
    resign_Dept = striphtml(str(lblDept)).split()

    for item_string in soup.find_all('span', {"id":"Label1"}):
        resign_string = striphtml(str(item_string))
        
        # 未開診 跳過
        if "未開診" in resign_string: 
            continue
        
        item = resign_string.split()
        item.pop(0)
        item.pop(0)
        item.pop(0)
        printer(item, resign_Date[1], resign_Dept[1], file_ptr)

    return 20

def getFilename(hospital):
    if not os.path.exists(dir_path + hospital) :
        os.makedirs(dir_path + hospital)
    date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
    file_name = dir_path + hospital + '/' + hospital + '_' + date  # file_path/file_name
    return file_name



hospital_url        = "https://regis.skh.org.tw/regisn/RegistProgressList.aspx?DeptNo="
hospital_url_dep_no = ['01','02','03','04','05','06','07','08','09','MA','11','12','13','14','15','16','17','19','20','21','22','23','24','25','26','27','28','29','31','41','43','45','66','67','99']
hospital_url_dep    = ""
file_name = getFilename(hospital)
sleep_time = 0
file_count = 0

SYSLOG("shinkong", "%s start!" % file_name)

while True:
    if file_count == 0:
        file_count = 180
        if file_name != getFilename(hospital):
            SYSLOG("shinkong", "%s is complete" % file_name)
            break
    file_count -= 1
    
    file_ptr = open(file_name, 'a')
    
    for no in hospital_url_dep_no :
        hospital_url_dep = hospital_url + no
        sleep_time = parseDoctorData(hospital_url_dep, file_ptr)
    
    file_ptr.close()
    time.sleep( sleep_time )
