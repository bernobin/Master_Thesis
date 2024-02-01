# -*- coding: utf-8 -*-
"""
The packaging algorithm sends trades of fixed size sequentially through
the liquidity pool graph.

If the package size is not small enough the algorithm can generate negative cycles
which breaks the Dijkstra logic.
In order to avoid this router() has a check that no profitable trade is used.

The score/objective computed is the expected amount of liquidity a random trader 
would receive. 
The score is between 0 and the 'average input'.

plotLiquidity() and getCsv() are to make it easy to get a first impression of 
the result. 
In the plots pools can look empty even though they have some liquidity
in them, which can make a great difference for analysis.
The csv's can be explored using for example 'Visone'.

Finally, the 'config.json' file is generated with the 'getConfig.py' file.

"""

import itertools
import pathlib
import matplotlib.pyplot as plt
import json
import copy
import csv
import os



'''
INPUT: 
   liquidities: current liquidity levels in the pool graph.
   start: currency offered for trade
   goal: currency traded for
   tradesize: size of the trade
   fee: fee for the CPMM

OUTPUT:
    tradeFromStart[goal]: amount of goal currency received
    liquidities: updated liquidity levels after trading start for goal.
'''
def router(liquidities, start, goal, tradesize, fee):

    queue = nodes.copy()
    k = queue.index(start)
    queue.insert(0, queue.pop(k))

    tradeFromStart = {}
    pathFromStart = {}
    for node in nodes:
        if node == start:
            tradeFromStart[node] = tradesize
            pathFromStart[node] = [start]
        else:
            tradeFromStart[node] = 0

    i = 0
    while i < len(nodes):
        activeNode = queue[i]
        for node in nodes:
            if (activeNode, node) in edges and liquidities[(activeNode, node)][1] and tradeFromStart[activeNode]:
                x, y = liquidities[(activeNode, node)]
                dx = tradeFromStart[activeNode]
                
                dyInv = x/y * 1/(1-fee) * 1/dx + 1/y
                # check if path s -> activeNode -> node is better than whatever is currently there
                # also check that the trade (activeNode, node) is not profitable as the
                #       current algorithm can't handle profitable cycles.
                if 1/dyInv > tradeFromStart[node] and 1/dyInv < tradeFromStart[activeNode]:
                    tradeFromStart[node] = 1/dyInv
                    pathToActive = pathFromStart[activeNode].copy()
                    pathToActive.append(node)
                    pathFromStart[node] = pathToActive
                
                    j = i+1
                    k = queue.index(node)
                    # we could do a binary search between i and k for more efficiency
                    while(j < len(queue) and tradeFromStart[queue[j]] > tradeFromStart[node]):
                        j+=1

                    queue.insert(j, queue.pop(k))

        i+=1
    

    if goal in pathFromStart:
        path = pathFromStart[goal]
        for i in range(len(path)-1):
            liquidities[(path[i], path[i+1])][0] += (1-fee)*tradeFromStart[path[i]]
            liquidities[(path[i], path[i+1])][1] -= tradeFromStart[path[i+1]]
            liquidities[(path[i+1], path[i])][0] -= tradeFromStart[path[i+1]]
            liquidities[(path[i+1], path[i])][1] += (1-fee)*tradeFromStart[path[i]]

    else:
         tradeFromStart[goal] = 0

    return tradeFromStart[goal], liquidities



'''
INPUT: 
   startingLiquidity: For each pair we start routing with this liquidity configuration
   bucket: Determines the size of trades we are considering (see config)
   splitInto: splitInto many uniform packages are routed sequentially
   fee: fee for the CPMM

OUTPUT:
    objective: the average exchange rate between any pair scaled by demand
'''
def getObj(startingLiquidity, bucket, splitInto, fee=0.003, csv=False):
    objective = 0
    # We could use more of the optimal returns
    for start, goal in itertools.permutations(nodes, 2):
        routingLiquidity = copy.deepcopy(startingLiquidity)
        arrivedLiquidity = 0
        tradesize = weights[start][goal]['buckets'][bucket]['tradesize']/(splitInto*totalLiquidity)
        
        for i in range(splitInto):
            received, routingLiquidity = router(routingLiquidity, start, goal, tradesize, fee)
            arrivedLiquidity += received
        
        if arrivedLiquidity == 0:
            print('explored a disconnected graph.')
            
        objective += weights[start][goal]['buckets'][bucket]['count'] * arrivedLiquidity


        if csv:
            getCSV(startingLiquidity, routingLiquidity, start, goal, bucket)

    return objective



