import time
import subprocess,shlex
import MySQLdb

headCommand="INSERT INTO log (O_ID, timestamp, attribute, value) VALUES "
lastHeadCommand="REPLACE INTO lastLog (O_ID, timestamp, attribute, value) VALUES "
def submit_list(waitList):
	con = MySQLdb.connect("?.?.?.?", "user", "password", "NetTracker")
	cur = con.cursor()
	query=""
	for content in waitList:
		query+="(%s,%s,'%s',%s),"%(str(content[0]),str(content[1]),str(content[2]),str(content[3]))
	
	query=query[0:-1]+';'

	cur.execute(headCommand+query)
	cur.execute(lastHeadCommand+query)
	con.close()

mapping={}
lastPoint={}
lastResponse={}	#for each [E_Name][spicific] -> 'NO' or 'OK'
resultList=[]
con = MySQLdb.connect("?.?.?", "user", "password", "E_Mon")
cur = con.cursor()

cur.execute("SELECT O_ID, ifIndex, E_Name FROM Equipment_Detail JOIN Equipment ON Equipment_Detail.E_ID=Equipment.E_ID JOIN Division ON Equipment.D_ID=Division.D_ID WHERE D_Name LIKE '%IDC%'")

while True:
	row=cur.fetchone()
	if row is not None:
		O_ID=row[0]
		ifIndex=row[1]
		E_Name=row[2]
		if E_Name not in mapping:
			mapping[E_Name]={}
			lastResponse[E_Name]={};
			lastResponse[E_Name]['ifHCInOctets']='NO'
			lastResponse[E_Name]['ifHCOutOctets']='NO'

		mapping[E_Name][ifIndex]=O_ID
		lastPoint[O_ID]={}
	else:
		break

con.close()

print "finish mapping"

resultList=[]

#calculation round
while True:
	print "start a calculation round"
	totalWait=0.0
	startTime=time.time()

	#fire snmpwalk commands 
	for E_Name in mapping:
		for specific in ['ifHCInOctets','ifHCOutOctets']:
			command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s %s"%(E_Name,specific)
			result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
			resultList.append({'E_Name':E_Name,'specific':specific,'timestamp':int(time.time()),'result':result})
	
	waitList=[]
	for element in resultList:
		E_Name=element['E_Name']
		specific=element['specific']
		result=element['result']
		beforeWait=time.time()
		result.wait()
		afterWait=time.time()
		totalWait+=(afterWait-beforeWait)
		timestamp=element['timestamp']
		output=result.communicate()[0]
		output=output.split('\n')[0:-1]
		
		#many cases here
		
		if lastResponse[E_Name][specific]=='NO' and len(output)==0:
			#Nothing to do (Nothing is changed from the last time)
			pass

		elif lastResponse[E_Name][specific]=='NO' and len(output)>0:
			#Keep initial value (nothing to do with database)
			for line in output:
				temp=line.split('.')[1].split(' ')
				ifIndex=int(temp[0])
				
				if ifIndex in mapping[E_Name]:
					val=int(temp[3])
					O_ID=mapping[E_Name][ifIndex]
					
					lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val}

			lastResponse[E_Name][specific]='OK'
		
		elif lastResponse[E_Name][specific]=='OK' and len(output)==0 :
			#node become dead (submit to database)
			for ifIndex in mapping[E_Name]:
				O_ID=mapping[E_Name][ifIndex]
				lastPoint[O_ID][specific]={'timestamp': timestamp, 'value':'NULL'}
				
				waitList.append([O_ID,timestamp,specific[4],'NULL'])
				if len(waitList)>=300:
					#push these info to database
					submit_list(waitList)
					waitList=[]

			lastResponse[E_Name][specific]='NO'
		
		elif lastResponse[E_Name][specific]=='OK' and len(output)>0 :
			#normal response, have last result (most general)
			for line in output:
				temp=line.split('.')[1].split(' ')
				ifIndex=int(temp[0])

				if ifIndex in mapping[E_Name]:
					val=int(temp[3])
					O_ID=mapping[E_Name][ifIndex]
					byteDiff=(val-lastPoint[O_ID][specific]['value'])
					if byteDiff<0:
						print byteDiff
						byteDiff+=18446744073709551616  #2^64
					bitRate=int(byteDiff*8/(timestamp-lastPoint[O_ID][specific]['timestamp']))
					lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val}
					
					waitList.append([O_ID,timestamp,specific[4],bitRate])
					if len(waitList)>=300:
						#push these info to database
						submit_list(waitList)
						waitList=[]
	
	if len(waitList)>0:	#last query for the rest of data in this round
		#push these info to database
		submit_list(waitList)
		waitList=[]

	resultList=[]
	finishTime=time.time()
	print "timeUsage(in seconds)", int(finishTime-startTime)
	print "waitUsage(in seconds)", int(totalWait)
	time.sleep(60)


