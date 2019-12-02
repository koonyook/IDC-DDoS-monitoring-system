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
			cur.execute("SELECT O_ID, source, target, interface, inFilter, level FROM port WHERE level=%s"%(str(level)))
		elif level==0:
			cur.execute("SELECT O_ID, source, target, interface, inFilter, level FROM port")

		while True:
			row=cur.fetchone()
			if row is not None:
				content.append({'oid':row[0],'source':row[1],'destination':row[2],'interface':row[3],'inFilter':row[4],'level':row[5]})
			else:
				break
		
		con.close()

		return shortcut.response(content)
	index.exposed = True

class GetColor(object):
	def index(self,level,timestamp=None):
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

		if timestamp is not None:
			#fixed timestamp
			timestamp=int(timestamp)
			if timestamp%300 != 0:
				timestamp -= timestamp%300
			
			cur.execute("SELECT port.O_ID, port.speed, Traffic.inRate, Traffic.outRate FROM port LEFT OUTER JOIN Traffic ON port.O_ID=Traffic.O_ID WHERE %s and Traffic.timestamp=%s"%(levelOption,str(timestamp)))
		
		else:
			cur.execute("SELECT port.O_ID, port.speed, lastTraffic.inRate, lastTraffic.outRate FROM port LEFT OUTER JOIN lastTraffic ON port.O_ID=lastTraffic.O_ID WHERE %s "%(levelOption))

			
		while True:
			row=cur.fetchone()
			if row is not None:

				maxRate=float(row[1])*1000	#convert to bit per sec
				inRate=row[2]
				outRate=row[3]
				
				if maxRate==0:
					content.append({'oid':row[0],'color': setting.ZERO_CAPACITY_COLOR})	#for uncalculatable
				else:
					selectedRate=max(inRate,outRate)
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
	def index(self,oidList,timestamp=None):
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
				cur2.execute("""
					SELECT pipe_has_ipv4.IPV4_addr
					FROM project
					INNER JOIN mainpipe ON mainpipe.ProjectID = project.ProjectID
					INNER JOIN pipe_has_ipv4 ON pipe_has_ipv4.PipeID = mainpipe.PipeID
					WHERE project.ProjectID='%s'
				"""%(str(projectID)))
				lastPort['ip']=[]
				while True:
					row=cur2.fetchone()
					if row is not None:
						lastPort['ip'].append(row[0])
					else:
						break
				
				lastPort['ip']=network.getIPPoolStringList(lastPort['ip'])

			else:
				lastPort['customer']='-'
				lastPort['ip']='-'

			#traffic info
			if timestamp is not None:
				#fixed timestamp
				timestamp=int(timestamp)
				if timestamp%300 != 0:
					timestamp -= timestamp%300

				cur.execute("SELECT timestamp, inRate, outRate FROM Traffic WHERE O_ID=%s and timestamp=%s"%(str(oid),str(timestamp)))
										
			else:
				cur.execute("SELECT timestamp, inRate, outRate FROM lastTraffic WHERE O_ID=%s"%(str(oid)))
			
			row=cur.fetchone()
	
			if row is not None:
				lastPort['timestamp']=row[0]
				if lastPort['capacity']==0:
					lastPort['inbound']={'rate':row[1],'percent':'null' ,'color':setting.ZERO_CAPACITY_COLOR}
					if row[1] is None:
						lastPort['inbound']['rate']='null'
					
					lastPort['outbound']={'rate':row[2],'percent':'null' ,'color':setting.ZERO_CAPACITY_COLOR}
					if row[2] is None:
						lastPort['outbound']['rate']='null'
				
				else:
					if row[1] is not None:
						inRatio=float(row[1])/float(lastPort['capacity'])
						lastPort['inbound']={'rate':row[1],'percent':inRatio*100,'color':general.getColorCode(inRatio)}
					else:
						lastPort['inbound']={'rate':'null','percent':'null','color':'null'}
					
					if row[2] is not None:
						outRatio=float(row[2])/float(lastPort['capacity'])
						lastPort['outbound']={'rate':row[2],'percent':outRatio*100,'color':general.getColorCode(outRatio)}
					else:
						lastPort['outbound']={'rate':'null','percent':'null','color':'null'}

			else:
				#never mornitor
				lastPort['inbound']={'rate':'none','percent':'none','color':'none'}
				lastPort['outbound']={'rate':'none','percent':'none','color':'none'}
			
			##########################
			content.append(lastPort)

		con.close()
		con2.close()
		return shortcut.response(content)
	index.exposed = True

class Port(object):
	init = Init()
	getColor = GetColor()
	getMoreDetail = GetMoreDetail()