'''
INPUT: 
   liquidity: liquidity levels in the pool graph.
   weights: contains symbols of the tokens
   name: the y axis label

OUTPUT:
    plots and saves liquidity levels of pools without duplicates
'''
def plotLiquidity(liquidity, weights, name):
    plotPool = []
    plotLiquidity = []
    
    for (token1, token2) in liquidity:
        symb1 = weights[token1]['symb']
        symb2 = weights[token2]['symb']
        
        if not(str((symb1, symb2)) in plotPool or str((symb2, symb1)) in plotPool):
            plotPool.append(str((symb1, symb2)))
            plotLiquidity.append(liquidity[(token1, token2)][0])

    plt.bar(plotPool, plotLiquidity)
    plt.xlabel('pools')
    plt.ylabel(name)
    plt.xticks(rotation='vertical')
    plt.ylim(0, 1)
    
    filepath = pathlib.Path('./outputs')
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        
    filename = name +'.pdf'
    file = pathlib.Path(filepath/filename)

    plt.savefig(file, bbox_inches = 'tight')
    plt.show()
    plt.cla()
    plt.clf()
            
    pass



'''
INPUT: 
   startingLiquidity: liquidity levels in the pool graph before any trades
   routingLiquidity: liquidity levels in the pool graph after all trades
   start: the token offered in the trade
   goal: the token traded for
   bucket: indicates the size of the considered trade (see config)

OUTPUT:
    creates a csv-file containing the information for 
        'token1' - first token in the pool
        'token2' - second token in the pool
        'inserted Liquidity' - amount of token1 inserted
        'removed liquidity' - amount of token2 removed
        'original liquidity' - original liquidity level of the (token1, token2) pool
        'demand' - scaled count of how many trades of this type there were
'''
def getCSV(startingLiquidity, routingLiquidity, start, goal, bucket):
    startSymb = weights[start]['symb']
    goalSymb = weights[goal]['symb']
    
    if startingLiquidity == scaledLiquidity:
        path = pathlib.Path('./routing data/old/' + bucket)
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        path = pathlib.Path('./routing data/opt/' + bucket)
        if not os.path.exists(path):
            os.makedirs(path)
        
    filename = 'route_' + str(startSymb) + '-' + str(goalSymb) + '.csv'
    file = pathlib.Path(path/filename)

    
    with open(file, 'w', encoding='UTF8') as f:
        header = ['token1', 'token2', 'inserted Liquidity', 'removed liquidity', 'original liquidity', 'demand']
    
        writer = csv.writer(f)
        writer.writerow(header)
    
        for (token1, token2) in startingLiquidity:
            pool = (token1, token2)
            
            insertedLiquidity = totalLiquidity*(routingLiquidity[pool][0] - startingLiquidity[pool][0])/0.9997
            removedLiquidity = totalLiquidity*(startingLiquidity[pool][1] - routingLiquidity[pool][1])
            originalLiquidity = totalLiquidity*startingLiquidity[pool][0]
            demand = weights[token1][token2]['buckets'][bucket]['count']
            
            if insertedLiquidity > 0:
                data = [weights[token1]['symb'], weights[token2]['symb'], insertedLiquidity, removedLiquidity, originalLiquidity, demand]
            
            else:
                data = [weights[token1]['symb'], weights[token2]['symb'], '', '', originalLiquidity, demand]
            
            writer.writerow(data)
    pass


"""
PROBLEM DATA:

We grab the basic information from the json file and construct
    nodes (list)
    edges (list)
    currentLiquidity (dict)
    scaledLiquidity (dict)
    weights (dict)

currentLiquidity dictionary does not have a pool for each pair.
scaledLiquidity dicitionary scales values in currentLiquidity dictionary
    by the totalLiquidity in all pools together.
    
weights are based on the counted number of trades of a certain size and pair
    and are normalized by the total number of trades of any size and pair
"""

filename = 'config.json'
file = pathlib.Path(filename)

text = open(filename)
config = json.load(text)
    
n = config['size']
weights = config['weights']
reserves = config['reserves']


# Construct the rest of the problemdata
nodes = []
edges = []
currentLiquidity = {}
scaledLiquidity = {}

# Precision is used for rouding scaled liquidity and gradient descent stepsize
precision = 2

# Fee is for the CPMM formula
fee = 0.003

# Split into is how many uniform packages we split trades into
splitInto = 500


# Construct array of nodes and edges
for token1, token2 in itertools.permutations(weights, 2):
    nodes.append(token1)
    nodes.append(token2)
    edges.append((token1, token2))

nodes = list(set(nodes))


