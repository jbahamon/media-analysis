#!/usr/bin/python
import argparse as ap
import sys

def fix_dendrogram(graph, cl):
    already_merged = set()
    for merge in cl.merges:
        already_merged.update(merge)

    num_dendrogram_nodes = graph.vcount() + len(cl.merges)
    not_merged_yet = sorted(set(xrange(num_dendrogram_nodes)) - already_merged)
    if len(not_merged_yet) < 2:
        return

    v1, v2 = not_merged_yet[:2]
    cl._merges.append((v1, v2))
    del not_merged_yet[:2]

    missing_nodes = xrange(num_dendrogram_nodes,
            num_dendrogram_nodes + len(not_merged_yet))
    cl._merges.extend(zip(not_merged_yet, missing_nodes))
    cl._nmerges = graph.vcount()-1
    cl._nitems = graph.vcount()

def cluster(G, nodes, N):

    import igraph as ig
    import numpy as np
    
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
    
    clusterings = g.community_fastgreedy(weights = "weight")

    fix_dendrogram(g, clusterings)

    return clusterings.as_clustering(N).membership


def positive_int(string):
    value = int(string)

    if value < 1:
        msg = "%r should be greater than 0" % string
        raise argparse.ArgumentTypeError(msg)
    return value

def percent(string):
    value = float(string)
    
    if value > 100 or value < 0:
        msg = "%r should be between 0 and 100" % string
        raise argparse.ArgumentTypeError(msg)
    return value

parser = ap.ArgumentParser(description = "Adapts similarity measures to a json file for visualization.")

parser.add_argument("nodes_file", type=ap.FileType("r"), help = \
    "A file with names for nodes. If -f is used, flows will be parsed from this " + \
    "file too.")

parser.add_argument("edges_file", type=ap.FileType("r"), help = \
    "A file with similarities for each pair of nodes, to be used as edge weights.")

parser.add_argument("-o", "--out_file",type=ap.FileType("w"), default=sys.stdout,  help = \
    "The output file. If none is specified, the json file will be written to the standard output.")

parser.add_argument("-p", "--percentage", type=percent, default=5.0, help = "Percentage of the strongest edges to be considered, in the [0, 100] range (default: %(default)s)")

parser.add_argument("-i", "--influences", action="store_true", help = "Use this if the node file contains a measure for its influence next to each name, for node size.")

coloring = parser.add_mutually_exclusive_group(required=False)

coloring.add_argument("-c", "--cluster", metavar="N", type=positive_int, help = "Cluster nodes into N groups to color them.")
coloring.add_argument("-d", "--degree", type=str, choices=["weights", "links"], default="degrees", help = "Use degree to color nodes. 'weights' (default) uses weighted degree; 'links' only counts the number of edges.")

args = parser.parse_args()

percentage = args.percentage/100.0

import math
import networkx as nx

with args.out_file as json_file:
    with args.edges_file as edges_file:
        with args.nodes_file as nodes_file:
        
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
            weights = [ x[2] for x in chosen_edges ]


            if args.cluster:
                groups = cluster(G, [x.split(" ")[0].strip() for x in nodes_data ] if args.influences else [x.strip() for x in nodes_data], args.cluster )
            elif args.degree is None:
                groups = [0] * len(nodes_data)
            elif args.degree == "weights":
                groups = [ G.degree(ind, weight = "weight") for ind, line in enumerate(nodes_data) ]
            elif args.degree == "links":
                groups = [ G.degree(ind, weight = None) for ind, line in enumerate(nodes_data) ]
 
            json_file.write("{\n \"nodes\" :[\n")

            if args.influences:
		nodes = ",\n".join([ ( "{\"name\":\"%s\", \"color_value\": %f, \"size\": %d }" % \
                    ( line.split(" ")[0].rstrip("\r\n"), \
                      groups[ind], \
                      int(line.split(" ")[1].rstrip("\r\n")) ) ) \
                      for ind, line in enumerate(nodes_data) ])
            else:
                nodes = ",\n".join([ ( "{\"name\":\"%s\", \"color_value\": %f, \"size\": 5 }" % \
                    ( line.split(" ")[0].rstrip("\r\n"), \
                      groups[ind] )) \
                      for ind, line in enumerate(nodes_data) ])

            json_file.write(nodes)
            json_file.write( "],\n\"links\" :[")

            chosen_list = [] 

            for edge in chosen_edges:
                chosen_list.append("{\"source\": %d, \"target\": %d, \"value\": %f }" % (edge[0], edge[1], (edge[2] if args.degree and args.degree == "weights" else 1)))
            json_file.write(",\n".join(reversed(chosen_list)))
            json_file.write("],\n")

            json_file.write("\"max_degree\" : %f," % \
                max( G.degree(range(len(nodes_data)), weight = ("weight" if args.degree == "weights" else None)).values() ))

            json_file.write("\"min_degree\" : %f," % \
                min( G.degree(range(len(nodes_data)), weight = ("weight" if args.degree == "weights" else None)).values() ))

            if args.influences:        
                json_file.write("\"min_influence\": %d," % min([ int(line.split(" ")[1].rstrip("\r\n")) for ind, line in enumerate(nodes_data) ]))
            
                json_file.write("\"max_influence\": %d," % max([ int(line.split(" ")[1].rstrip("\r\n")) for ind, line in enumerate(nodes_data) ]))
            else:

                json_file.write("\"max_influence\": 5,")
                json_file.write("\"min_influence\": 5,") 
            
            json_file.write("\"max_similarity\": %f," % max( [ x[2] for x in chosen_edges ] ))
            json_file.write("\"min_similarity\": %f," % min( [ x[2] for x in chosen_edges ] ))
            
            json_file.write("\"color\": " + ("\"clusters\"" if args.cluster else "\"degree\""))

            json_file.write("}")
