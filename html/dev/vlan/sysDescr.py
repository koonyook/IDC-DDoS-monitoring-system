import time
import subprocess,shlex
import MySQLdb

answer=[]

con = MySQLdb.connect("?.?.?.?", "?", "?", "NetTracker")
cur = con.cursor()

cur.execute("SELECT E_ID, E_Name FROM node")

while True:
	row=cur.fetchone()
	if row is not None:
		command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN %s sysDescr"%(row[1])
		result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
		result.wait()
		output=result.communicate()[0]
		sysDescr=output.replace('SNMPv2-MIB::sysDescr.0 = STRING: ','')
		if sysDescr.startswith('Cisco'):
			tmp=sysDescr.replace('(tm)','')
			begin=tmp.find('(')+1;
			end=tmp.find(')');
			brand='Cisco'
			model=tmp[begin:end]
		elif sysDescr.startswith('H3C'):
			lines=sysDescr.split('\n')
			i=0
			while i<len(lines):
				if 'Release' in lines[i]:
					break
				i+=1
			i+=1
			tmp=lines[i].split(' ')
			if tmp[0]!='H3C':
				model=tmp[0].strip()
			else:
				model=tmp[1].strip()
			brand='H3C'
		elif sysDescr.startswith('Hitachi'):
			tmp=sysDescr.split(' ')
			i=0
			for i in range(len(tmp)):
				if tmp[i]=='Switch':
					break
			i+=1
			model=tmp[i].strip()
			brand='Hitachi'
		elif sysDescr.startswith('HP'):
			lines=sysDescr.split('\n')
			i=0
			while i<len(lines):
				if 'Release' in lines[i]:
					break
				i+=1
			i+=1
			tmp=lines[i].split(' ')
			if tmp[0]!='HP':
				model=' '.join(tmp[0:]).strip()
			else:
				model=' '.join(tmp[1:]).strip()
			brand='HP'
		elif sysDescr.startswith('Huawei'):
			lines=sysDescr.split('\n')
			i=0
			while i<len(lines):
				if 'Release' in lines[i]:
					break
				i+=1
			i+=1
			tmp=lines[i].split(' ')
			model=' '.join(tmp[0:2]).strip()
			brand='Huawei'
		answer.append([row[0],sysDescr,brand,model])
		print '.'
	else:
		break

for element in answer:
	cur.execute("UPDATE node SET sysDescr='%s', brand='%s', model='%s' WHERE E_ID=%s"%(element[1],element[2],element[3],str(element[0])))

con.close()
