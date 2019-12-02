import time
import subprocess,shlex
import MySQLdb
c=0
command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN das-cbwci01.csloxinfo.net 1.3.6.1.2.1.17.7.1.4.3.1.2"
print shlex.split(command)
result = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
#print result.poll()
output=result.communicate()[0]
while result.poll()==None:
	output+=result.communicate()[0]
	#print '!'
	c+=1
	#time.sleep(1)
	#print '!'

result.wait()
print output
print "3rd checkpoint"
print c
