from bs4 import BeautifulSoup
import urllib
import time

def getHtml(url):
	handle = urllib.urlopen(url)
	html_get = handle.read()
	soup = BeautifulSoup(html_get)
	return soup.prettify('utf-8')


thisurl = "http://www.wanfang.gov.tw/p3_register_visits.aspx"

for i in range(0,3600):
	html = getHtml(thisurl)
	file_name = 'data_%.0f' % (time.time())
	print file_name
	file = open('data/'+file_name, 'w')
	file.write(html)
	file.close()
	print '%d mins' % (i)
	time.sleep(60)

