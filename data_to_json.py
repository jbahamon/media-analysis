#!/usr/bin/python
import sys
import math
import networkx as nx
import igraph as ig
import numpy as np

percentage = float(sys.argv[3])

with open(sys.argv[4], "w") as json_file:
    with open(sys.argv[2]) as edges_file:
        with open(sys.argv[1]) as nodes_file:
        
            nodes_data = nodes_file.readlines()
            edges_data = edges_file.readlines()

            G = nx.Graph()
            G.add_nodes_from(range(len(nodes_data)))

            edges_list = []

            for line in edges_data:
                edge = line.split(" ")
                edges_list.append((int(edge[0]), int(edge[1]), float(edge[2])))

            edges_list.sort(key = lambda x: -float(x[2]))

            target_length = int(math.ceil(len(edges_data) * percentage))
            chosen_edges = edges_list[0:target_length]
            G.add_weighted_edges_from(chosen_edges)
            
            
            json_file.write("{\n \"nodes\" :[\n")
            nodes = ",\n".join([ ("{\"name\":\"" + line.rstrip("\r\n") + \
                    "\",\"degree\":" + str(int(G.degree(ind))) + "}") for ind, line
                        in enumerate(nodes_data) ])
            json_file.write(nodes)
            json_file.write( "],\n\"links\" :[")

            chosen_list = [] 

            for edge in chosen_edges:
                chosen_list.append("{\"source\":" + str(edge[0]) + ",\"target\":" + \
                                    str(edge[1]) + ",\"value\":" + "1" + "}")
            json_file.write(",\n".join(chosen_list))
            json_file.write("]}")
