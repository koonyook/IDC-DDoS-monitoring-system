import time
import datetime
import subprocess,shlex
import MySQLdb as mdb

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

#gather internal IP Address for screening
MAIN_DB_IP_ADDRESS="?.?.?.?"
MAIN_DB_USERNAME="?"
MAIN_DB_PASSWORD="?"
MAIN_DB_NAME="NetTracker"

IDCINFO_DB_IP_ADDRESS="?.?.?.?"
IDCINFO_DB_USERNAME="?"
IDCINFO_DB_PASSWORD="?"
IDCINFO_DB_NAME="idcinfo"
con = mdb.connect(IDCINFO_DB_IP_ADDRESS, IDCINFO_DB_USERNAME, IDCINFO_DB_PASSWORD, IDCINFO_DB_NAME)
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

con = mdb.connect(MAIN_DB_IP_ADDRESS, MAIN_DB_USERNAME, MAIN_DB_PASSWORD, MAIN_DB_NAME)
cur = con.cursor()

cur.execute("SELECT MAX(timestamp) FROM flowLog")
maxTime=cur.fetchone()[0]
startTime=None
if maxTime==None:
	startTime=cutSeconds(datetime.datetime.now())-datetime.timedelta(days=7)
else:
	timeStr="20"+str(maxTime)
	startTime=datetime.datetime(
		year=int(timeStr[0:4]),
		month=int(timeStr[4:6]),
		day=int(timeStr[6:8]),
		hour=int(timeStr[8:10]),
		minute=int(timeStr[10:12])
	) + datetime.timedelta(minutes=1)
	
	cmpTime=cutSeconds(datetime.datetime.now())-datetime.timedelta(days=7)
	if startTime<cmpTime:
		startTime=cmpTime

con.close()

while True:
	if cutSeconds(datetime.datetime.now())-startTime > datetime.timedelta(minutes=2):
		#time gap allow you to get more data
		timeStr=getTimeString(startTime)
		print "start",timeStr
		command="nfdump -M /mnt/netflow/cor-bkkcbw33:cor-bkkcbw34 -r nfcapd.%s -n 300 -s ip/flows -o csv -q"%(timeStr)
		result = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE)
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
			con = mdb.connect(MAIN_DB_IP_ADDRESS, MAIN_DB_USERNAME, MAIN_DB_PASSWORD, MAIN_DB_NAME)
			cur = con.cursor()
			
			cur.execute("INSERT INTO flowLog (timestamp,ip,flow) VALUES %s ;"%(valueString[0:-1]))

			con.close()

		startTime+=datetime.timedelta(minutes=1)
	
	else:
		time.sleep(60)



