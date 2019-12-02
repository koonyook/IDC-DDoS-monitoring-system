import time
import datetime
import subprocess,shlex
import MySQLdb as mdb

from mainDaemon import Daemon

import setting


#this is an example
#class MyDaemon(Daemon):
#	def run(self):
#		while True:
#			time.sleep(1)

def getTimeString(d):
	# d = datetime
	return str(d.year)+"%02d"%(d.month)+"%02d"%(d.day)+"%02d"%(d.hour)+"%02d"%(d.minute)

def sameMinute(a,b):
	if a.year==b.year and a.month==b.month and a.day==b.day and a.hour==b.hour and a.minute==b.minute:
		return True
	else:
		return False

def cutSeconds(d):
	return datetime.datetime(
		year=d.year,
		month=d.month,
		day=d.day,
		hour=d.hour,
		minute=d.minute
	)


class monflowd(Daemon):
	'''
	Monitoring NetFlow Daemon
	'''

	def run(self):

		con = mdb.connect(setting.IDCINFO_DB_IP_ADDRESS, setting.IDCINFO_DB_USERNAME, setting.IDCINFO_DB_PASSWORD, setting.IDCINFO_DB_NAME)
		cur = con.cursor()						
		allIP=[]
		cur.execute("SELECT IPV4_addr FROM ipv4 WHERE 1")
		while True:
			tmp=cur.fetchone()
			if tmp!=None:
				allIP.append(tmp[0])
			else:
				break
		con.close()
		print len(allIP)

		con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()

		cur.execute("SELECT MAX(timestamp) FROM flowLog")
		maxTime=cur.fetchone()[0]
		startTime=None
		if maxTime==None:
			startTime=cutSeconds(datetime.datetime.now())-datetime.timedelta(days=setting.DELETE_THRESHOLD_DAY)
		else:
			timeStr="20"+str(maxTime)
			startTime=datetime.datetime(
				year=int(timeStr[0:4]),
				month=int(timeStr[4:6]),
				day=int(timeStr[6:8]),
				hour=int(timeStr[8:10]),
				minute=int(timeStr[10:12])
			) + datetime.timedelta(minutes=1)
			
			cmpTime=cutSeconds(datetime.datetime.now())-datetime.timedelta(days=setting.DELETE_THRESHOLD_DAY)
			if startTime<cmpTime:
				startTime=cmpTime

		con.close()

		while True:
			if cutSeconds(datetime.datetime.now())-startTime > datetime.timedelta(minutes=2):
				#time gap allow you to get more data
				timeStr=getTimeString(startTime)
				print "start",timeStr
				command="/usr/local/bin/nfdump -M /mnt/netflow/cor-bkkcbw33:cor-bkkcbw34 -r nfcapd.%s -n 300 -s ip/flows -o csv -q"%(timeStr)
				result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
				result.wait()
				output=result.communicate()[0]
				output=output.split('\n')[1:-2]
				#print len(output)
				filteredIP=[]
				valueString=" "
				for line in output:
					#print line
					tmp=line.split(',')
					ip=tmp[4]
					flow=tmp[5]
					if ip in allIP:
						filteredIP.append((ip,flow))
						valueString+="(%s,'%s',%s),"%(timeStr[2:],ip,flow)
						#print ip,flow
				print len(filteredIP)
				if len(filteredIP)>0:
					con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
					cur = con.cursor()
					
					cur.execute("INSERT INTO flowLog (timestamp,ip,flow) VALUES %s ;"%(valueString[0:-1]))
					
					thresholdStr=getTimeString(startTime-datetime.timedelta(days=setting.DELETE_THRESHOLD_DAY))
					cur.execute("DELETE FROM log WHERE timestamp<%s"%(thresholdStr[2:]))

					con.close()

				startTime+=datetime.timedelta(minutes=1)
			
			else:
				time.sleep(60)
