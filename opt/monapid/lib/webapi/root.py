from webapi.testAPI import Test
from webapi.portAPI import Port
from webapi.toolAPI import Tool
from webapi.ipAPI   import IPStat
from webapi.incidentAPI import Incident

import setting
import cherrypy


class ApplicationInterface(object):

	def index(self):
		return '<H1>Help for Monitoring API usage</H1>\nbla bla bla...'
	index.exposed = True

	#testing branch
	test = Test()
	
	#real branch
	port = Port()
	tool = Tool()
	incident = Incident()
	ip = IPStat()