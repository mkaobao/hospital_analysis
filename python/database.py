# This Python file uses the following encoding: utf-8
import sqlite3 as lite
import os.path

_con = None
_cur = None

def check_file_exist(fileName):
	return os.path.exists(fileName)

def init_db():
	global _cur
	_cur.execute("CREATE TABLE pacient_list(Id INTEGER PRIMARY KEY, Datetime TEXT, Name TEXT, Dept TEXT, Room TEXT, Interval TEXT, Comment TEXT, CurNumber INTEGER, Start INTEGER, End INTEGER, Duration INTEGER);")
	_cur.execute("PRAGMA journal_mode=WAL;")

def setDBFile(fileName):
	global _con
	global _cur
	ret = check_file_exist(fileName)
	_con = lite.connect(fileName)
	_cur = _con.cursor()
	if False == ret:
		init_db()

def insert(params):
	_cur.execute("INSERT INTO pacient_list(Datetime, Name, Dept, Room, Interval, Comment, CurNumber, Start, End, Duration) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%d', '%d', '%d', '%d');" % (params['datetime'], params['name'], params['dept'], params['room'], params['interval'], params['comment'], params['curnumber'], params['start'], params['end'], params['duration']))
	_con.commit()

def checkPoint():
	_cur.execute("PRAGMA wal_checkpoint(PASSIVE);")

def listAll():
	_cur.execute("SELECT DISTINCT Dept, Name FROM pacient_list ORDER BY Dept, Name;")
	return _cur.fetchall()

def searchByParams(params):
	if 'name' in params:
		query = 'Name="%s"' % params['name']
		if 'date' in params:
			query += ' AND Datetime="%s"' % params['date']
		if 'interval' in params:
			string = '上午診'
			if params['interval'] == 'M' or params['interval'] == 'm':
				string = '上午診'
			elif params['interval'] == 'A' or params['interval'] == 'a':
				string = '下午診'
			elif params['interval'] == 'N' or params['interval'] == 'n':
				string = '夜間診'
			query += ' AND Interval="%s"' % string
		_cur.execute("SELECT * FROM pacient_list WHERE %s ORDER BY Datetime, Start;" % query)
		return _cur.fetchall()
	else:
		return []

def getDoctorList():
	_cur.execute("SELECT DISTINCT Name FROM pacient_list;")
	return _cur.fetchall()

def close():
	_con.close()

# def update(params):
# def delete(params):
