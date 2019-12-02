import cherrypy
from mainDaemon import Daemon
from webapi.root import ApplicationInterface
import setting


#this is an example
#class MyDaemon(Daemon):
#	def run(self):
#		while True:
#			time.sleep(1)

class monapid(Daemon):
	'''
	Monitoring API Daemon
	'''

	def run(self):
		cherrypy.config.update({'engine.autoreload_on':False})
		cherrypy.config.update({'server.thread_pool':10})
		cherrypy.config.update({'server.socket_host': '0.0.0.0','server.socket_port': 8080}) 
		cherrypy.quickstart(ApplicationInterface())


