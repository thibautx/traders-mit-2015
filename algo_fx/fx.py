from base import *
import numpy as np
from collections import deque


FX = ['USD', 'CAD', 'EUR', 'CHF', 'JPY']
PAIRS = ['USDCAD', 'EURUSD', 'USDCHF', 'USDJPY', 'EURCAD', 'EURJPY', 'EURCHF', 'CHFJPY']

INDEX = {'USD': 0,
         'CAD': 1,
         'EUR': 2,
         'CHF': 3,
         'JPY': 4}

import math

ARB_OPPS = 0


def initialize(graph, source):
    d = {}
    p = {}
    for node in graph:
        d[node] = float('Inf')
        p[node] = None
    d[source] = 0
    return d, p


def relax(node, neighbour, graph, d, p):
    # If the distance between the node and the neighbour is lower than the one I have now
    if d[neighbour] > d[node] + graph[node][neighbour]:
        # Record this lower distance
        d[neighbour]  = d[node] + graph[node][neighbour]
        p[neighbour] = node


def retrace_negative_loop(p, start):
    arb_loop = [start]
    next_node = start
    while True:
        next_node = p[next_node]
        if next_node not in arb_loop:
            arb_loop.append(next_node)
        else:
            arb_loop.append(next_node)
            arb_loop = arb_loop[arb_loop.index(next_node):]
            return arb_loop


def bellman_ford(graph, source):
    d, p = initialize(graph, source)
    for i in range(len(graph)-1):
        for u in graph:
            for v in graph[u]:
                relax(u, v, graph, d, p)


    # Step 3: check for negative-weight cycles
    for u in graph:
        for v in graph[u]:
        	if d[v] < d[u] + graph[u][v]:
        		return(retrace_negative_loop(p, source))
    return None


def make_graph(graph_data):
    """ (dictionary) -> WgtGraph
    makeGraph takes properly formatted dictionary and returns a WgtGraph
    """
    G = WeightedGraph()
    for key in graph_data.keys():
        tokens = key.split('_')
        # print tokens
        if len(tokens) > 1:
            pair_1 = tokens[0]
            pair_2 = tokens[1]
            G.addEdge(DirectedEdge(pair_1, pair_2, -math.log(graph_data[key])))
    return G


class DirectedEdge:
    """
    DirectedEdge represents a weighted edge. v represents the home vertex. w represents the away vertex
    """
    def __init__(self, v, w, weight):
        self._v = v
        self._w = w
        self._weight = weight

    def fromVertex(self):
        return self._v

    def toVertex(self):
        return self._w

    def weight(self):
        return self._weight


class WeightedGraph:
    """
    WgtGraph is an adjacency list representation of a weighted digraph. A list of of all outgoing
    edges is maintained for each vertex
    """
    def __init__(self):
        self._numEdges = 0
        self._numVertices = 0
        self._adjList = {}

    def addEdge(self, graphEdge):
        if not graphEdge.fromVertex() in self._adjList:
            self._adjList[graphEdge.fromVertex()] = []
            self._numVertices += 1
        self._adjList[graphEdge.fromVertex()].append(graphEdge)

        self._numEdges += 1

    def neighbors(self, vertex):
        return self._adjList.get(vertex)

    def vertices(self):
        return self._adjList.keys()

    def numVertices(self):
        return self._numVertices

    def adjList(self):
        return self._adjList

    def __str__(self):
        toString = ""
        for vertex in self.vertices():
            toString += vertex + "\n"
            for edge in self.neighbors(vertex):
                toString += str(edge) + "\n"
        return toString


class WgtDirectedCycle:
    """Finds a directed cycle in a weighted digraph"""
    def __init__(self, G):
        self._explored = set()
        self._edgeTo = {}
        self._onStack = set()
        self._cycle = []
        for vertex in G.vertices():
            if vertex not in self._explored: self.dfs(G, vertex)

    def dfs(self, G, vertex):
        self._onStack.add(vertex)
        self._explored.add(vertex)

        if vertex in G.adjList():
            for edge in G.neighbors(vertex):
                toVertex = edge.toVertex()

                if self._cycle != []:
                    return

                elif toVertex not in self._explored:
                    self._edgeTo[toVertex] = edge
                    self.dfs(G, toVertex)

                elif toVertex in self._onStack:
                    while edge.fromVertex() != toVertex:
                        self._cycle.append(edge)
                        edge = self._edgeTo[edge.fromVertex()]
                    self._cycle.append(edge)

        self._onStack.remove(vertex)

    def hasCycle(self):
        """ () -> bool
        hasCycle returns true if a directed cycle found
        """
        return self._cycle != []

    def cycle(self):
        """ () -> list """
        return self._cycle


