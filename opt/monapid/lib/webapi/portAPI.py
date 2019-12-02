import setting
import MySQLdb as mdb
import json
from util import general
from util import shortcut
from util import network
import cherrypy

levelDict={'core':3,'distribute':2,'access':1, 'all':0}

class Init(object):
	def index(self,level):
		#check input
		if level not in ['core','distribute','access','all']:
			return shortcut.response("ERROR: level can be 'core','distribute', 'access', or 'all' ")

		#process
		content=[]
		level=levelDict[level]
		
		con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		
		if level in [1,2,3]:
			cur.execute("SELECT O_ID, source, target, interface, inFilter, level, E_ID, matched_O_ID, Ifindex FROM port WHERE level=%s"%(str(level)))
		elif level==0:
			cur.execute("SELECT O_ID, source, target, interface, inFilter, level, E_ID, matched_O_ID, Ifindex FROM port")

		while True:
			row=cur.fetchone()
			if row is not None:
				content.append({'oid':row[0],'source':row[1],'destination':row[2],'interface':row[3],'inFilter':row[4],'level':row[5], 'eid':row[6], 'matched_oid':row[7], 'Ifindex':row[8]})
			else:
				break
		
		con.close()

		return shortcut.response(content)
	index.exposed = True


class GetColor(object):
	def index(self,level,timestampStart=None,timestampEnd=None):
		#check input
		if level not in ['core','distribute','access','all']:
			return shortcut.response("ERROR: level can be 'core','distribute', 'access', or 'all' ")
		
		#process
		content=[]
		level=levelDict[level]
		
		con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		
		levelOption=""
		if level==0:
			levelOption=" 1=1 "
		else:
			levelOption=" port.level=%s "%(str(level))

		if timestampStart is not None and timestampEnd is not None:
			#fixed timestamp
			timestampStart=int(timestampStart)
			timestampEnd  =int(timestampEnd)
			#cannot get NULL value from MAX in most case
			cur.execute("SELECT port.O_ID, port.speed, MAX(log.value) FROM port LEFT OUTER JOIN log ON port.O_ID=log.O_ID WHERE %s and log.timestamp>=%s and log.timestamp<=%s GROUP BY port.O_ID"%(levelOption,str(timestampStart),str(timestampEnd)))
		
		else: #bring last update
			cur.execute("SELECT port.O_ID, port.speed, MAX(lastLog.value) FROM port LEFT OUTER JOIN lastLog ON port.O_ID=lastLog.O_ID WHERE %s GROUP BY port.O_ID"%(levelOption))

			
		while True:
			row=cur.fetchone()
			if row is not None:

				maxRate=float(row[1])*1000	#convert to bit per sec
				selectedRate=row[2]
				
				if maxRate==0:
					content.append({'oid':row[0],'color': setting.ZERO_CAPACITY_COLOR})	#for uncalculatable
				else:
					if selectedRate is None:
						content.append({'oid':row[0],'color': selectedRate})
					else:
						colorCode=general.getColorCode(float(selectedRate)/float(maxRate))
						content.append({'oid':row[0],'color': colorCode})
			else:
				break

		con.close()

		return shortcut.response(content)
	index.exposed = True

