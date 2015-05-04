#!/usr/bin/python
import sys
import math
import networkx as nx
import igraph as ig
import numpy as np
G = nx.Graph()

percentage = float(sys.argv[3])
percentage = float(sys.argv[3])

print "============================================="
print "Full Graph"
print "============================================="
with open(sys.argv[1]) as nodes_file:
    nodes_data = nodes_file.readlines()
    G.add_nodes_from(range(len(nodes_data)))

edges_list = []
with open(sys.argv[2]) as edges_file:
    edges_data = edges_file.readlines()
    target_length = int(math.ceil(len(edges_data) * percentage))

    for line in edges_data:
        edge = line.split(" ")
        edges_list.append((int(edge[0]), int(edge[1]), float(edge[2])))

    edges_list.sort(key = lambda x:
            -float(x[2]))
    chosen_edges = edges_list[0:target_length]

    G.add_weighted_edges_from(chosen_edges)


print "Degree histogram:"
print nx.degree_histogram(G)
print nx.info(G)

print "Closeness Centrality: " + \
    str(nx.algorithms.centrality.closeness_centrality(G))

print "Average Clustering Coefficient: " + str(nx.average_clustering(G))

print "Assortativity: " + str(nx.degree_assortativity_coefficient(G))

a_numpy = np.triu(nx.to_numpy_matrix(G))
# get the row, col indices of the non-zero elements in your adjacency matrix
conn_indices = np.where(a_numpy)

conn_indices = [ conn.tolist()[0] for conn in conn_indices ]

# get the weights corresponding to these indices
weights = a_numpy[conn_indices].tolist()[0]
# a sequence of (i, j) tuples, each corresponding to an edge from i -> j
edges = zip(*conn_indices)
# initialize the graph from the edge sequence
g = ig.Graph(n=len(nodes_data), edges=edges, directed=False)

# assign node names and weights to be attributes of the vertices and edges
# respectively
g.vs['label'] = nodes_data
g.es['weight'] = weights

# I will also assign the weights to the 'width' attribute of the edges. this
# means that igraph.plot will set the line thicknesses according to the edge
# weights
g.es['width'] = weights


print g.summary(verbosity=1)
print "Betweenness: " + str(g.betweenness())
print "Number of cliques: " + str(g.clique_number())
print "Girth: " + str(g.girth())
print "Independence number: " + str(g.independence_number())
print "Path Length Histogram: " + \
    str(g.path_length_hist(directed=False))
print "Transitivity: " + \
    str(g.transitivity_undirected(mode="zero"))
print "Average Local Transitivity: " + \
    str(g.transitivity_avglocal_undirected(mode="zero"))
if g.articulation_points():
    print "Articulation points: " + ", ".join([ nodes_data[j].strip() for j in g.articulation_points() ])

print weights

print "\n\n\n"

ig.plot(g.community_fastgreedy( weights = [ int(i * 1000) for i in  weights ]))
ig.plot(g.community_edge_betweenness(directed = False))

subgraphs = g.decompose(mode=ig.WEAK, minelements=2)
n = 1
for subgraph in subgraphs:

    print "============================================="
    print "Connected Component n. " + str(n)
    print "============================================="

    n += 1

    print subgraph.summary(verbosity=1)
    print "Betweenness: " + str(subgraph.betweenness())
    print "Number of cliques: " + str(subgraph.clique_number())
    print "Girth: " + str(subgraph.girth())
    print "Independence number: " + str(subgraph.independence_number())
    print "Path Length Histogram: " + \
        str(subgraph.path_length_hist(directed=False))
    print "Transitivity: " + \
        str(subgraph.transitivity_undirected(mode="zero"))
    print "Average Local Transitivity: " + \
        str(subgraph.transitivity_avglocal_undirected(mode="zero"))
    if subgraph.articulation_points():
        print "Articulation points: " + ", ".join([ nodes_data[j].strip() for j in subgraph.articulation_points() ])
    ig.plot(subgraph.community_walktrap( weights = [ int(i * 1000) for i in  weights ]))

