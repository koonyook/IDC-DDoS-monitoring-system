import time
import subprocess,shlex
import MySQLdb

from mainDaemon import Daemon

import setting


#this is an example
#class MyDaemon(Daemon):
#	def run(self):
#		while True:
#			time.sleep(1)

headCommand="INSERT INTO log (O_ID, timestamp, attribute, value) VALUES "
lastHeadCommand="REPLACE INTO lastLog (O_ID, timestamp, attribute, value) VALUES "

def submit_list(waitList):
	con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
	cur = con.cursor()
	query=""
	for content in waitList:
		query+="(%s,%s,'%s',%s),"%(str(content[0]),str(content[1]),str(content[2]),str(content[3]))
	
	query=query[0:-1]+';'

	cur.execute(headCommand+query)
	cur.execute(lastHeadCommand+query)
	con.close()

def delete_old_log():
	con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
	cur = con.cursor()
	cur.execute("DELETE FROM log WHERE timestamp<"+(str(int(time.time())-(setting.DELETE_THRESHOLD_DAY*24*60*60))))
	con.close()

class monwalkd(Daemon):
	'''
	Monitoring walk Daemon
	'''

	def run(self):
		mapping={}
		supportHC={} # O_ID -> boolean
		speed={} # O_ID -> Kbps
		matched={} # O_ID -> O_ID
		fireBoth={} # E_Name -> boolean
		lastPoint={}
		resultList=[]
		#con = MySQLdb.connect(setting.CNS_DB_IP_ADDRESS, setting.CNS_DB_USERNAME, setting.CNS_DB_PASSWORD, setting.CNS_DB_NAME)
		con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()

		#cur.execute("SELECT O_ID, ifIndex, E_Name FROM Equipment_Detail JOIN Equipment ON Equipment_Detail.E_ID=Equipment.E_ID JOIN Division ON Equipment.D_ID=Division.D_ID WHERE D_Name LIKE '%IDC%'")
		cur.execute("SELECT O_ID, ifIndex, E_Name, Speed, matched_O_ID FROM port             JOIN node      ON             port.E_ID=     node.E_ID JOIN division ON      node.D_ID=division.D_ID WHERE D_Name LIKE '%IDC%'")

		while True:
			row=cur.fetchone()
			if row is not None:
				O_ID=row[0]
				ifIndex=row[1]
				E_Name=row[2]
				if E_Name not in mapping:
					mapping[E_Name]={}

				mapping[E_Name][ifIndex]=O_ID
				
				speed[O_ID]=int(row[3])
				matched[O_ID]=row[4]
				
				lastPoint[O_ID]={}
				lastPoint[O_ID]['ifHCInOctets']={'timestamp': -1,'value':'NULL', 'bitRate':-1, 'mark':'?', 'incidentID':-1}
				lastPoint[O_ID]['ifHCOutOctets']={'timestamp': -1,'value':'NULL', 'bitRate':-1, 'mark':'?', 'incidentID':-1}

			else:
				break

		con.close()
		
		print "finish mapping"

		resultList=[]

		#fill supportHC by real walk
		for E_Name in mapping:
			command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s ifHCInOctets"%(E_Name)
			result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
			resultList.append({'E_Name':E_Name,'result':result})
		
		for element in resultList:
			E_Name=element['E_Name']
			result=element['result']
			result.wait()
			
			for ifIndex in mapping[E_Name]:
				O_ID=mapping[E_Name][ifIndex]
				supportHC[O_ID]=False

			if result.returncode!=0:
				#cannot connect with target
				#just use HC for all
				for ifIndex in mapping[E_Name]:
					O_ID=mapping[E_Name][ifIndex]
					supportHC[O_ID]=True
				
				fireBoth[E_Name]=False

			elif result.returncode==0:	
				#can connect with target
				output=result.communicate()[0]
				output=output.split('\n')[0:-1]
				HC_Count=0
				for line in output:
					temp=line.split('.')[1].split(' ')
					ifIndex=int(temp[0])
					if ifIndex in mapping[E_Name]:
						O_ID=mapping[E_Name][ifIndex]
						supportHC[O_ID]=True
						HC_Count+=1
				
				if HC_Count<len(mapping[E_Name]):
					fireBoth[E_Name]=True
				else:
					fireBoth[E_Name]=False
		
		resultList=[]
		
		#finish checking supportHC

		#calculation round
		while True:
			#print "start a calculation round"
			#totalWait=0.0
			#startTime=time.time()

			#fire snmpwalk commands 
			for E_Name in mapping:
				for specific in ['ifHCInOctets','ifHCOutOctets']:
					command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s %s"%(E_Name,specific)
					result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
					resultList.append({'E_Name':E_Name,'specific':specific,'timestamp':int(time.time()),'result':result})

					if fireBoth[E_Name]:
						command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s %s"%(E_Name, specific.replace('HC',''))
						result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
						resultList[-1]['result2']=result
			
			waitList=[]
			for element in resultList:
				E_Name=element['E_Name']
				specific=element['specific']
				timestamp=element['timestamp']
				
				#clear mark (for one element)
				for ifIndex in mapping[E_Name]:
					lastPoint[mapping[E_Name][ifIndex]][specific]['mark']='?'

				#get result from HC (64bit) first and then 32bit
				
				for r in [1,2]:
					
					if r==2 and fireBoth[E_Name]==False:
						break

					if r==1:
						result=element['result']	#first round
					elif r==2:
						result=element['result2']
					
					result.wait()
					output=result.communicate()[0]
					output=output.split('\n')[0:-1]

					for line in output:
						temp=line.split('.')[1].split(' ')
						ifIndex=int(temp[0])
						
						if ifIndex in mapping[E_Name]:
							if r==1 or (r==2 and supportHC[mapping[E_Name][ifIndex]]==False):
								val=int(temp[3])
								O_ID=mapping[E_Name][ifIndex]
								
								# 2 cases here for obvious value

								#1 Keep initial value (nothing to do with database)
								if lastPoint[O_ID][specific]['value']=='NULL':
									lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val, 'bitRate':-1, 'mark':'pass', 'incidentID':lastPoint[O_ID][specific]['incidentID']}
								
								#2 Normal case
								elif lastPoint[O_ID][specific]['value']!='NULL':
									byteDiff=(val-lastPoint[O_ID][specific]['value'])	
									if byteDiff<0:
										if r==1:
											byteDiff+=18446744073709551616  #2^64
										elif r==2:
											byteDiff+=4294967296			#2^32

									bitRate=int(byteDiff*8/(timestamp-lastPoint[O_ID][specific]['timestamp']))
									
									if speed[O_ID]>0:
										#check new incident
										lastPercent=float(lastPoint[O_ID][specific]['bitRate'])*100/float(speed[O_ID]*1000)
										newPercent=float(bitRate)*100/float(speed[O_ID]*1000)
										
										if lastPoint[O_ID][specific]['incidentID']==-1:
											
											if lastPercent<80 and newPercent>=80:
												#put new incident to db
												con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
												cur = con.cursor()
												cur.execute("INSERT INTO incident (incident_type, timestamp_start, subject, detail) VALUES (%s,%s,'%s','%s');"%(str(1),str(timestamp),'Exceed 80%','Testing'))
												incidentID = con.insert_id()
												
												valueString=''
												for oid in [O_ID]:
													valueString+= " (%s,%s),"%(str(incidentID),str(oid))
												valueString=valueString[0:-1]+';'
												cur.execute("INSERT INTO incident_port (incidentID, O_ID) VALUES "+valueString)

												con.close()
												nextIncidentID=incidentID
											
											else:
												nextIncidentID=lastPoint[O_ID][specific]['incidentID']
											
										else:
											
											if newPercent < 80:
												#auto acknowledge
												incidentID=lastPoint[O_ID][specific]['incidentID']

												con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
												cur = con.cursor()
												cur.execute("UPDATE incident SET status=1, timestamp_end=%s WHERE incidentID=%s AND status=0 ;"%(str(timestamp),str(incidentID)))
												#affectedRow=cur.rowcount
												con.close()

												nextIncidentID=-1
											
											else:
												nextIncidentID=lastPoint[O_ID][specific]['incidentID']
									
									else:
										#speed==0
										nextIncidentID=lastPoint[O_ID][specific]['incidentID']

									lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val, 'bitRate':bitRate, 'mark':[O_ID,timestamp,specific[4],bitRate], 'incidentID':nextIncidentID}
								

				"""
				if fireBoth[E_Name]:
					#get result from result2
					result=element['result2']
					result.wait()
					output=result.communicate()[0]
					output=output.split('\n')[0:-1]

					for line in output:
						temp=line.split('.')[1].split(' ')
						ifIndex=int(temp[0])
						
						if ifIndex in mapping[E_Name] and supportHC[mapping[E_Name][ifIndex]]==False:
							val=int(temp[3])
							O_ID=mapping[E_Name][ifIndex]
							
							# 2 cases here for obvious value

							#1 Keep initial value (nothing to do with database)
							if lastPoint[O_ID][specific]['value']=='NULL':
								lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val, 'bitRate':-1, 'mark':'pass', 'incidentID':-1}
							
							#2 Normal case
							elif lastPoint[O_ID][specific]['value']!='NULL':
								byteDiff=(val-lastPoint[O_ID][specific]['value'])	
								if byteDiff<0:
									byteDiff+=4294967296  #2^32
								bitRate=int(byteDiff*8/(timestamp-lastPoint[O_ID][specific]['timestamp']))
								lastPoint[O_ID][specific]={'timestamp': timestamp,'value':val, 'bitRate':bitRate, 'mark':[O_ID,timestamp,specific[4],bitRate]}
				"""

				#clear '?' mark
				for ifIndex in mapping[E_Name]:
					O_ID=mapping[E_Name][ifIndex]
					
					if lastPoint[O_ID][specific]['mark']=='?':
						# 2 cases here
						
						#3 Nothing to do (Nothing is changed from the last time)
						if lastPoint[O_ID][specific]['value']=='NULL':
							lastPoint[O_ID][specific]['mark']='pass'
						
						#4 Down
						else:
							lastPoint[O_ID][specific]={'timestamp': timestamp, 'value':'NULL', 'bitRate':-1, 'mark':[O_ID,timestamp,specific[4],'NULL'], 'incidentID':lastPoint[O_ID][specific]['incidentID']}
				
				#push data to DB
				for ifIndex in mapping[E_Name]:
					O_ID=mapping[E_Name][ifIndex]
					
					if lastPoint[O_ID][specific]['mark']!='pass':
						waitList.append(lastPoint[O_ID][specific]['mark'])
						if len(waitList)>=300:
							#push these info to database
							submit_list(waitList)
							waitList=[]
			
			if len(waitList)>0:	#last query for the rest of data in this round
				#push these info to database
				submit_list(waitList)
				waitList=[]

			resultList=[]
			#finishTime=time.time()
			#print "timeUsage(in seconds)", int(finishTime-startTime)
			#print "waitUsage(in seconds)", int(totalWait)
			
			#delete old info
			delete_old_log()
			
			time.sleep(60)