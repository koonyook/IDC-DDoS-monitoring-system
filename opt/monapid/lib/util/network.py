import subprocess, shlex
import re
import random
import string
import time

class IPAddr:
	'''	
	IP address
		- sequence
	'''

	def __init__(self,ip):
		# ip can be either an integer or a string

		if isinstance(ip, (int, long)):
			self.sequence=[0]*4

			self.sequence[3]=ip%(256**1)
			ip-=self.sequence[3]
			self.sequence[2]=ip%(256**2)
			ip-=self.sequence[2]
			self.sequence[1]=ip%(256**3)
			ip-=self.sequence[1]
			self.sequence[0]=ip%(256**4)
			ip-=self.sequence[0]
			
			if ip!=0:
				raise NameError('InvalidIP')
			else:
				self.sequence[3]/=(256**0)
				self.sequence[2]/=(256**1)
				self.sequence[1]/=(256**2)
				self.sequence[0]/=(256**3)

		else:
			ipString=str(ip)
			self.sequence=ipString.split('.')
			if len(self.sequence) != 4:
				raise NameError('InvalidIP')
			try:
				for i in range(len(self.sequence)):
					self.sequence[i]=int(self.sequence[i])
					if not (self.sequence[i] in range(256)):
						raise NameError('InvalidIP') 

			except ValueError:
				raise NameError('InvalidIP')
			except NameError:
				raise
			except:
				print "Unexpected error:", sys.exc_info()[0]
				raise 
	
	def getProduct(self):
		product=0;
		for num in self.sequence:
			product = product*256 + num
		return product

	def isSubnetMask(self):
		'''	
		return int of slash notation
		return False of false subnetmask 
		'''
		product=self.getProduct()
		divider=2**31;
		count=0;
		while product/divider==1:
			product=product%divider
			divider/=2
			count+=1
		
		if product==0:
			return count
		else:
			return False

	def isInNetwork(self,networkID,subnetMask):
		if self==networkID:
			return False
		
		networkProduct=networkID.getProduct()
		subnetProduct=subnetMask.getProduct()
		myProduct=self.getProduct()
		
		if (myProduct&subnetProduct) == networkProduct:
			return True
		else:
			return False

	def __eq__(self,other):
		return (str(self)==str(other))

	def __repr__(self):
		res=[]
		for num in self.sequence:
			res.append(str(num))
		return '.'.join(res)
		

def getIPPoolStringList(ipList):
	'''
	ipList=list of string of ip
	return list of string
	'''
	if len(ipList)<=1:
		return ipList
	
	result=[]

	productList=[]
	for element in ipList:
		productList.append(IPAddr(element).getProduct())
	
	productList.sort()
	startIP=productList[0]
	stopIP=productList[0]
	for i in range(1,len(productList)):
		if productList[i]==productList[i-1]+1:
			stopIP=productList[i]
		else:
			if startIP!=stopIP:
				result.append(str(IPAddr(startIP))+'-'+str(IPAddr(stopIP)))
			else:
				result.append(str(IPAddr(startIP)))
			startIP=productList[i]
			stopIP=productList[i]
	
	if startIP!=stopIP:
		result.append(str(IPAddr(startIP))+'-'+str(IPAddr(stopIP)))
	else:
		result.append(str(IPAddr(startIP)))
	
	return result


def getVlanStringList(vlanList):
	'''
	vlanList=list of string of vlan
	return list of string
	'''
	if len(vlanList)<=1:
		return vlanList
	
	result=[]
	
	#convert string to int
	for i in range(len(vlanList)):
		vlanList[i]=int(vlanList[i])

	productList=vlanList
	
	vlanList.sort()
	startVlan=productList[0]
	stopVlan=productList[0]
	for i in range(1,len(productList)):
		if productList[i]==productList[i-1]+1:
			stopVlan=productList[i]
		else:
			if startVlan!=stopVlan:
				result.append(str(startVlan)+'-'+str(stopVlan))
			else:
				result.append(str(startVlan))
			startVlan=productList[i]
			stopVlan=productList[i]
	
	if startVlan!=stopVlan:
		result.append(str(startVlan)+'-'+str(stopVlan))
	else:
		result.append(str(startVlan))
	
	return result