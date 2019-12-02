import subprocess,shlex

#command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN www.google.com ifInOctets"
command="snmpwalk -v 2c -c 3eF27m85x4Kv927szN dds-bkkcbw31 ifInOctets"

result=subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
result.wait()
print result.returncode

