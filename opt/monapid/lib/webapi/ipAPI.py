import setting
import MySQLdb as mdb
import subprocess, shlex
import json
import datetime
from util import general
from util import shortcut
import cherrypy


class GetFlow(object):
	'''
	return flow of that ip {start_minute=timestamp, end_minute=timestamp, data=[]}
	'''
	def index(self, ip, subPlot='', days=3):
		if len(ip.split('.'))!=4:
			return shortcut.response({'status':'error','message':'Invalid IP Address'})
		else:
			con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
			cur = con.cursor()
			
			timestampThreshold = datetime.datetime.now() - datetime.timedelta(days=int(days))

			cur.execute("SELECT timestamp,flow,packet,size FROM flowLog WHERE ip='%s' AND timestamp>%s ORDER BY timestamp "%(ip,timestampThreshold.strftime('%s')))
			
			dataList=[]
			while True:
				tmp=cur.fetchone()
				if tmp!=None:
					timestamp,flow,packet,size=tmp
					if dataList==[]:
						dataList.append((timestamp,flow,packet,size))
					else:
						while dataList[-1][0]<timestamp-60:
							dataList.append((dataList[-1][0]+60,None,None,None))
						dataList.append((timestamp,flow,packet,size))
				else:
					break
			con.close()
			
			if dataList==[]:
				return shortcut.response({'status':'error','message':'No log'})
			else:
				startMinute=dataList[0][0]
				endMinute=dataList[-1][0]
				
				flowList=[]
				subList=[]
				for element in dataList:
					flowList.append(element[1])
					if element[1]==None:
						subList.append(None)
					elif subPlot=='ppf':
						subList.append(element[2]/element[1])
					elif subPlot=='spf':
						subList.append(1000*element[3]/element[1])
					elif subPlot=='spp':
						subList.append(1000*element[3]/element[2])
					elif subPlot=='p':
						subList.append(element[2])
					elif subPlot=='s':
						subList.append(1000*element[3])
					else:
						subList.append(None)

				if subPlot=='ppf':
					subName='Packet per Flow'
				elif subPlot=='spf':
					subName='Size per Flow'
				elif subPlot=='spp':
					subName='Size per Packet'
				elif subPlot=='p':
					subName='Packet'
				elif subPlot=='s':
					subName='Size'
				else:
					subName='[wrong key]'
							
				return shortcut.response({'status':'OK','start_minute':startMinute,'end_minute':endMinute,'flow':flowList,'subList':subList, 'subName':subName})

	index.exposed = True

class GetTop(object):
	'''
	return set of current to ip and flow { timestamp:, data:[(ip,flow),(ip,flow),(ip,flow)] }
	'''
	def index(self,orderby='flow', n='20', timestamp=None):
		if not n.isdigit or orderby not in ['flow','packet','size']:
			return shortcut.response({'status':'error','message':'Invalid number'})
		else:
			con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
			cur = con.cursor()
			
			if timestamp==None:
				#get last timestamp
				cur.execute("SELECT MAX(timestamp) FROM flowLog")
				lastTimestamp=cur.fetchone()[0]
			else:
				lastTimestamp=timestamp

			cur.execute("SELECT ip,flow,packet,size FROM flowLog WHERE timestamp=%s ORDER BY %s DESC LIMIT 0, %s"%(lastTimestamp,orderby,str(n)))
			
			dataList=[]
			ipSetString=" ("
			while True:
				tmp=cur.fetchone()
				if tmp!=None:
					dataList.append([tmp[0],tmp[1],tmp[2],tmp[3],tmp[2]/tmp[1]])
					ipSetString += "'%s',"%(tmp[0])
				else:
					break
			ipSetString=ipSetString[0:-1]+')'
			con.close()
			
			if dataList!=[]:
				con = mdb.connect(setting.IDCINFO_DB_IP_ADDRESS, setting.IDCINFO_DB_USERNAME, setting.IDCINFO_DB_PASSWORD, setting.IDCINFO_DB_NAME)
				cur = con.cursor()
				cur.execute("""SELECT pipe_has_ipv4.IPV4_addr, project.ProjectID, project.ProjectName
				FROM project
				INNER JOIN mainpipe ON mainpipe.ProjectID = project.ProjectID
				INNER JOIN pipe_has_ipv4 ON pipe_has_ipv4.PipeID = mainpipe.PipeID
				WHERE pipe_has_ipv4.IPV4_addr IN %s
				"""%(ipSetString))
				for i in range(cur.rowcount):
					ip,projectID,projectName=cur.fetchone()
					for element in dataList:
						if element[0]==ip:
							element.append(projectID)
							element.append(projectName)
							break
				
				con.close()			
			return shortcut.response({'status':'OK','timestamp':lastTimestamp, 'data':dataList})

	index.exposed = True

class IPStat(object):
	getFlow = GetFlow()
	getTop = GetTop()