# Construct "edge - reserve" dictionary
totalLiquidity = 0
for pool in reserves:
    try:
        currentLiquidity[(reserves[pool]['token0'], reserves[pool]['token1'])][0] += reserves[pool]['reserves']
        currentLiquidity[(reserves[pool]['token0'], reserves[pool]['token1'])][1] += reserves[pool]['reserves']
        currentLiquidity[(reserves[pool]['token1'], reserves[pool]['token0'])][0] += reserves[pool]['reserves']
        currentLiquidity[(reserves[pool]['token1'], reserves[pool]['token0'])][1] += reserves[pool]['reserves']
    except KeyError:
        currentLiquidity[(reserves[pool]['token0'], reserves[pool]['token1'])] = [reserves[pool]['reserves'], reserves[pool]['reserves']]
        currentLiquidity[(reserves[pool]['token1'], reserves[pool]['token0'])] = [reserves[pool]['reserves'], reserves[pool]['reserves']]

    if (reserves[pool]['token0'], reserves[pool]['token1']) in edges:
        totalLiquidity += reserves[pool]['reserves']


for pool in edges:
    if pool in currentLiquidity:
        scaledLiquidity[pool] = [round(currentLiquidity[pool][0]/totalLiquidity, precision), round(currentLiquidity[pool][1]/totalLiquidity, precision)]
    else:
        scaledLiquidity[pool] = [0, 0]


# Construct weights
totTrades = 0
for token1, token2 in itertools.permutations(nodes, 2):
    buckets = weights[token1][token2]['buckets']
    for bucket in buckets:
        totTrades += buckets[bucket]['count']
            
for token1, token2 in itertools.permutations(nodes, 2):
    for bucket in buckets:
        weights[token1][token2]['buckets'][bucket]['count'] /= totTrades
    


"""
START SOLVING

We do a simple gradient descent where we move a 'delta' unit of $$ between
the two pools with the best improvement until we plateau.

"""

delta = 1/(10**precision)
steps = 0

currentObjectives = []
for bucket in buckets:
    currentObjectives.append(getObj(scaledLiquidity, bucket, splitInto, fee))
currentObjective = sum(currentObjectives)
scaledObjective = currentObjective
bestObjective = currentObjective
bestLiquidity = scaledLiquidity.copy()

while bestObjective > currentObjective or steps == 0:
    
    currentObjective = bestObjective
    bestObjective = 0

    for (pool1, pool2) in itertools.permutations(edges, 2):
        liquidity = bestLiquidity.copy()
        (token11, token12) = pool1
        (token21, token22) = pool2
        
        # it might be more efficient to move as soon as there is improvement?
        # we don't have to consider all swaps, its enough to condier swaps (i, i+1)
        if liquidity[pool2][0]:
            liquidity[pool1] = [round(liquidity[pool1][0] + delta, precision), round(liquidity[pool1][1] + delta, precision)]
            liquidity[(token12, token11)] = [round(liquidity[(token12, token11)][0] + delta, precision), round(liquidity[(token12, token11)][1] + delta, precision)]
            liquidity[pool2] = [round(liquidity[pool2][0] - delta, precision), round(liquidity[pool2][1] - delta, precision)]
            liquidity[(token22, token21)] = [round(liquidity[(token22, token21)][0] - delta, precision), round(liquidity[(token22, token21)][1] - delta, precision)]

            objectives = []
            for bucket in buckets:
                objectives.append(getObj(liquidity, bucket, splitInto, fee))
            objective = sum(objectives)
            
            if objective > max(currentObjective, bestObjective):
                bestObjective = objective
                bestLiquidity = liquidity.copy()
    steps += 1



"""
OUTPUT

We plot some things such as:
    -optimal and current routing
    -optimal and current liquidity


"""

# Calculate the average amount of tokens traded for reference
averageInput = 0
for token1 in nodes:
    for token2 in nodes:
        buckets = weights[token1][token2]['buckets']
        for bucket in buckets:
            averageInput += buckets[bucket]['count'] * buckets[bucket]['tradesize']
            

# Save some routings to look at
for bucket in buckets:
    getObj(scaledLiquidity, bucket, splitInto, fee, csv=True)
    getObj(bestLiquidity, bucket, splitInto, fee, csv=True)

plotLiquidity(scaledLiquidity, weights, 'current')
plotLiquidity(bestLiquidity, weights, 'best')


print('average input:', averageInput)

print('old:\t', totalLiquidity * scaledObjective)
print('opt:\t', totalLiquidity * currentObjective, end='\n\n')

print('steps:\t\t', steps)
print('precision:\t', precision, end='\n\n')
print('split into', splitInto, 'trades')

print('tokens:')
for node in nodes:
    print('\t', weights[node]['symb'])

