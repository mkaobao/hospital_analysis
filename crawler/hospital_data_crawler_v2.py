from bs4 import BeautifulSoup
import urllib
import time
import datetime

logFile			= 'error.log'

def parseDoctorData(url, file_ptr):
	timestamp 	= time.time()
	date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y_%m_%d %H:%M:%S')

	try:
		handle 		= urllib.urlopen(url)
		html_get 	= handle.read()
		soup 		= BeautifulSoup(html_get)
	except:
		log = open(logFile, 'a')
		log.write("%s [err] get web failed." % date)
		log.close()
		return 60

	print date + ' OK'

	# FIXME: combine two for loop
	for item_string in soup.find_all('div', {"class":"p3_tab_h2"}):
		array = []
		for index in range(0,6):
			content = unicode(item_string.contents[index].string).strip(' \n')
			array.append(content)
		file_ptr.write('%.0f %s %s %s %s %s %s\n' % (timestamp, array[0].encode('utf-8'),array[1].encode('utf-8'),array[2].encode('utf-8'),array[3].encode('utf-8'),array[4].encode('utf-8'),array[5].encode('utf-8')))

	for item_string in soup.find_all('div', {"class":"p3_tab_h4"}):
		array = []
		for index in range(0,6):
			content = unicode(item_string.contents[index].string).strip(' \n')
			array.append(content)
		file_ptr.write('%.0f %s %s %s %s %s %s\n' % (timestamp, array[0].encode('utf-8'),array[1].encode('utf-8'),array[2].encode('utf-8'),array[3].encode('utf-8'),array[4].encode('utf-8'),array[5].encode('utf-8')))
	return 20

def getFilename(hospital):
	date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
	file_name = hospital + '/' + hospital + '_' + date  # file_path/file_name
	return file_name

hospital 		= 'wanfang'
hospital_url  	= "http://www.wanfang.gov.tw/p3_register_visits.aspx"
sleep_time = 0
file_name = ''
file_count = 0

while True:
	if file_count == 0:
		file_count = 180
		temp_file_name = getFilename(hospital)
		if file_name != temp_file_name:
			file_name = temp_file_name
			print "file name is reset: " + file_name
	file_ptr = open(file_name, 'a')
	sleep_time = parseDoctorData(hospital_url, file_ptr)
	file_ptr.close()
	time.sleep( sleep_time )
	file_count -= 1
