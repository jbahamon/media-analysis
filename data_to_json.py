#!/usr/bin/python
import argparse as ap
import sys

def percent(string):
    value = float(string)
    
    if value > 100 or value < 0:
        msg = "%r should be between 0 and 100" % string
        raise argparse.ArgumentTypeError(msg)
    return value

parser = ap.ArgumentParser(description = "Adapts similarity measures to a json file for visualization.")

parser.add_argument("nodes_file", type=ap.FileType("r"), help = \
    "A file with names for nodes. If -f is used, flows will be parsed from this" + \
    "file too.")

parser.add_argument("edges_file", type=ap.FileType("r"), help = \
    "A file with similarities for each pair of nodes, to be used as edge weights.")

parser.add_argument("-o", "--out_file",type=ap.FileType("w"), default=sys.stdout,  help = \
    "The output file. If none is specified, the json file will be written to the standard output.")

parser.add_argument("-p", "--percentage", type=percent, default=5.0, help = "Percentage of the strongest edges to be considered, in the [0, 100] range (default: %(default)s)")

parser.add_argument("-i", "--influences", action="store_true", help = "Use this if the node file contains a measure for its influence next to each name.")

parser.add_argument("-w", "--weighted", action="store_true", help = "Use weighted degree to color nodes")

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
           
            json_file.write("{\n \"nodes\" :[\n")

            if args.influences:
		nodes = ",\n".join([ ( "{\"name\":\"%s\", \"degree\": %f, \"size\": %d }" % \
                    ( line.split(" ")[0].rstrip("\r\n"), \
                      G.degree(ind, weight = ("weight" if args.weighted else None)), \
                      int(line.split(" ")[1].rstrip("\r\n")) ) ) \
                      for ind, line in enumerate(nodes_data) ])
            else:
                nodes = ",\n".join([ ( "{\"name\":\"%s\", \"degree\": %f, \"size\": 5 }" % \
                    ( line.split(" ")[0].rstrip("\r\n"), \
                      G.degree(ind, weight = ("weight" if args.weighted else None)))) \
                      for ind, line in enumerate(nodes_data) ])

            json_file.write(nodes)
            json_file.write( "],\n\"links\" :[")

            chosen_list = [] 

            for edge in chosen_edges:
                chosen_list.append("{\"source\": %d, \"target\": %d, \"value\": %f }" % (edge[0], edge[1], (edge[2] if args.weighted else 1)))
            json_file.write(",\n".join(reversed(chosen_list)))
            json_file.write("],\n")

            json_file.write("\"max_degree\" : %f," % \
                max( G.degree(range(len(nodes_data)), weight = ("weight" if args.weighted else None)).values() ))

            json_file.write("\"min_degree\" : %f," % \
                min( G.degree(range(len(nodes_data)), weight = ("weight" if args.weighted else None)).values() ))

            if args.influences:        
                json_file.write("\"min_influence\": %d," % min([ int(line.split(" ")[1].rstrip("\r\n")) for ind, line in enumerate(nodes_data) ]))
            
                json_file.write("\"max_influence\": %d," % max([ int(line.split(" ")[1].rstrip("\r\n")) for ind, line in enumerate(nodes_data) ]))
            else:

                json_file.write("\"max_influence\": 5,")
                json_file.write("\"min_influence\": 5,") 
            
            json_file.write("\"max_similarity\": %f," % max( [ x[2] for x in chosen_edges ] ))
            json_file.write("\"min_similarity\": %f" % min( [ x[2] for x in chosen_edges ] ))

            json_file.write("}")
