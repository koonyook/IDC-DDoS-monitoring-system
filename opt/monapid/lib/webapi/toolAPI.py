import setting
import MySQLdb as mdb
import MySQLdb
import subprocess, shlex
import time
import json
from util import general
from util import shortcut
import cherrypy


class UpdateFromCNSMON(object):
	'''
	update node and port from cnsmon
	'''
	def index(self):
		
		sourceDBIP=setting.CNS_DB_IP_ADDRESS
		sourceDBUser=setting.CNS_DB_USERNAME
		sourceDBPass=setting.CNS_DB_PASSWORD
		sourceDBName=setting.CNS_DB_NAME
		
		destDBIP=setting.MAIN_DB_IP_ADDRESS
		destDBUser=setting.MAIN_DB_USERNAME
		destDBPass=setting.MAIN_DB_PASSWORD
		destDBName=setting.MAIN_DB_NAME
		
		topologyDBIP=setting.CMDB_IP_ADDRESS
		topologyDBUser=setting.CMDB_USERNAME
		topologyDBPass=setting.CMDB_PASSWORD
		topologyDBName=setting.CMDB_NAME

		#1 create new table
		con = mdb.connect(destDBIP, destDBUser, destDBPass, destDBName)
		cur = con.cursor()

		con2 = mdb.connect(destDBIP, destDBUser, destDBPass, destDBName)
		cur2=con2.cursor()

		con3 = mdb.connect(destDBIP, destDBUser, destDBPass, destDBName)
		cur3=con3.cursor()

		conf = mdb.connect(sourceDBIP, sourceDBUser, sourceDBPass, sourceDBName)
		curf=conf.cursor()

		cont = mdb.connect(topologyDBIP, topologyDBUser, topologyDBPass, topologyDBName)
		curt=cont.cursor()

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `division` (
		  `D_ID` smallint(5) NOT NULL AUTO_INCREMENT,
		  `D_Name` varchar(50) DEFAULT NULL,

		  PRIMARY KEY (`D_ID`)
		) ENGINE=MyISAM  DEFAULT CHARSET=latin1
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `node` (
		  `E_ID` smallint(5) NOT NULL AUTO_INCREMENT,
		  `D_ID` smallint(5) DEFAULT NULL,
		  `E_Name` varchar(50) DEFAULT NULL,
		  `name` varchar(50) NOT NULL DEFAULT '',
		  `level` tinyint(4) DEFAULT 0,
		  `sysDescr` text NOT NULL,
		  `brand` varchar(15) NOT NULL DEFAULT '',
		  `model` varchar(50) NOT NULL DEFAULT '',

		  PRIMARY KEY (`E_ID`)
		) ENGINE=MyISAM  DEFAULT CHARSET=latin1
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `port` (
		  `O_ID` smallint(10) NOT NULL AUTO_INCREMENT,
		  `E_ID` smallint(5) DEFAULT NULL,
		  `deleted` smallint(6) DEFAULT NULL,
		  `isChannel` tinyint(4) DEFAULT NULL,
		  `level` tinyint(4) DEFAULT 0,
		  `inFilter` tinyint(4) DEFAULT 0,
		  `Interface` varchar(50) DEFAULT NULL,
		  `Ifindex` int(10) DEFAULT NULL,
		  `Speed` varchar(10) NOT NULL,
		  `ifAlias` text,
		  `source` varchar(50) NOT NULL DEFAULT '',
		  `target` varchar(50) NOT NULL DEFAULT '',
		  `targetInterface` varchar(50) NOT NULL DEFAULT '',
		  `target_E_ID` smallint(6) DEFAULT NULL,
		  `matched_O_ID` smallint(6) DEFAULT NULL,
		  `candidateLink` smallint(6) DEFAULT NULL,
		  `restLink` smallint(6) DEFAULT NULL,
		  PRIMARY KEY (`O_ID`)
		) ENGINE=MyISAM  DEFAULT CHARSET=latin1;
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `log` (
		  `O_ID` smallint(6) NOT NULL,
		  `attribute` char(1) NOT NULL COMMENT '''I'' = In, ''O'' = Out',
		  `timestamp` int(10) unsigned NOT NULL,
		  `value` bigint(10) unsigned DEFAULT NULL COMMENT 'bit per sec',
		  PRIMARY KEY (`O_ID`,`timestamp`,`attribute`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620;
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `lastLog` (
		  `O_ID` smallint(6) NOT NULL,
		  `attribute` char(1) NOT NULL COMMENT '''I'' = In, ''O'' = Out',
		  `timestamp` int(10) unsigned NOT NULL,
		  `value` bigint(10) unsigned DEFAULT NULL COMMENT 'bit per sec',
		  PRIMARY KEY (`O_ID`,`attribute`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620;
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `incident` (
		  `incidentID` int(10) unsigned NOT NULL AUTO_INCREMENT,
		  `incident_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0=Unknown',
		  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0=Not Ended, 1=Auto Ended, 2=Acked',
		  `timestamp_start` int(10) unsigned NOT NULL,
		  `timestamp_end` int(10) unsigned DEFAULT NULL,
		  `subject` text NOT NULL,
		  `detail` text NOT NULL,
		  PRIMARY KEY (`incidentID`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620 AUTO_INCREMENT=1 ;
		""")

		cur.execute("""
		CREATE TABLE IF NOT EXISTS `incident_port` (
		  `incidentID` int(10) unsigned NOT NULL,
		  `O_ID` smallint(6) NOT NULL,
		  PRIMARY KEY (`incidentID`,`O_ID`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620 COMMENT='One incident can involve no port or many ports';
		""")
		
		cur.execute("""
		CREATE TABLE IF NOT EXISTS `vlan_port` (
		  `vlanNumber` smallint(6) NOT NULL,
		  `O_ID` smallint(6) NOT NULL,
		  PRIMARY KEY (`vlanNumber`,`O_ID`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620;
		""")
		
		cur.execute("""
		CREATE TABLE IF NOT EXISTS `flowLog` (
		  `timestamp` int(10) unsigned NOT NULL,
		  `ip` varchar(15) NOT NULL,
		  `flow` int(10) unsigned NOT NULL,
		  `packet` int(10) unsigned NOT NULL,
		  `size` int(10) unsigned NOT NULL COMMENT 'KB',
		  PRIMARY KEY (`timestamp`,`ip`)
		) ENGINE=MyISAM DEFAULT CHARSET=tis620;
		""")

		print "8 tables were created"

		#1.2 clear division, node port
		cur.execute("DELETE FROM division WHERE 1=1")
		cur.execute("DELETE FROM node WHERE 1=1")
		cur.execute("DELETE FROM port WHERE 1=1")

		print "3 tables have been clear"

		#2.1 move Division to division
		curf.execute("SELECT D_ID, D_Name from Division")
		for i in range(curf.rowcount):
			did,dname=curf.fetchone()
				
			cur.execute("INSERT INTO division (D_ID, D_Name) VALUES (%s,'%s');"%(str(did),dname))


		#2.2 move data to node table
		curf.execute("SELECT E_ID, Equipment.D_ID, E_Name from Equipment JOIN Division ON Equipment.D_ID=Division.D_ID WHERE D_Name LIKE '%IDC%'")
		for i in range(curf.rowcount):
			eid,did,ename=curf.fetchone()
			
			ename=ename.lower()

			if ename.endswith('.csloxinfo.net'):
					newName=ename.split('.')[0]
			else:
				newName=ename
				
			cur.execute("INSERT INTO node (E_ID, D_ID, E_Name, name) VALUES (%s, %s,'%s','%s');"%(str(eid),str(did),ename,newName))

		#3 move data to port table
		curf.execute("SELECT O_ID, Equipment_Detail.E_ID, Interface, Ifindex, Speed, ifAlias FROM Equipment_Detail JOIN Equipment ON Equipment_Detail.E_ID=Equipment.E_ID JOIN Division ON Equipment.D_ID=Division.D_ID WHERE D_Name LIKE '%IDC%'")
		for i in range(curf.rowcount):
			oid,eid,interface,ifindex,speed,ifalias=curf.fetchone()
			cur.execute("INSERT INTO port (O_ID, E_ID, Interface, Ifindex, Speed, ifAlias) VALUES (%s,%s,'%s',%s,%s,'%s');"%(str(oid),str(eid),interface,str(ifindex),str(speed),ifalias))

		conf.close()	#no more connection to this database

		print "init data were moved"

		#4 classify port type
		cur.execute("UPDATE port SET isChannel=0 WHERE 1=1")
		cur.execute("UPDATE port SET isChannel=1 WHERE interface LIKE 'Bridge-Aggregation%' OR interface LIKE 'Port-channel%'")

		print "isChannel has been set"


		#5 source
		cur.execute("SELECT E_ID, name FROM node")

		for i in range(cur.rowcount):        
			eid,ename = cur.fetchone()
			cur2.execute("UPDATE port SET source='"+ename+"' WHERE E_ID="+str(eid))
			print ' ',i,'/',cur.rowcount,'          \r',

		print "source column added"

		#6 match from CMDB Relation (correct data)
		correctCounter=0
		curt.execute("SELECT source_ip, interface, device_id, portid FROM relation")
		for i in range(curt.rowcount):
			sourceName,sourcePort,destName,destPort=curt.fetchone()
			#change everything to my format

			#sourceName (short and low-capital format)
			sourceName=sourceName.lower()
			if sourceName.endswith('.csloxinfo.net'):
				sourceName=sourceName.split('.')[0]
			
			#sourcePort
			sourcePort=sourcePort.replace(',','')
			if sourcePort.startswith('PO'):
				sourcePort={'type':'channel', 'number':sourcePort.split('/')[0].replace('PO',''), 'name':sourcePort.split('/')[0].replace('PO','Port-channel') } #name for debugging
			elif sourcePort.startswith('Fa'):
				sourcePort={'type':'Fa', 'number':sourcePort.replace('Fa',''), 'name': sourcePort.replace('Fa','FastEthernet')}
			elif sourcePort.startswith('Gi'):
				sourcePort={'type':'Gi', 'number':sourcePort.replace('Gi',''), 'name': sourcePort.replace('Gi','GigabitEthernet') }
			elif sourcePort.startswith('Te'):
				sourcePort={'type':'Te', 'number':sourcePort.replace('Te',''), 'name': sourcePort.replace('Te','TenGigabitEthernet') }
			else:
				sourcePort={'type':'else', 'name':sourcePort}
			
			#destName
			destName=destName.lower()
			if destName.endswith('.csloxinfo.net'):
				destName=destName.split('.')[0]
			
			#destPort
			if destPort.startswith('POS'):
				destPort={'type':'channel', 'number':destPort.split('/')[0].replace('POS',''), 'name':destPort.split('/')[0].replace('POS','Port-channel') } #name for debugging
			elif destPort.startswith('FastEthernet'):
				destPort={'type':'Fa', 'number':destPort.replace('FastEthernet',''), 'name':destPort }
			elif destPort.startswith('GigabitEthernet'):
				destPort={'type':'Gi', 'number':destPort.replace('GigabitEthernet',''), 'name':destPort }
			elif destPort.startswith('TenGigabitEthernet'):
				destPort={'type':'Te', 'number':destPort.replace('TenGigabitEthernet',''), 'name':destPort }
			else:
				destPort={'type':'else' , 'name' :destPort}
			
			#find source
			if sourcePort['type']=='channel':
				portOption="(Interface='%s' or Interface='%s')"%("Port-channel"+sourcePort['number'],"Bridge-Aggregation"+sourcePort['number'])
			else:
				portOption="Interface='%s' "%(sourcePort['name'])

			cur.execute("SELECT O_ID FROM port WHERE matched_O_ID IS NULL and source='%s' and %s "%(sourceName,portOption))
			if cur.rowcount==1:
				sourceOID=cur.fetchone()[0]
				#find destination oid
				if destPort['type']=='channel':
					portOption="(Interface='%s' or Interface='%s')"%("Port-channel"+destPort['number'],"Bridge-Aggregation"+destPort['number'])
				else:
					portOption="Interface='%s' "%(destPort['name'])
				
				cur.execute("SELECT O_ID FROM port WHERE matched_O_ID IS NULL and source='%s' and %s "%(destName,portOption))
				if cur.rowcount==1:
					destOID=cur.fetchone()[0]
					#full update to both ports
					cur.execute("UPDATE port SET target='%s', targetInterface='%s', matched_O_ID=%s  WHERE O_ID=%s"%(destName,destPort['name'],str(destOID),str(sourceOID)))
					cur.execute("UPDATE port SET target='%s', targetInterface='%s', matched_O_ID=%s  WHERE O_ID=%s"%(sourceName,sourcePort['name'],str(sourceOID),str(destOID)))
					correctCounter+=1
				else:
					#update only destination to source port (surely unmatch)
					cur.execute("UPDATE port SET target='%s', targetInterface='%s', matched_O_ID=0 WHERE O_ID=%s"%(destName,destPort['name'],str(sourceOID)))

			else:
				continue

		cont.close()
		print "finish relation from cmdb, pair count =",correctCounter

		#7.1 identify internal target
		cur.execute("SELECT E_ID, name FROM node")
		#print cur.rowcount

		for i in range(cur.rowcount):        
			eid,ename = cur.fetchone()
			
			cur2.execute("SELECT O_ID, target FROM port WHERE target='' and ifAlias LIKE '%"+ename+"%'")
			for j in range(cur2.rowcount):
				oid,target=cur2.fetchone()
				
				if target in ename:	#target is substring of ename
					cur3.execute("UPDATE port SET target='"+ename+"' WHERE O_ID="+str(oid))
				else:
					pass
			print ' ',i,'/',cur.rowcount,'          \r',

		print "internal target, OK"

		#7.2 identify external target
		afile=open(setting.MAIN_PATH+"externalNodeList.txt","r")
		while True:
			ename=afile.readline().strip()
			if ename=='':
				break
			else:
				cur2.execute("SELECT O_ID, target FROM port WHERE target='' and ifAlias LIKE '%"+ename+"%'")
				for j in range(cur2.rowcount):
					oid,target=cur2.fetchone()
					
					if target in ename:	#target is substring of ename
						cur3.execute("UPDATE port SET target='"+ename+"' WHERE O_ID="+str(oid))
					else:
						pass

		afile.close()
		print "external target, OK"

		#7.3 identify void target
		afile=open(setting.MAIN_PATH+"voidNodeList.txt","r")
		while True:
			ename=afile.readline().strip()
			if ename=='':
				break
			else:
				cur2.execute("SELECT O_ID, target FROM port WHERE target='' and ifAlias LIKE '%"+ename+"%'")
				for j in range(cur2.rowcount):
					oid,target=cur2.fetchone()
					
					if target in ename:	#target is substring of ename
						cur3.execute("UPDATE port SET target='obsolete' WHERE O_ID="+str(oid))
					else:
						pass

		afile.close()
		print "void target, OK"

		#8 identify target_E_ID
		cur.execute("SELECT O_ID, target FROM port WHERE target!='' and target!='obsolete' ")
		#print cur.rowcount

		for i in range(cur.rowcount):        
			oid,targetName = cur.fetchone()
			
			cur2.execute("SELECT E_ID FROM node WHERE name='%s'"%(targetName))
			if cur2.rowcount==1:
				targetEID=cur2.fetchone()[0]
				cur3.execute("UPDATE port SET target_E_ID=%s WHERE O_ID=%s"%(str(targetEID),str(oid)))

		print "target_E_ID, OK"

		#9 calculate candidateLink
		cur.execute("SELECT O_ID, E_ID, target_E_ID, isChannel FROM port WHERE target_E_ID IS NOT NULL")

		for i in range(cur.rowcount):        
			row = cur.fetchone()
			sourceOID= row[0]
			sourceEID=row[1]
			targetEID=row[2]
			isChannel=row[3]

			cur2.execute("SELECT O_ID, E_ID FROM port WHERE E_ID=%s and target_E_ID=%s and isChannel=%s"%(str(targetEID),str(sourceEID),str(isChannel)))

			cur3.execute("UPDATE port SET candidateLink=%s WHERE O_ID=%s"%(str(cur2.rowcount),str(sourceOID)))
			
			print ' ',i,'/',cur.rowcount,'          \r',

		print "candidateLink, OK"

		#10.1 match O_ID
		while True:
			counter=0
			cur.execute("SELECT O_ID, E_ID, target_E_ID, Interface, isChannel FROM port WHERE candidateLink>0 and matched_O_ID IS NULL")
			#print cur.rowcount

			for i in range(cur.rowcount):        
				row = cur.fetchone()
				sourceOID= row[0]
				sourceEID=row[1]
				targetEID=row[2]
				ifName=row[3]
				isChannel=row[4]
				
				#extract possible substrings
				signature=[]
				for aif in ifName.split(','):

					if "Ethernet" in aif:
						aif=aif.split("Ethernet")[1]
						aif=aif.split(".")[0]
						signature.append(aif)
						if aif.count('/')==2:
							signature.append(aif[2:])
					
					elif aif.startswith('ge'):
						aif=aif.replace('ge-','')
						signature.append(aif)
						if aif.count('/')==2:
							signature.append(aif[2:])
					
					elif aif.startswith('Apresia13200-48X-PSR-'):
						aif=aif.replace('Apresia13200-48X-PSR-','')
						continue

					elif aif.startswith("Port-channel"):
						signature.append('po'+aif[12:])
						signature.append('channel'+aif[12:])
						signature.append('channel '+aif[12:])
						signature.append('group'+aif[12:])
						signature.append('group '+aif[12:])
						signature.append('')
					
					elif aif.startswith("Bridge-Aggregation"):
						signature.append('po'+aif[18:])
						signature.append('channel'+aif[18:])
						signature.append('channel '+aif[18:])
						signature.append('group'+aif[18:])
						signature.append('group '+aif[18:])
						signature.append('')

					else:
						continue
				
				#execute each sub string and count (1 -> ok -> stop)
				for asig in signature:
					cur2.execute("SELECT O_ID FROM port WHERE matched_O_ID IS NULL and E_ID=%s and target_E_ID=%s and ifAlias LIKE '%%%s%%' and isChannel=%s"%(str(targetEID),str(sourceEID),asig,str(isChannel)))

					if cur2.rowcount==1:
						counter+=1
						#last target
						targetOID=cur2.fetchone()[0]
						cur3.execute("UPDATE port SET matched_O_ID=%s WHERE O_ID=%s"%(str(targetOID),str(sourceOID)))
						cur3.execute("UPDATE port SET matched_O_ID=%s WHERE O_ID=%s"%(str(sourceOID),str(targetOID)))
						break
				
				print ' ',i,'/',cur.rowcount,'          \r',
				
			if counter==0:
				print "end of matching"
				break
			else:
				print "counter",counter,'       '

		#10.2 update restLink
		cur.execute("SELECT O_ID, E_ID, target_E_ID, isChannel FROM port WHERE target_E_ID IS NOT NULL")
		#print cur.rowcount

		for i in range(cur.rowcount):        
			row = cur.fetchone()
			sourceOID= row[0]
			sourceEID=row[1]
			targetEID=row[2]
			isChannel=row[3]

			cur2.execute("SELECT O_ID, E_ID FROM port WHERE matched_O_ID IS NULL and E_ID=%s and target_E_ID=%s and isChannel=%s"%(str(targetEID),str(sourceEID),str(isChannel)))
			cur3.execute("UPDATE port SET restLink=%s WHERE O_ID=%s"%(str(cur2.rowcount),str(sourceOID)))
			print ' ',i,'/',cur.rowcount,'          \r',

		print "restLink, OK"

		#11 reserve port without matching
		cur.execute("UPDATE port SET matched_O_ID=0 WHERE matched_O_ID IS NULL and (ifAlias LIKE '%reserve%' or ifAlias LIKE '%no_use%' )")
		print "reserve, OK"

		#12 determine level and inFilter 
		print "determine level and inFilter"
		#clear all level
		cur.execute("UPDATE node SET level=0 WHERE 1")
		cur.execute("UPDATE port SET level=0, inFilter=0 WHERE 1")
		#12.1 determine node level
		#access node = 1
		cur.execute("UPDATE node SET level=1 WHERE name LIKE 'das%' OR name LIKE 'dps%' OR name LIKE 'dfs%' OR name LIKE 'dos%' ")
		#distribute node =2
		cur.execute("UPDATE node SET level=2 WHERE name LIKE 'dds%' ")
		cur.execute("SELECT E_ID FROM node WHERE name LIKE 'cos%' ")
		for i in range(cur.rowcount):
			row=cur.fetchone()
			eid=row[0]
			cur2.execute("SELECT O_ID FROM port JOIN node ON port.target_E_ID=node.E_ID WHERE port.E_ID=%s AND node.level=1"%(str(eid)))
			if cur2.rowcount>0:
				cur3.execute("UPDATE node SET level=2 WHERE E_ID=%s"%(str(eid)))
		#core node = 3
		cur.execute("UPDATE node SET level=3 WHERE name LIKE 'cor%' ")
		cur.execute("SELECT E_ID FROM node WHERE level=0 AND name LIKE 'cos%'")
		for i in range(cur.rowcount):
			row=cur.fetchone()
			eid=row[0]
			cur2.execute("SELECT O_ID FROM port JOIN node ON port.target_E_ID=node.E_ID WHERE port.E_ID=%s AND node.level=3"%(str(eid)))
			if cur2.rowcount>0:
				cur3.execute("UPDATE node SET level=3 WHERE E_ID=%s"%(str(eid)))
		#12.2 determine port level (follow core)
		cur.execute("SELECT E_ID, level FROM node WHERE level!=0")
		for i in range(cur.rowcount):
			row=cur.fetchone()
			eid=row[0]
			level=row[1]
			cur2.execute("UPDATE port SET level=%s WHERE E_ID=%s"%(str(level),str(eid)))
		#12.3 deternine port inFilter
		#access level
		cur.execute("UPDATE port SET inFilter=1 WHERE level=1 AND target_E_ID IS NULL")
		#distribute level
		cur.execute("SELECT O_ID FROM port WHERE level=2")
		for i in range(cur.rowcount):
			row=cur.fetchone()
			oid=row[0]
			cur2.execute("SELECT O_ID FROM port JOIN node ON port.target_E_ID=node.E_ID WHERE port.O_ID=%s AND node.level=1"%(str(oid)))
			if cur2.rowcount>0:
				cur3.execute("UPDATE port SET inFilter=1 WHERE O_ID=%s"%(str(oid)))
		#core level
		cur.execute("SELECT O_ID FROM port WHERE level=3")
		for i in range(cur.rowcount):
			row=cur.fetchone()
			oid=row[0]
			cur2.execute("SELECT O_ID FROM port JOIN node ON port.target_E_ID=node.E_ID WHERE port.O_ID=%s AND node.level=2"%(str(oid)))
			if cur2.rowcount>0:
				cur3.execute("UPDATE port SET inFilter=1 WHERE O_ID=%s"%(str(oid)))

		#13 report section
		cur.execute("SELECT count(O_ID) From port")
		print cur.fetchone()[0],"total unique ports"

		cur.execute("SELECT count(O_ID) From port where source=''")
		print "    "+str(cur.fetchone()[0])+"without source"
		cur.execute("SELECT count(O_ID) From port where source!=''")
		print "    "+str(cur.fetchone()[0])+"with    source"

		cur.execute("SELECT count(O_ID) From port where source!='' and target_E_ID IS NULL")
		print "        "+str(cur.fetchone()[0])+"have no internal target"
		cur.execute("SELECT count(O_ID) From port where source!='' and target_E_ID IS NOT NULL")
		print "        "+str(cur.fetchone()[0])+"have    internal target"

		cur.execute("SELECT count(O_ID) From port where source!='' and matched_O_ID IS NOT NULL")
		print "            "+str(cur.fetchone()[0])+" are identified (know their pair or surely not used"

		print ''
		cur.execute("SELECT count(O_ID) From port where restLink=0 and matched_O_ID IS NULL and target_E_ID IS NOT NULL")
		print str(cur.fetchone()[0])+" restLink=0 but has no matching **"
		cur.execute("SELECT count(O_ID) From port where restLink>0 and matched_O_ID IS NULL and target_E_ID IS NOT NULL")
		print str(cur.fetchone()[0])+" restLink>0 but has no matching **"
		con3.close()
		con2.close()
		con.close()

		
		#restart monwalkd service
		result = subprocess.Popen(shlex.split("service monwalkd restart"),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		result.wait()

		print 'finish'
		
		return shortcut.response("OK")

	index.exposed = True

class UpdateVLAN(object):
	'''
	update node and port from cnsmon
	'''
	def index(self):
		
		con = MySQLdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()

		cur.execute("SELECT E_ID, E_Name FROM node")
		answer=[]
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
		
		print 'finish getting model'

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

		cur.execute("SELECT E_ID, E_Name, brand, model FROM node WHERE level=1")

		counter=0
		while True:
			counter+=1
			print counter
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
					output=result.communicate()[0]
					while result.poll()==None:
						output+=result.communicate()[0]
					result.wait()

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
					
					output=result.communicate()[0]
					while result.poll()==None:
						output+=result.communicate()[0]
					result.wait()

					if result.returncode!=0:
						#can go on this mib
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
					cur.execute("SELECT O_ID FROM port WHERE E_ID=%s AND Ifindex=%s"%(str(E_ID),str(ifIndex)))
					if cur.rowcount==1:
						O_ID=cur.fetchone()[0]
						valueString=''
						for vlan in answer[E_ID][ifIndex]:
							valueString+=" (%s,%s),"%(str(O_ID),str(vlan))
						
						valueString=valueString[0:-1]+';'

						cur.execute("INSERT INTO vlan_port (O_ID, vlanNumber) VALUES %s"%(valueString))

		con.close()

		print 'completely finish'
		return shortcut.response("OK")

	index.exposed = True

class Tool(object):
	updateFromCNSMON = UpdateFromCNSMON()
	updateVLAN = UpdateVLAN()