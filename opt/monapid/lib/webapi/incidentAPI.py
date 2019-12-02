import setting
import MySQLdb
import subprocess, shlex
import json
import time
from util import general
from util import shortcut
import cherrypy


class Add(object):
	'''
	test adding incident
	'''
	def index(self, subject, oids='', type=-1):
		timestamp=int(time.time())
		con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		cur.execute("INSERT INTO incident (incident_type, timestamp_start, subject, detail) VALUES (%s,%s,'%s','%s');"%(str(type),str(timestamp),subject,'just a testing'))
		incidentID = con.insert_id()
		if (oids!=''):
			oids=oids.split(',')
			valueString=''
			for oid in oids:
				valueString+= " (%s,%s),"%(str(incidentID),str(oid))
			valueString=valueString[0:-1]+';'
			cur.execute("INSERT INTO incident_port (incidentID, O_ID) VALUES "+valueString)
		con.close()
		return shortcut.response({'incidentID':incidentID})

	index.exposed = True

class Acknowledge(object):
	'''
	end incident
	'''
	def index(self, incidentID, method='button'):	#method can be 'auto'
		timestamp=int(time.time())
		if method=='button':
			method=2
		elif method=='auto':
			method=1
		else:
			method=3
		
		con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		cur.execute("UPDATE incident SET status=%s, timestamp_end=%s WHERE incidentID=%s AND status=0 ;"%(str(method),str(timestamp),str(incidentID)))
		affectedRow=cur.rowcount
		con.close()
		if affectedRow==1:
			return shortcut.response({'result':'OK'})
		elif affectedRow==0:
			return shortcut.response({'result':'error', 'message':'This incident had been ended before.'})

	index.exposed = True

class GetAll(object):
	'''
	send all incident info for display in browser
	'''
	def index(self):	#method can be auto
		answerDict={}
		con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		cur.execute("SELECT incidentID, incident_type, timestamp_start, subject, detail FROM incident WHERE status=0")
		for i in range(cur.rowcount):        
			row = cur.fetchone()
			answerDict[row[0]]={'incident_type':row[1], 'timestamp_start':row[2], 'subject':row[3], 'detail':row[4], 'oids':[]}
		
		cur.execute("SELECT incident.incidentID, O_ID FROM incident JOIN incident_port ON incident.incidentID=incident_port.incidentID WHERE status=0")
		for i in range(cur.rowcount):
			row = cur.fetchone()
			if row[0] in answerDict:
				answerDict[row[0]]['oids'].append(row[1])

		con.close()
		return shortcut.response(answerDict)

	index.exposed = True

class Incident(object):
	testAdd = Add()
	acknowledge = Acknowledge()
	getAll = GetAll()