class BellmanFord:

    def __init__(self, G, source):
        self._distTo = dict([(vertex, float('inf')) for vertex in G.vertices()])
        self._distTo[source] = 0
        self._edgeTo = {}
        self._onQueue = dict([(vertex, False) for vertex in G.vertices()])
        self._cycle = []
        self._count = 1

        self._q = deque()
        self._q.append(source)
        self._onQueue[source] = True

        while(len(self._q) > 0 and not self.has_negative_cycle()):
            vertex = self._q.popleft()
            self._onQueue[vertex] = False
            self.relax(G, vertex)

    def relax(self, G, vertex):
        epsilon = 0.0001
        for edge in G.neighbors(vertex):
            toVertex = edge.toVertex()
            if self._distTo[toVertex] > self._distTo[vertex] + edge.weight() + epsilon:
                self._distTo[toVertex] = self._distTo[vertex] + edge.weight()
                self._edgeTo[toVertex] = edge
                if not self._onQueue[toVertex]:
                    self._q.append(toVertex)
                    self._onQueue[toVertex] = True
            self._count += 1
            if self._count % 2*G.numVertices() == 0:
                self.find_negative_cycle()

    def find_negative_cycle(self):
        spt = WeightedGraph()

        for edge in self._edgeTo.values():
            spt.addEdge(edge)

        finder = WgtDirectedCycle(spt)
        self._cycle = finder.cycle()

    def has_negative_cycle(self):
        """ () -> bool
        hasNegativeCycle returns true if cycle was found, false otherwise
        """
        return self._cycle != []

    def get_cycle(self):
        """ () -> list """
        return self._cycle


def normalize(graph):
    arbitrage_g = {}
    for k, neighbors in graph.iteritems():
        arbitrage_g[k] = {}
        for m, weights in neighbors.iteritems():
            arbitrage_g[k][m] = (-1) * math.log(weights)
    return arbitrage_g


class FXBot(BaseBot):

    def __init__(self):
        super(FXBot, self).__init__()

    def arbitrage(self):
        orders = []
        graph_data = {}
        for pair, value in self.topBid.iteritems():
            pair_1 = pair[:3]  # currency 1
            pair_2 = pair[3:]  # currency 2
            if pair_1 not in graph_data.keys():
                graph_data[pair_1] = {}
            if pair_2 not in graph_data.keys():
                graph_data[pair_2] = {}
            graph_data[pair_1+'_'+pair_2] = float(value)
            graph_data[pair_2+'_'+pair_1] = 1/float(value)

        G = make_graph(graph_data)
        bf = BellmanFord(G, G.vertices()[0])
        if bf.has_negative_cycle():
            result = bf.get_cycle()
            print "Start with 100 units {0}".format(result[-1].fromVertex())
            balance = 100
            while result:

                edge = result.pop()
                key = edge.fromVertex() + "_" + edge.toVertex()
                balance = balance * graph_data[key]
                print "{0} to {1} @ {2} = {3:.2f} {4}".format(edge.fromVertex(), edge.toVertex(), graph_data[key], balance, edge.toVertex())

        return orders

    def update_state(self, msg):
        super(FXBot, self).update_state(msg)

    def process(self, msg):
        self.started = True
        super(FXBot, self).process(msg)
        orders = []
        if (self.started and time() - self.lastActionTime >
                self.options.get('delay')):
            self.lastActionTime = time()

            # XXX: Your strategies go here
            # examples:
            # orders.extend(self.marketMake())
            # orders.extend(self.momentum())
            orders.extend(self.arbitrage())
            # orders.extend(self.arbitrage())

        if len(orders) > 0:
            action = {
                'message_type': 'MODIFY ORDERS',
                'orders': orders,
            }
            return dumps(action)
        return None

if __name__ == '__main__':
    bot = FXBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)
