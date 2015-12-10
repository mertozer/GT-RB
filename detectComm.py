import networkx as nx
import copy
import operator
import random
import time
#G = nx.read_edgelist('networks/booksUSPolitics/polbooks_edges.txt')
#G = nx.karate_club_graph()
#G = nx.read_edgelist('networks/dolphin/dolphins_edges.txt')
G = nx.connected_caveman_graph(20,8)
nodeCommDict = {}
commNodeDict = {}
deltaQ = {}
a_i = {}
connected = {}
secAssTime = 0
firstAssTime = 0
beforeJoinTime = 0
resPars = [10,1,0.5,0.1,0.05,0.01,0.001,0.0001,0.00001,0.000001]

def initComms():
	global nodeCommDict
	global commNodeDict
	nodeCommDict = {}
	commNodeDict = {}
	nodes = nx.nodes(G)
	for node in nodes:
		nodeCommDict[node] = node
		commNodeDict[node] = [node]

def printInfo():
	print(nx.info(G))
	print('Num of Comms: ' + str(len(commNodeDict)))
	print('Comm Assignments: ' + str(commNodeDict))

def rho(c1, c2):
	return 1 if c1 == c2 else 0

def initDeltaQandA_i(resPar):
	global deltaQ
	global a_i
	global connected
	deltaQ = {}
	a_i = {}
	m = float(G.size())
	for node in G:
		a_i[node] = G.degree(node)/(2*m)
		deltaQ[node] = {}
		connected[node] = {}
		degreeNode = G.degree(node)
		for node2 in G[node]:
			deltaQ[node][node2] = 1/(2*m) - resPar*degreeNode*G.degree(node2)/(4*m*m)
			connected[node][node2] = True
			try:
				connected[node2][node] = True
			except KeyError:
				connected[node2] = {}
				connected[node2][node] = True
	
def calcGlobalModularity():
	m = float(G.size()) #check it once more
	nodes = nx.nodes(G)
	sumIJ = 0.0
	for nodeI in nodes:
		sumJ = 0.0
		for nodeJ in nodes:
			if nodeI == nodeJ: continue
			rhoV = rho(nodeCommDict[nodeI],nodeCommDict[nodeJ])
			sumJ += ((1 if nodeJ in G[nodeI] else 0) - (float(G.degree(nodeI)*G.degree(nodeJ))/(2*m)))*rhoV
		sumIJ += sumJ
	modularity = (1.0/(2*m)) * sumIJ
	return modularity

def joinComms(commJ,commI):
	#i joins j
	global commNodeDict
	global nodeCommDict
	global deltaQ
	global a_i
	global secAssTime
	global firstAssTime
	global connected
	#update deltaQ
	
	start_timeFor = time.time()
	connectedToIJ = {}
	connectedToIJ.update(connected[commI])
	connectedToIJ.update(connected[commJ])
	
	for commKIJ in connectedToIJ:
		if not commJ == commKIJ:
			deltaQ[commJ][commKIJ] = (deltaQ[commI][commKIJ] if commKIJ in deltaQ[commI] else 0) + (deltaQ[commJ][commKIJ] if commKIJ in deltaQ[commJ] else 0)
	for commKI in connected[commI]:
		if not commKI in connectedToIJ and not commJ == commKI:
			deltaQ[commJ][commKI] = (deltaQ[commI][commKI] if commKI in deltaQ[commI] else 0) - 2*a_i[commJ]*a_i[commKI]
	for commKJ in connected[commJ]:
		if not commKJ in connectedToIJ and not commJ == commKJ:
			deltaQ[commJ][commKJ] = (deltaQ[commJ][commKJ] if commKJ in deltaQ[commJ] else 0) - 2*a_i[commI]*a_i[commKJ]
		
	start_time = time.time()
	
	for comm in deltaQ:
		if commI in deltaQ[comm]:
			del deltaQ[comm][commI]
	del deltaQ[commI]
	firstAssTime += time.time()-start_time
	
	start_time = time.time()
	a_i[commJ] = a_i[commJ] + a_i[commI]
	a_i[commI] = 0
	for node in commNodeDict[commI]:
		nodeCommDict[node] = commJ
	commNodeDict[commJ] += commNodeDict[commI]
	del commNodeDict[commI]
	start_time = time.time()
	commsConnectedToCommI = connected[commI]
	for comm in commsConnectedToCommI:
		if commI in connected[comm]:
			del connected[comm][commI]
			connected[comm][commJ] = True
	connected[commJ].update(commsConnectedToCommI)
	if commJ in connected[commJ]:
		del connected[commJ][commJ]
	del connected[commI]
	secAssTime += time.time()-start_time
	
def run():
	global commNodeDict
	global nodeCommDict
	global deltaQ
	global a_i
	update = False
	maxModularityGain = 0.0
	joining = 0
	toBeJoined = 0
	comm = list(commNodeDict)[random.randint(0,len(commNodeDict)-1)]
	try:
		maxCommToJoin,modularityChange = max(deltaQ[comm].items(),key=operator.itemgetter(1))
	except Exception: #meaning no possible merge for comm
		#print('KeyError')
		modularityChange = -1
	if modularityChange > 0:
		update = True
		start_time = time.time()
		joinComms(maxCommToJoin,comm)
	
	return update
fw = open('results.txt','w')
if __name__ == "__main__":
	random_restart = 100
	printInfo()
	for resPar in resPars:
		commNodeDictMax = {}
		maximumModularityAchieved = 0
		avgNumberOfComms = 0
		avgModularity = 0
		restart_counter = random_restart
		while restart_counter > 0:
			#print('Random Restart ' + str(random_restart))
			#print('Initializing Communities...')
			initComms()
			#print('Initializing delta Q...')
			initDeltaQandA_i(resPar)
			update = run()
			runCount = 0
			while update:
				update = run()
				runCount += 1
			modularityAchieved = calcGlobalModularity()
			if modularityAchieved > maximumModularityAchieved:
				maximumModularityAchieved = modularityAchieved
				commNodeDictMax = copy.deepcopy(commNodeDict)
			avgNumberOfComms += len(commNodeDict)
			avgModularity += modularityAchieved
			restart_counter -= 1
		avgNumberOfComms /= random_restart
		avgModularity /= random_restart
		fw.write(str(resPar) + ',' + str(avgNumberOfComms) + ',' + str(avgModularity) + ',' + str(len(commNodeDictMax)) + ',' + str(maximumModularityAchieved) + ',' + str(random_restart))
		fw.write('\n')
		print('Resolution Parameter: ' + str(resPar))
		print('\tModularity Achieved: ' + str(maximumModularityAchieved))
		print('\tNumber Of Communities: ' + str(len(commNodeDictMax)))
		#print('\t'+ str(commNodeDictMax))
		print('\tavg modularity achieved: ' + str(avgModularity))
		print('\tavg number of communities: ' + str(avgNumberOfComms))

