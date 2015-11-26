#!/usr/bin/python
import sys
import math
import networkx as nx
import igraph as ig
import numpy as np

divisions = int(sys.argv[3])

assortativities = []
clustering = []
closeness = []

with open(sys.argv[1]) as nodes_file:
    nodes_data = nodes_file.readlines()

with open(sys.argv[2]) as edges_file:
    edges_data = edges_file.readlines()
    edges_list = []
    
    for line in edges_data:
        edge = line.split(" ")
        edges_list.append((int(edge[0]), int(edge[1]), float(edge[2])))

    edges_list.sort(key = lambda x:
        -float(x[2]))


division_width = len(edges_data) * 100.0/float(divisions)

for i in range(divisions):
    G = nx.Graph()
    G.add_nodes_from(range(len(nodes_data)))
    target_length = int(math.ceil(division_width * (i + 1)))
    chosen_edges = edges_list[0:target_length]
    G.add_weighted_edges_from(chosen_edges)

assortativities.append(nx.degree_assortativity_coefficient(G))
clustering.append(nx.average_clustering(G))
closeness.append(nx.closeness_centrality(G))

print " ".join([ str(i) for i in assortativities])
print " ".join([ str(i) for i in clustering])
print " ".join([ str(i) for i in closeness])

