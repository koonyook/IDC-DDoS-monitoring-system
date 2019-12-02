import time
import subprocess,shlex
import MySQLdb

tobi = {
'0':'0000',
'1':'0001',
'2':'0010',
'3':'0011',
'4':'0100',
'5':'0101',
'6':'0110',
'7':'0111',
'8':'1000',
'9':'1001',
'A':'1010',
'B':'1011',
'C':'1100',
'D':'1101',
'E':'1110',
'F':'1111'
}

swap = {
'0':'0',
'1':'8',
'2':'4',
'3':'C',
'4':'2',
'5':'A',
'6':'6',
'7':'E',
'8':'1',
'9':'9',
'A':'5',
'B':'D',
'C':'3',
'D':'B',
'E':'7',
'F':'F'
}

answer={}

con = MySQLdb.connect("?.?.?.?", "?", "?", "NetTracker")
cur = con.cursor()

cur.execute("SELECT E_ID, E_Name, brand, model FROM node WHERE name='das-cbwci01'")

while True:
	row=cur.fetchone()
	if row is not None:
		E_ID, E_Name, brand, model = row
		print E_Name,brand,model
		
		answer[E_ID]={}

		#first gathering
		if brand=='Cisco':
			mib="1.3.6.1.4.1.9.9.68.1.2.2.1.2"
		else:
			mib="1.3.6.1.2.1.17.7.1.4.5.1.1"
		
		command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s %s"%(E_Name,mib)
		result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
		result.wait()
		print "1st checkpoint"
		output=result.communicate()[0]
		for line in output.split('\n')[0:-1]:
			tmp=line.split(' ')
			ifIndex=int(tmp[0].split('.')[-1])
			vlan=int(tmp[-1])
			answer[E_ID][ifIndex]=[vlan,]
		
		#second gathering
		if brand=='Cisco':
			command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s 1.3.6.1.4.1.9.9.46.1.6.1.1.11"%(E_Name)
			result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
			result.wait()
			output=result.communicate()[0]
			output=output.split('\n')[0:-1]
			i=0
			while i<len(output):
				if '=' in output[i]:
					if '""' in output[i]:
						pass
					else:
						#this is the first line of a data set
						ifIndex=int(output[i].split(' ')[0].split('.')[-1])
						startPoint=output[i].find('Hex-STRING:')+12
						gatherHex = ''.join(output[i][startPoint:].split(' '))
						i+=1
						while i<len(output) and '=' not in output[i] :
							gatherHex+=''.join(output[i].split(' '))
							i+=1
						i-=1
						
						if ifIndex not in answer[E_ID]:
							answer[E_ID][ifIndex]=[]

						#calculate hex string
						currentVlan=0
						for ch in gatherHex:
							bi=tobi[ch]
							for j in [0,1,2,3]:
								if bi[j]=='1' and currentVlan+j not in answer[E_ID][ifIndex]:
									answer[E_ID][ifIndex].append(currentVlan+j)
							currentVlan+=4

				i+=1

		else:
			# non-Cisco

			#need number mapping to ifIndex
			command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s 1.3.6.1.2.1.17.1.4.1.2"%(E_Name)
			result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
			result.wait()
			print "2nd checkpoint"
			output=result.communicate()[0]
			output=output.split('\n')[0:-1]
			i=0
			tmpConvert={}	# number -> ifIndex
			while i<len(output):
				tmp=output[i].split(' ')
				ifIndex=int(tmp[-1])
				ifNumber=int(tmp[0].split('.')[-1])
				tmpConvert[ifNumber]=ifIndex

				i+=1

			command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s 1.3.6.1.2.1.17.7.1.4.3.1.2"%(E_Name)
			result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
			result.wait()
			print "3rd checkpoint"
			if result.returncode!=0:
				#can go on this mib
				output=result.communicate()[0]
				output=output.split('\n')[0:-1]
				i=0
				while i<len(output):
					if '=' in output[i]:
						if '""' in output[i]:
							pass
						else:
							#this is the first line of a data set
							vlan=int(output[i].split(' ')[0].split('.')[-1])
							startPoint=output[i].find('Hex-STRING:')+12
							gatherHex = ''.join(output[i][startPoint:].split(' '))
							i+=1
							while i<len(output) and '=' not in output[i] :
								gatherHex+=''.join(output[i].split(' '))
								i+=1
							i-=1
							
							if model=='S5100-24P-SI' or model=='S3600-28TP-SI':
								#swap all pair of number
								newHex=''
								for j in range(len(gatherHex)/2):
									newHex+=swap[gatherHex[j*2+1]]+swap[gatherHex[j*2]]
								gatherHex=newHex
							

							#calculate hex string
							currentIfNumber=1
							for ch in gatherHex:
								if ch not in tobi:
									print "here:",ch
								bi=tobi[ch]
								for j in [0,1,2,3]:
									if bi[j]=='1':
										ifIndex=tmpConvert[currentIfNumber+j]
										if ifIndex not in answer[E_ID]:
											answer[E_ID][ifIndex]=[]
										if vlan not in answer[E_ID][ifIndex]:
											answer[E_ID][ifIndex].append(vlan)

								currentIfNumber+=4

				i+=1
		
		print "finish"
		
	else:
		break

cur.execute("DELETE FROM vlan_port WHERE 1=1")

for E_ID in answer:
	for ifIndex in answer[E_ID]:
		if len(answer[E_ID][ifIndex])>0:
			cur.execute("SELECT O_ID FROM port WHERE E_ID=%s AND Ifindex=%s")
			if cur.rowcount==1:
				O_ID=cur.fetchone()[0]
				valueString=''
				for vlan in answer[E_ID][ifIndex]:
					valueString+="(%s,%s), "%(str(O_ID),str(vlan))

				cur.execute("INSERT INTO vlan_port (O_ID, vlanNumber) VALUES %s"%(valueString))

con.close()
