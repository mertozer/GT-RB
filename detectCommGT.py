import networkx as nx
import copy
import operator
import random
import time
import sys

#G = nx.read_edgelist('networks/booksUSPolitics/polbooks_edges.txt')
#G = nx.karate_club_graph()
#G = nx.read_edgelist('networks/dolphin/dolphins_edges.txt')
G = nx.connected_caveman_graph(20,8)
nodeCommDict = {}
commNodeDict = {}
Q_U = {}
a_i = {}
strategyFixed = {}
currentPayoff = {}
secAssTime = 0
firstAssTime = 0
beforeJoinTime = 0
#Loss function constant
c = 0
def initComms():
	global nodeCommDict
	global commNodeDict
	global strategyFixed
	global currentPayoff
	nodeCommDict = {}
	commNodeDict = {}
	nodes = nx.nodes(G)
	for node in nodes:
		nodeCommDict[node] = node
		commNodeDict[node] = [node]
		currentPayoff[node] = 0
		strategyFixed[node] = False

def printInfo():
	print(nx.info(G))
	print('Num of Comms: ' + str(len(commNodeDict)))
	print('Comm Assignments: ' + str(commNodeDict))

def rho(c1, c2):
	return 1 if c1 == c2 else 0

def initQ_UandA_i():
	global Q_U
	global a_i
	Q_U = {}
	a_i = {}
	m = float(G.size())
	for node in G:
		a_i[node] = G.degree(node)/(2*m)
		Q_U[node] = G.degree(node)/(2*m)
	
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

def common_elements(list1, list2):
    return len([element for element in list1 if element in list2])
	
def calcIndModularity(node, possibleCommAss):
	global Q_U
	neighbors = G[node]
	m = float(G.size())
	sumJ = 0
	for node2 in commNodeDict[possibleCommAss]:
		sumJ += (1 if node2 in neighbors else 0)#*rho(possibleCommAss,nodeCommDict[node2]) #- ((G.degree(node)*G.degree(node2))/(2*m))*common_elements(possibleCommAss,nodeCommDict[node2])
		# It is weird to traverse over only the nodes in the same community and calculate rho as well!!! That's what paper says.
	
	sumJ -= G.degree(node)*Q_U[possibleCommAss]
	indModularity = (1/(2*m))*sumJ
	return indModularity
	
def calcLoss(node, possibleCommAss):
	sizes = {}
	maxSizeComm = 0
	minSizeComm = sys.maxint
	for comm in commNodeDict:
		if maxSizeComm < len(commNodeDict[comm]):
			maxSizeComm = len(commNodeDict[comm])
		if minSizeComm > len(commNodeDict[comm]):
			minSizeComm = len(commNodeDict[comm])
	for comm in commNodeDict:
		sizes[comm] = (float(len(commNodeDict[comm]))-minSizeComm)/(maxSizeComm-minSizeComm+0.000001)
	return c*(sizes[possibleCommAss]) # 1-size favors bigger commmunities, size favors smaller communities
	
def findBestStrategyFor(node):
	global commNodeDict
	global nodeCommDict
	global currentPayoff
	global Q_U
	m = float(G.size())
	#currentGain = calcIndModularity(node,nodeCommDict[node])
	#currentLoss = calcLoss(node,nodeCommDict[node])
	#currentPayoff = currentGain - currentLoss
	maxPayoff = currentPayoff[node]
	bestCommAss = nodeCommDict[node]
	neighborCommSet = {}
	for neNode in G[node]:
		neighborCommSet[nodeCommDict[neNode]] = 0
		
	for comm in neighborCommSet:
		tmpGain = calcIndModularity(node,comm)
		tmpLoss = calcLoss(node,comm)
		tmpPayoff = tmpGain - tmpLoss
		if tmpPayoff > maxPayoff:
			maxPayoff = tmpPayoff
			bestCommAss = comm
	
	if maxPayoff > currentPayoff[node]:
		#print('Node: ' + str(node) + ' migrates from ' + str(nodeCommDict[node]) + ' to ' + str(bestCommAss))
		communityItBelongsTo = nodeCommDict[node]
		nodeListOfCommunityItBelongsTo = commNodeDict[communityItBelongsTo]
		del nodeListOfCommunityItBelongsTo[nodeListOfCommunityItBelongsTo.index(node)]
		Q_U[bestCommAss] += G.degree(node)/(2*m)
		Q_U[nodeCommDict[node]] -= G.degree(node)/(2*m)
		if nodeListOfCommunityItBelongsTo == []:
			del commNodeDict[communityItBelongsTo]
		commNodeDict[bestCommAss].append(node)
		nodeCommDict[node] = bestCommAss
		currentPayoff[node] = maxPayoff
		#print('tempGain ' + str(tmpGain))
		#print('tempLoss ' + str(tmpLoss))		
		# raw_input()
		return False
	return True
		
def run():
	global strategyFixed
	node = G.nodes()[random.randint(0,len(G)-1)]
	strategyFixed[node] = findBestStrategyFor(node)
fw = open('gresults.txt','w')
if __name__ == "__main__":
	cVars = [10,1,0.5,0.1,0.05,0.01,0.001,0.0001,0.00001,0.000001]
	#cVars = [100]
	random_restart = 10
	printInfo()
	for cVar in cVars:
		avgNumberOfComms = 0
		avgModularity = 0
		maximumModularityAchieved = 0
		commNodeDictMax = {}
		c = cVar
		restart_counter = random_restart
		while restart_counter > 0:
			#print('Run ' + str(random_restart))
			isAllFixed = False
			initComms()
			initQ_UandA_i()
			numOfIterations = 0
			while not isAllFixed and numOfIterations < 1000:
				run()
				isAllFixed = True
				for node in strategyFixed:
					isAllFixed = isAllFixed and strategyFixed[node]# and findBestStrategyFor(node)
				numOfIterations += 1
			#print(str(numOfIterations) + ' iterations taken')
			modularityAchieved = calcGlobalModularity()
			if modularityAchieved > maximumModularityAchieved:
				maximumModularityAchieved = modularityAchieved
				commNodeDictMax = copy.deepcopy(commNodeDict)
			avgNumberOfComms += len(commNodeDict)
			avgModularity += modularityAchieved
			restart_counter -= 1
		avgNumberOfComms /= random_restart
		avgModularity /= random_restart
		fw.write(str(cVar) + ',' + str(avgNumberOfComms) + ',' + str(avgModularity) + ',' + str(len(commNodeDictMax)) + ',' + str(maximumModularityAchieved) + ',' + str(random_restart))
		fw.write('\n')
		print('Resolution Parameter: ' + str(cVar))
		print('\tModularity Achieved: ' + str(maximumModularityAchieved))
		print('\tNumber Of Communities: ' + str(len(commNodeDictMax)))
		#print('\t'+ str(commNodeDictMax))
		print('\tavg modularity achieved: ' + str(avgModularity))
		print('\tavg number of communities: ' + str(avgNumberOfComms))


