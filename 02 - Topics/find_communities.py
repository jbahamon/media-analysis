#!/usr/bin/python
import json
import argparse as ap
import os, sys
import igraph as ig
import warnings
import operator
from collections import defaultdict
from math import isinf, log, sqrt
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
        raise ap.ArgumentTypeError(msg)
    return value

parser = ap.ArgumentParser(description = "Clusters communities for a" \
    "JSON file containing similarities as edge weights")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read graph data from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

parser.add_argument( "-s", "--min_similarity", type=float,default=0, help = \
        "The minimum similarity to allow.")

parser.add_argument( "-kl", "--min_kurtosis", type=float,default=float("-inf"), help = \
        "The minimum kurtosis to allow.")

parser.add_argument( "-kh", "--max_kurtosis", type=float, default=float("inf"), help = \
        "The maximum kurtosis to allow.")

parser.add_argument("N", metavar="number_of_communities", type=positive_int, default=sys.stdin, help = \
        "The number of communities to find.")

parser.add_argument("-r", "--reverse_frequencies", action="store_true",
        help = "Reverse topic frequencies for top keywords.")

parser.add_argument("-c", "--count_keywords", type=int, default=0, help = \
        "The number of top keywords per community. If this parameter is "
        "omitted or passed a nonpositive integer, keyword count will not be "
        "performed.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

with args.in_file as json_file:
    with args.out_file as out_file: 
        parsed_json = json.loads(json_file.read())
        
        min_similarity = args.min_similarity
        max_kurtosis   = args.max_kurtosis
        min_kurtosis   = args.min_kurtosis

        G = ig.Graph()
        chosen_nodes = []
        chosen_edges = []

        for edge in parsed_json["links"]:
            if edge["values"][0] > min_similarity and \
                    edge["values"][1] >= min_kurtosis and\
                    edge["values"][1] < max_kurtosis:
                    chosen_edges.append(edge)
                    chosen_nodes.append(edge["source"])
                    chosen_nodes.append(edge["target"])

       
        if isinf(max_kurtosis):
            max_kurtosis = max(edge["values"][1] for edge in
                    parsed_json["links"])
       
        if isinf(min_kurtosis):
            min_kurtosis = min(edge["values"][1] for edge in
                    parsed_json["links"])

        node_to_index = { k:v for (k,v) in enumerate(set(chosen_nodes)) }
        index_to_node = { v:k for (k,v) in enumerate(set(chosen_nodes)) }

        weights = []
        min_weight = min([ edge["values"][0] for edge in chosen_edges ])
        for i, edge in enumerate(chosen_edges):
            chosen_edges[i] = (index_to_node[edge["source"]],
                    index_to_node[edge["target"]])
            weights.append(edge["values"][0] - min_weight)

        g = ig.Graph(n = len(node_to_index), edges=chosen_edges, directed=False)
        g.es["weight"] = weights
        clusterings = g.community_fastgreedy(weights = "weight")

        clusterings = clusterings.as_clustering(args.N)
        assignments = clusterings.membership
        
        for node in parsed_json["nodes"]:
            try:
                node["color_value"] = assignments[index_to_node[node["index"]]] + 1
            except KeyError:
                node["color_value"] = 0

        
        if args.count_keywords > 0:
            community_keyword_counts = defaultdict(lambda : defaultdict(int))

            totals = defaultdict(float)
            norms = defaultdict(float)

            for node in parsed_json["nodes"]:
                for k, v in parsed_json["keyword_count"][node["name"]].iteritems():
                    norms[node["color_value"]] += v*v

            for k, v in norms.iteritems():
                norms[k] = sqrt(v)

            for node in parsed_json["nodes"]:
                try:
                    for k, v in parsed_json["keyword_count"][node["name"]].iteritems():
                        community_keyword_counts[node["color_value"]][k] += v
                        if v > 0:
                            totals[k] += v/norms[node["color_value"]]
                except KeyError:
                    pass

            N = float(args.N + 1)

            for community, kw_list in community_keyword_counts.iteritems():
                for kw in kw_list.keys():
                    if totals[kw] == 0:
                        kw_list[kw] = 0
                    else:
                        kw_list[kw] *= log(N/(totals[kw]))
                
            for k, v in community_keyword_counts.iteritems():
                vals = sorted(v.iteritems(), key =
                        operator.itemgetter(1), reverse = True)[:args.count_keywords]

                max_val = max(map(operator.itemgetter(1), vals))
                min_val = min(map(operator.itemgetter(1), vals))

                if min_val == max_val:
                    max_val += 0.01

                community_keyword_counts[k] = dict(map(lambda x:
                    (x[0], (x[1] - min_val)/(max_val - min_val)), vals ))

            parsed_json["keyword_count"] = (community_keyword_counts)

        parsed_json["links"] = parsed_json["links"]
        parsed_json["min_similarity"] = min_similarity
        parsed_json["min_kurtosis"] = min_kurtosis
        parsed_json["max_kurtosis"] = max_kurtosis

        
        if args.pretty:
            out_file.write(json.dumps( parsed_json, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps(parsed_json))




