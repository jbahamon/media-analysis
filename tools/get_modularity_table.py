#!/usr/bin/python
import json
import argparse as ap
import os, sys
import igraph as ig
import warnings
import collections

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

parser = ap.ArgumentParser(description = "Computes a table of modularities and "
    "conductance values for a JSON file containing graph vertices and edges.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read a graph from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

parser.add_argument("-t", "--term", type=str, help = \
    "If there are similarity scores for different identifiers, the one to use.")
parser.add_argument( "-sl", "--min_sensitivity",
        type=float, default=float("-Inf"), nargs="?", 
        help ="The minimum sensitivity to allow.")

parser.add_argument( "-sh", "--max_sensitivity", 
        type=float, default=float("Inf"), nargs="?",
        help = "The maximum sensitivity to allow.")

parser.add_argument( "min_weight", type=float, default=0, help = \
        "The minimum edge weight to allow.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)


def find_conductance(graph, clustering, weights):

    conductance = 0

    all_edges = sum(graph.strength(weights="weight"))
#extract the nodes of interest from graph
    for nodes in clustering:

#get vertex set and subgraph set to compare differences
        vertices = graph.vs.select(nodes)
        subgraph = graph.subgraph(nodes)

#get relevant data from vertex set and subgraph
        edges_inside = float(sum(subgraph.strength(weights="weight")))
        total_edges = float(sum(graph.strength(vertices, weights="weight")))

        edges_border = total_edges - edges_inside

        if edges_border == 0:
            continue
        
        adherence = float(min(total_edges, all_edges - edges_inside))

        conductance = max(conductance, 
                         edges_border / adherence )


    return conductance

with args.in_file as json_file:
    with args.out_file as out_file: 
        parsed_json = json.loads(json_file.read())
        
        min_weight = args.min_weight

        G = ig.Graph()
        chosen_nodes = []
        chosen_edges = []
        edges = parsed_json["links"]

        if isinstance(edges, collections.Mapping):
            try:
                edges = edges[args.term]
            except KeyError:
                keys = "".join("\t - %s\n" % term for term in edges.keys())
                sys.exit("A similarity score identifier is needed (-t option). The "
                        "following are available: \n" + keys)

        min_sensitivity = args.min_sensitivity
        max_sensitivity = args.max_sensitivity

        if min_sensitivity is not None and not max_sensitivity is None:
            max_sensitivity = float("Inf")

        if min_sensitivity is not None and not max_sensitivity is None:
            max_sensitivity = float("Inf")
        
        if min_sensitivity is not None and max_sensitivity is not None:
            for edge in edges:
                if (edge["values"][0] > min_weight and
                    edge["values"][1] > min_sensitivity and
                    edge["values"][1] < max_sensitivity):
                    chosen_edges.append(edge)
                    chosen_nodes.append(edge["source"])
                    chosen_nodes.append(edge["target"])
        else:
            for edge in edges:
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

        print "n\tModularity\tConductance\n"

        for i in xrange(1,20):

            clustering = clusterings.as_clustering(i)

            print "%d\t%f\t%f" % (i, g.modularity(clustering, weights),
                    find_conductance(g, clustering, weights))