class GetMoreDetail(object):
	def index(self,oidList,timestampStart=None,timestampEnd=None):
		#process input
		oidList=oidList.strip().split(',')
		for i in range(len(oidList)):
			oidList[i]=int(oidList[i])
		
		content=[]

		con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
		cur = con.cursor()
		
		con2 = mdb.connect(setting.IDCINFO_DB_IP_ADDRESS, setting.IDCINFO_DB_USERNAME, setting.IDCINFO_DB_PASSWORD, setting.IDCINFO_DB_NAME)
		cur2 = con2.cursor()

		#one by one
		for oid in oidList:
			lastPort={'oid':oid}
			#easy general info
			cur.execute("SELECT IfAlias, speed, Interface, source FROM port WHERE O_ID=%s"%(str(oid)))
			row=cur.fetchone()
			if row is None:
				continue	#just ignore that asking
			else:
				lastPort['description']=str(row[0])
				lastPort['capacity']=float(row[1])*1000  #convert to bit per sec
				interfaceName=row[2]
				switchName=row[3]
			
			#vlan info (in case there is a real customer on this port)
			lastPort['vlan']=[]
			cur.execute("SELECT vlanNumber FROM vlan_port WHERE O_ID=%s"%(str(oid)))
			while True:
				row=cur.fetchone()
				if row is not None:
					lastPort['vlan'].append(row[0])
				else:
					break
			
			#customer info
			cur2.execute("""
				SELECT customer.CustName, customer.ContractPerson, customer.Telephone, customer.Mobile, project.ProjectID, project.ProjectName, racklocation.LocationName
				FROM customer
				INNER JOIN project ON project.Customer_CustPrimaryID = customer.CustPrimaryID
				INNER JOIN mainrack ON mainrack.ProjectID = project.ProjectID
				INNER JOIN racklocation ON racklocation.LocationID = mainrack.LocationID
				INNER JOIN rack_has_switch_port ON rack_has_switch_port.Rack_RackID = mainrack.RackID
				INNER JOIN switchport ON switchport.SwitchPortID = rack_has_switch_port.Switch_port_SwitchportID
				INNER JOIN equipment_has_swport ON equipment_has_swport.SwitchPortID = switchport.SwitchPortID
				INNER JOIN equipment ON equipment.EquipID = equipment_has_swport.EquipID 
				INNER JOIN switch ON switchport.Switch_SwitchID=SwitchID
				WHERE 
				switch.SwitchName LIKE '%s.%%' and 
				switchport.SwitchportName LIKE '%s'
			"""%(switchName, interfaceName))
			row=cur2.fetchone()
			if row is not None:
				lastPort['customer']={'CustName':row[0],'ContractPerson':row[1],'Telephone':row[2],'Mobile':row[3],'ProjectID':row[4],'ProjectName':row[5],'LocationName':row[6]}
				projectID=row[4]
				
				#cur2.execute("""
				#	SELECT pipe_has_ipv4.IPV4_addr
				#	FROM project
				#	INNER JOIN mainpipe ON mainpipe.ProjectID = project.ProjectID
				#	INNER JOIN pipe_has_ipv4 ON pipe_has_ipv4.PipeID = mainpipe.PipeID
				#	WHERE project.ProjectID='%s'
				#"""%(str(projectID)))
				
				if len(lastPort['vlan'])>0:
					possibleVlanString=''
					for vlan in lastPort['vlan']:
						possibleVlanString+=str(vlan)+','
					
					possibleVlanString=possibleVlanString[0:-1]

					#vlanCondition="AND vlan.VlanNumber in (%s) "%(possibleVlanString)

				else:
					possibleVlanString='0'
					#vlanCondition=""

				#new execution to scope ip and vlan by 1.projectID 2.existing vlans on that specific port
				cur2.execute("""
					SELECT ipv4.IPV4_addr, vlan.VlanNumber 
					FROM mainpipe
					INNER JOIN pipe_has_ipv4 ON pipe_has_ipv4.PipeID = mainpipe.PipeID
					INNER JOIN ipv4 ON ipv4.IPV4_addr = pipe_has_ipv4.IPV4_addr
					INNER JOIN network ON network.NetworkID = ipv4.Network_NetworkID
					INNER JOIN vlan ON vlan.VlanID = network.Vlan_VlanID
					WHERE mainpipe.ProjectID='%s'
					AND vlan.VlanNumber in (%s) 
				"""%(str(projectID),possibleVlanString))
				
				lastPort['ip']=[]
				lastPort['vlan']=[]
				while True:
					row=cur2.fetchone()
					if row is not None:
						if row[0] not in lastPort['ip']:
							lastPort['ip'].append(row[0])
						if row[1] not in lastPort['vlan'] and row[1]!=None:
							lastPort['vlan'].append(row[1])
					else:
						break
				
				if lastPort['ip']==[]:
					#case of nothing come out because of junk vlan
					cur2.execute("""
						SELECT pipe_has_ipv4.IPV4_addr
						FROM mainpipe
						INNER JOIN pipe_has_ipv4 ON pipe_has_ipv4.PipeID = mainpipe.PipeID
						WHERE mainpipe.ProjectID='%s'
					"""%(str(projectID)))

					while True:
						row=cur2.fetchone()
						if row is not None:
							if row[0] not in lastPort['ip']:
								lastPort['ip'].append(row[0])
						else:
							break

				lastPort['ip']=network.getIPPoolStringList(lastPort['ip'])				
				lastPort['vlan']=network.getVlanStringList(lastPort['vlan'])

			else:
				lastPort['customer']='-'
				lastPort['ip']='-'
				lastPort['vlan']='-'
			
			#traffic info
			if timestampStart is not None and timestampEnd is not None:
				#fixed timestamp
				timestampStart=int(timestampStart)
				timestampEnd=int(timestampEnd)

				cur.execute("""SELECT timestamp, attribute, value FROM log 
					WHERE O_ID=%s and log.timestamp>=%s and log.timestamp<=%s and value in 
					(
						SELECT MAX(value) FROM log 
						WHERE O_ID=%s and log.timestamp>=%s and log.timestamp<=%s 
						GROUP BY attribute
					) 
					GROUP BY attribute			
				"""%(str(oid),str(timestampStart),str(timestampEnd),str(oid),str(timestampStart),str(timestampEnd)))
			else:
				cur.execute("SELECT timestamp, attribute, value FROM lastLog WHERE O_ID=%s"%(str(oid)))
	
			if cur.rowcount==2:
				
				for i in [1,2]:
					row=cur.fetchone()
					if row[1]=='I':
						direction='inbound'
					if row[1]=='O':
						direction='outbound'

					lastPort[direction]={'timestamp':row[0]}
					
					if row[2] is None:
						lastPort[direction]['rate']='null'
					else:
						lastPort[direction]['rate']=row[2]
					
					if lastPort['capacity']==0:
						lastPort[direction]['percent']='null'
						lastPort[direction]['color']=setting.ZERO_CAPACITY_COLOR
					elif lastPort[direction]['rate']=='null':
						lastPort[direction]['percent']='null'
						lastPort[direction]['color']='null'
					else:
						trafficRatio=float(row[2])/float(lastPort['capacity'])
						lastPort[direction]['percent']=trafficRatio*100
						lastPort[direction]['color']=general.getColorCode(trafficRatio)

			elif cur.rowcount<2:
				#never mornitor
				lastPort['inbound']={'timestamp':'none','rate':'none','percent':'none','color':'none'}
				lastPort['outbound']={'timestamp':'none','rate':'none','percent':'none','color':'none'}
			
			else:
				#bug
				print cur.rowcount + 'error at portAPI.py (rowcount>2)'
				lastPort['inbound']={'timestamp':'none','rate':'none','percent':'none','color':'none'}
				lastPort['outbound']={'timestamp':'none','rate':'none','percent':'none','color':'none'}
			##########################
			content.append(lastPort)

		con.close()
		con2.close()
		return shortcut.response(content)
	index.exposed = True

