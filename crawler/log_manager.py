import os
import time
import datetime

dir_path = '/home/mkao/workplace/hospital_analysis/crawler/'
LOG_PATH = dir_path + 'log/'

class LOG_LEVEL:
	SYSTEM = LOG_PATH + 'sys.log'
	DEBUG  = LOG_PATH + 'debug.log'
	ERROR  = LOG_PATH + 'error.log'

def createLogDir():
	if not os.path.exists(LOG_PATH):
		os.makedirs(LOG_PATH)

def writeLog(level, tag, message):
	createLogDir()
	date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d %H:%M:%S')
	fd = open(level, 'a')
	fd.write('%s [%s]\t%s\n' % (date, tag, message))
	fd.close()

def ERRORLOG(tag, message):
	writeLog(LOG_LEVEL.ERROR, tag, message)

def DEBUGLOG(tag, message):
	writeLog(LOG_LEVEL.DEBUG, tag, message)

def SYSLOG(tag, message):
	writeLog(LOG_LEVEL.SYSTEM, tag, message)