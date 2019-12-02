import time
import re
import setting

hexDigit=['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']

def getCurrentTime():
	return time.time()-time.timezone


def getColorCode(r):
	'''
	r: 0.0 - 1.0 or else
	return: string of color code or else
	'''
	if type(r)==type(float()):
		
		if r<0.0:
			r=0.0
		elif r>1.0:
			r=1.0
		
		level=setting.COLOR_LEVEL
		
		if r==1.0:
			answer=level[-1]
		else:
			for i in range(len(level)):
				if r>= level[i][0]:
					#between level[i] and level[i+1]
					#base color
					answer=[r,level[i][1],level[i][2],level[i][3]]
					#plus or minus
					for j in [1,2,3]:
						answer[j]+=int( (level[i+1][j]-level[i][j])*float(r-level[i][0])/float(level[i+1][0]-level[i][0]) )
		
		#change from number to code
		colorCode='#'
		for i in [1,2,3]:
			colorCode+=hexDigit[answer[i]/16]+hexDigit[answer[i]%16]
		
		return colorCode

	else:
		return r
