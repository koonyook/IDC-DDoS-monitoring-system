import cherrypy
import json

class HelloWorld(object):
	def index(self):
		cherrypy.response.headers['Content-Type']='application/json'
		cherrypy.response.headers['Access-Control-Allow-Origin']='*'
		return json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4, separators=(',', ': '))
		#return "Hello World!"

	index.exposed = True


cherrypy.config.update({'engine.autoreload_on':False})
cherrypy.config.update({'server.thread_pool':10})
cherrypy.config.update({'server.socket_host': '0.0.0.0','server.socket_port': 8080}) 
cherrypy.quickstart(HelloWorld())
