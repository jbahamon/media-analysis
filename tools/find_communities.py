#!/usr/bin/python
import json
import argparse as ap
import os, sys
import igraph as ig
import warnings

warnings.filterwarnings('error')

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


def positive_int(string):
    value = int(string)

    if value < 1:
        msg = "%r should be greater than 0" % string
        raise argparse.ArgumentTypeError(msg)
    return value

parser = ap.ArgumentParser(description = "Computes correlations for a " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read time series from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

parser.add_argument( "min_weight", type=float, default=0, help = \
        "The minimum edge weight to allow.")

parser.add_argument("N", metavar="number_of_communities", type=positive_int, default=sys.stdin, help = \
        "The number of communities to find.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

with args.in_file as json_file:
    with args.out_file as out_file: 
        parsed_json = json.loads(json_file.read())
        
        min_weight = args.min_weight

        G = ig.Graph()
        chosen_nodes = []
        chosen_edges = []

        for edge in parsed_json["links"]:
            if edge["value"] > min_weight:
                chosen_edges.append(edge)
                chosen_nodes.append(edge["source"])
                chosen_nodes.append(edge["target"])

        
        node_to_index = { k:v for (k,v) in enumerate(set(chosen_nodes)) }
        index_to_node = { v:k for (k,v) in enumerate(set(chosen_nodes)) }

        weights = []
        min_weight = min([ edge["value"] for edge in chosen_edges ])

        for i, edge in enumerate(chosen_edges):
            chosen_edges[i] = (index_to_node[edge["source"]],
                    index_to_node[edge["target"]])
            weights.append(edge["value"] - min_weight)

        g = ig.Graph(n = len(node_to_index), edges=chosen_edges, directed=False)
        g.es["weight"] = weights
        clusterings = g.community_fastgreedy(weights = "weight")

        fix_dendrogram(g, clusterings)
        assignments = clusterings.as_clustering(args.N).membership
        for node in parsed_json["nodes"]:
            try:
                node["color_value"] = assignments[index_to_node[node["index"]]] + 1
            except KeyError:
                node["color_value"] = 0

        parsed_json["min_weight"] = min_weight

        if args.pretty:
            out_file.write(json.dumps( parsed_json, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps(parsed_json))




