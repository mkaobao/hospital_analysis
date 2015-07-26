# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from log_manager import ERRORLOG
from log_manager import SYSLOG
import os
import urllib
import urllib2
import time
import datetime
import re

dir_path        = '/home/mkao/workplace/hospital_analysis/crawler/'
hospital        = 'chimei'

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub(' ', data)

def parseDoctorData(url, file_ptr):
    try:
        handle    = urllib.urlopen(url)
        html_get  = handle.read()
        soup      = BeautifulSoup(html_get)
    except:
        ERRORLOG(hospital, 'url read failed!')
        return 60

    counter   = 1
    counter2  = 1
    line = ""
    for row in soup.find_all('td'):
        if counter2 == 1 :
            line = '%.0f ' % time.time()
        if counter2==3 :
            row = str(row).replace(" ", "")
            row = str(row).replace("醫師", "")
        if counter > 6 and (counter2 == 1 or counter2 == 2 or counter2 == 3 or counter2 == 6) :
            line = line + '%s ' % (striphtml(str(row)))
        
        counter2 = counter2 + 1
        counter  = counter  + 1

        if counter2 == 7 :
            if len(line.split(' ')) > 2 :
                file_ptr.write(line + '\n')
            line = ""
            counter2 = 1
    return 20

def getFilename(hospital):
    if not os.path.exists(dir_path + hospital) :
        os.makedirs(dir_path + hospital)
    date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
    file_name = dir_path + hospital + '/' + hospital + '_' + date  # file_path/file_name
    return file_name

hospital_url        = "http://www.chimei.org.tw/left/register/progress/qprogress.asp?idept="
hospital_url_dep_no = ['730','731','732','733','734','735','736','737','738','739','751','752','753','754','755','756','757','758','771','772','510','570','590','703','713','773','774','775','776','777','778','779']
hospital_url_dep    = ""
file_name = getFilename(hospital)
sleep_time = 0
file_count = 0

SYSLOG("chimei", "%s start!" % file_name)

while True:
    if file_count == 0:
        file_count = 180
        if file_name != getFilename(hospital) :
            SYSLOG("chimei", "%s is complete" % file_name)
            break
    file_count -= 1

    file_ptr = open(file_name, 'a')

    for no in hospital_url_dep_no :
        hospital_url_dep = hospital_url + no + "&host=10"
        sleep_time = parseDoctorData(hospital_url_dep, file_ptr)

    file_ptr.close()
    time.sleep( sleep_time )
