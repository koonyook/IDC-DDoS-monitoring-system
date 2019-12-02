import setting
import cherrypy
import json
import traceback

def response(content):
	'''
	this is shortcut for API module
	'''
	
	cherrypy.response.headers['Content-Type']='application/json'

	if setting.PRODUCTION==True:
		return json.dumps(content)
	else:
		cherrypy.response.headers['Access-Control-Allow-Origin']='*'
		return json.dumps(content)
		#return json.dumps(content, sort_keys=True, indent=4, separators=(',', ': '))

