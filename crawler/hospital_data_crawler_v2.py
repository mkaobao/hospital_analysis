from bs4 import BeautifulSoup
from log_manager import ERRORLOG
from log_manager import SYSLOG
import os
import urllib
import time
import datetime

dir_path 		= '/home/mkao/workplace/hospital_analysis/crawler/'
hospital        = 'wanfang'

def printData(timestamp, elements):
    for item_string in elements:
        array = []
        for index in range(0,6):
            content = unicode(item_string.contents[index].string).strip(' \n')
            array.append(content)
        file_ptr.write('%.0f %s %s %s %s %s %s\n' % (timestamp, array[0].encode('utf-8'),array[1].encode('utf-8'),array[2].encode('utf-8'),array[3].encode('utf-8'),array[4].encode('utf-8'),array[5].encode('utf-8')))

def parseDoctorData(url, file_ptr):
    try:
        handle       = urllib.urlopen(url)
        html_get     = handle.read()
        soup         = BeautifulSoup(html_get)
    except:
        ERRORLOG('wanfang', 'url read failed!')
        return 60

    timestamp     = time.time()
    printData(timestamp, soup.find_all('div', {"class":"p3_tab_h2"}))
    printData(timestamp, soup.find_all('div', {"class":"p3_tab_h4"}))
    return 20

def getFilename(hospital):
    if not os.path.exists(dir_path + hospital) :
		os.makedirs(dir_path + hospital)
    date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
    file_name = dir_path + hospital + '/' + hospital + '_' + date  # file_path/file_name
    return file_name


hospital_url      = "http://www.wanfang.gov.tw/p3_register_visits.aspx"
file_name         = getFilename(hospital)
sleep_time        = 0
file_count        = 0

SYSLOG("wanfang", "%s start!" % file_name)

while True:
    if file_count == 0:
        file_count = 180
        if file_name != getFilename(hospital):
            SYSLOG("wanfang", "%s is complete" % file_name)
            break
    file_count -= 1
    
    file_ptr = open(file_name, 'a')
    sleep_time = parseDoctorData(hospital_url, file_ptr)
    file_ptr.close()
    time.sleep( sleep_time )