'''
	this file assign CONSTANT_VALUE only

	usage:
		import setting
		print setting.MAIN_PATH
'''
LOG_PATH="/var/log/"

MAIN_PATH="/opt/monapid/lib/"			#end with '/' because this is only way to allow path to be "/"

MAIN_DB_IP_ADDRESS="?.?.?.?"
MAIN_DB_USERNAME="?"
MAIN_DB_PASSWORD="?"
MAIN_DB_NAME="NetTracker"

CNS_DB_IP_ADDRESS='?.?.?.?'
CNS_DB_USERNAME='?'
CNS_DB_PASSWORD='?'
CNS_DB_NAME='E_Mon'

IDCINFO_DB_IP_ADDRESS="?.?.?.?"
IDCINFO_DB_USERNAME="?"
IDCINFO_DB_PASSWORD="?"
IDCINFO_DB_NAME="idcinfo"

CMDB_IP_ADDRESS='?.?.?'
CMDB_USERNAME='?'
CMDB_PASSWORD='?'
CMDB_NAME='topology'

'''
color gradient
0.0 => FFFFFF
0.5 => FFFF00
1.0 => FF0000
'''
COLOR_LEVEL=[]
COLOR_LEVEL.append([0.0, 255,255,255])	#first append have to be 0.0
COLOR_LEVEL.append([0.5, 255,255,  0])
COLOR_LEVEL.append([1.0, 255,  0,  0])	#last append have to be 1.0

PRODUCTION=False

ZERO_CAPACITY_COLOR='#0000FF'