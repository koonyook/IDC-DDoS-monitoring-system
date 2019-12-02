import setting
import MySQLdb
import subprocess, shlex
import json
from util import general
from util import shortcut
import cherrypy



class T1(object):
	'''
	test #1
	'''
	def index(self,x=None):
		result = subprocess.Popen(shlex.split("service monwalkd restart"),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		result.wait()
		return shortcut.response("this is t1"+str(x))

	index.exposed = True

class T2(object):
	'''
	test #2
	'''
	def index(self, r):
		cc=general.getColorCode(float(r))
		return shortcut.response(cc)

	index.exposed = True


class Test(object):
	t1 = T1()
	t2 = T2()