class Search(object):
	#return list of related oid
	def index(self,q):
		answer=[]
		#clssify input string
		if q.isdigit():
			#vlan
			con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
			cur = con.cursor()
			cur.execute("SELECT vlan_port.O_ID FROM vlan_port INNER JOIN port ON vlan_port.O_ID=port.O_ID WHERE vlanNumber=%s AND inFilter=1"%(q))
			for i in range(cur.rowcount):
				answer.append(cur.fetchone()[0])
			con.close()

		elif len(q.split('.'))==4:
			#ip address
			
			con = mdb.connect(setting.IDCINFO_DB_IP_ADDRESS, setting.IDCINFO_DB_USERNAME, setting.IDCINFO_DB_PASSWORD, setting.IDCINFO_DB_NAME)
			cur = con.cursor()
			
			cur.execute("""
				SELECT switch.SwitchName, switchport.SwitchportName
				FROM switchport
				INNER JOIN switch ON switchport.Switch_SwitchID=switch.SwitchID
				INNER JOIN rack_has_switch_port ON switchport.SwitchPortID = rack_has_switch_port.Switch_port_SwitchportID
				INNER JOIN mainrack ON rack_has_switch_port.Rack_RackID = mainrack.RackID
				INNER JOIN project ON mainrack.ProjectID = project.ProjectID
				INNER JOIN mainpipe ON project.ProjectID = mainpipe.ProjectID
				INNER JOIN pipe_has_ipv4 ON mainpipe.PipeID = pipe_has_ipv4.PipeID
				WHERE
				pipe_has_ipv4.IPV4_addr='%s'
			"""%(q))
			
			#get few possible port from idcInfo
			if cur.rowcount==0:
				con.close()
				#end
			else:
				candidatePort=[]
				for i in range(cur.rowcount):
					candidatePort.append(cur.fetchone())

				cur.execute("""
					SELECT vlan.VlanNumber 
					FROM vlan
					INNER JOIN network ON vlan.VlanID = network.Vlan_VlanID
					INNER JOIN ipv4 ON network.NetworkID = ipv4.Network_NetworkID

					WHERE ipv4.IPV4_addr='%s'
				"""%(q))
				if cur.rowcount==0:
					con.close()
					#end
				else:
					vlan=cur.fetchone()[0]
					con.close()
					#filter by my DB
					con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
					cur = con.cursor()
					
					if vlan!=None:
						#this IP has vlan
						for element in candidatePort:	#(name,interface)
							cur.execute("""SELECT vlan_port.O_ID 
								FROM vlan_port 
								INNER JOIN port ON vlan_port.O_ID = port.O_ID
								INNER JOIN node ON port.E_ID = node.E_ID
								WHERE vlanNumber=%s
								AND node.E_Name LIKE '%s'
								AND port.Interface LIKE '%s'
							"""%(str(vlan),element[0],element[1]))

							if cur.rowcount==1:
								answer.append(cur.fetchone()[0])
					else:
						#this IP has no vlan (e.g. 103.246.18.126)
						for element in candidatePort: 	#(name,interface)
							cur.execute("""SELECT port.O_ID
								FROM port 
								INNER JOIN node ON port.E_ID = node.E_ID
								WHERE node.E_Name LIKE '%s'
								AND port.Interface LIKE '%s'
							"""%(element[0],element[1]))

							if cur.rowcount==1:
								answer.append(cur.fetchone()[0])

					con.close()	
		
		else:
			#part of node name
			con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
			cur = con.cursor()

			cur.execute("SELECT port.O_ID FROM port INNER JOIN node ON port.E_ID=node.E_ID WHERE node.name like '%%%s%%' "%(q))

			for i in range(cur.rowcount):
				answer.append(cur.fetchone()[0])
			
			con.close()

			if answer==[]:
				#search by project name
				con = mdb.connect(setting.IDCINFO_DB_IP_ADDRESS, setting.IDCINFO_DB_USERNAME, setting.IDCINFO_DB_PASSWORD, setting.IDCINFO_DB_NAME)
				cur = con.cursor()
				
				cur.execute("""
					SELECT switch.SwitchName, switchport.SwitchportName
					FROM switchport
					INNER JOIN switch ON switchport.Switch_SwitchID=switch.SwitchID
					INNER JOIN rack_has_switch_port ON switchport.SwitchPortID = rack_has_switch_port.Switch_port_SwitchportID
					INNER JOIN mainrack ON rack_has_switch_port.Rack_RackID = mainrack.RackID
					INNER JOIN project ON mainrack.ProjectID = project.ProjectID	
					WHERE project.ProjectName LIKE '%%%s%%' 
					OR project.ProjectID LIKE '%%%s%%'
				"""%(q,q))
				
				candidatePort=[]
				for i in range(cur.rowcount):
					candidatePort.append(cur.fetchone())
				
				con.close()
				#get oid by my DB
				con = mdb.connect(setting.MAIN_DB_IP_ADDRESS, setting.MAIN_DB_USERNAME, setting.MAIN_DB_PASSWORD, setting.MAIN_DB_NAME)
				cur = con.cursor()
				
				for element in candidatePort: 	#(name,interface)
					cur.execute("""SELECT port.O_ID
						FROM port 
						INNER JOIN node ON port.E_ID = node.E_ID
						WHERE node.E_Name LIKE '%s'
						AND port.Interface LIKE '%s'
					"""%(element[0],element[1]))

					if cur.rowcount==1:
						answer.append(cur.fetchone()[0])

		return shortcut.response(answer)

	index.exposed = True

class Port(object):
	init = Init()
	getColor = GetColor()
	getMoreDetail = GetMoreDetail()
	search = Search()