#!/usr/bin/python
import json
import argparse as ap
import os, sys
from itertools import combinations
from collections import defaultdict
from tabulate import tabulate
from numpy.random import choice

parser = ap.ArgumentParser(description = "Computes user distribution for a"
        " clustering from a (hardcoded for now) set of database JSON files.")

parser.add_argument("-i", "--clustering_file", type=ap.FileType("r"), default=sys.stdin, help = \
    "An input file with the clustering. If not specified, standard input will be used.")

parser.add_argument("followers", type=ap.FileType("r"), help = \
    "The JSON file containing followers.")

parser.add_argument("-c", "--cluster_followers", nargs="?", const=sys.stdout, type=ap.FileType("w"), help = \
    "If supplied, the file where the cluster sizes (in terms of followers) will "
    "be output. If the flag is enabled but no file is supplied, standard "
    "output will be used.")

parser.add_argument("-f", "--follower_clusters", nargs="?", const=sys.stdout, type=ap.FileType("w"), help = \
    "If supplied, the file where the cluster-follower histogram will "
    "be output. If the flag is enabled but no file is supplied, standard "
    "output will be used.")

parser.add_argument("-s", "--summary", nargs="?", const=sys.stdout, type=ap.FileType("w"), help = \
    "If supplied, the file where clustering summary will be output. "
    "If the flag is enabled but no file is supplied, standard output will be "
    "used.")

args = parser.parse_args()


outlet_sets = dict()
selected_outlets = []
all_followers = set()

with args.clustering_file as clustering_file:
    parsed_json = json.loads(clustering_file.read())
    selected_outlets = parsed_json["nodes"]
    
with args.followers as in_file:
    outlets_followers = json.loads(in_file.read())
    
    for outlet in selected_outlets:
        outlet_sets[outlet["name"]] = set(outlets_followers[outlet["name"]])
        all_followers |= outlet_sets[outlet["name"]]

# how many followers per cluster?

cluster_followers = defaultdict(set)

for outlet in selected_outlets:
    cluster_followers[outlet["color_value"]] |= outlet_sets[outlet["name"]]

if args.cluster_followers is not None:
    with args.cluster_followers as cluster_followers_file:
        cluster_followers_file.write("ID;followers\n")
        cluster_followers_file.write("\n".join(("%d;%d" % (c, len(n))) for c, n
            in cluster_followers.iteritems()) + "\n")

# how many clusters per follower?

if args.follower_clusters is not None:

    clusters_per_follower = defaultdict(float)
    clusters_per_follower_with_zeros = defaultdict(float)

    followers_exclusive = 0.0
    followers_nonexclusive = 0.0

    for follower in all_followers:
        
        touched_clusters = sum(follower in followers for cluster, followers in
                cluster_followers.iteritems())

        if follower in cluster_followers[0]:
            clusters_per_follower_with_zeros[touched_clusters - 1] += 1.0
            followers_nonexclusive += 1.0

        else:
            clusters_per_follower[touched_clusters] += 1.0
            followers_exclusive += 1.0

    with args.follower_clusters as follower_clusters_file:
        follower_clusters_file.write("N;without_unclustered;has_unclustered\n")

        full_range = sorted(list(set(clusters_per_follower.keys()) |
                                 set(clusters_per_follower_with_zeros.keys())))

        follower_clusters_file.write("\n".join(("%d;%f;%f" % (c,
            clusters_per_follower[c],
            clusters_per_follower_with_zeros[c])) for c in
            full_range) + "\n")

if args.summary is not None:
    with args.summary as summary_file:
        headers = ("ID",
                   "Size", 
                   "Media outlets", 
                   "Audience size", 
                   "")


        clusters = [ (cluster, 
                      [ x["name"] for x in selected_outlets if x["color_value"] == cluster ], 
                      len(followers) ) 
                      for cluster, followers in cluster_followers.iteritems() ]
        
        table = [ [
            cluster,
            len(cluster_outlets),
            ", ".join(map(lambda x: "texttt{%s}" % x, choice(cluster_outlets,
                size=min(len(cluster_outlets), 3), replace=False)))
            + ("..." if len(cluster_outlets) > 3 else ""),
            followers,
            "" ]
            for cluster, cluster_outlets, followers in clusters ]

        summary_file.write(
                tabulate(table, headers=headers, tablefmt="latex")
                .replace('begin{tabular}',r'begin{tabular}{0.9\textwidth}')
                .replace("tabular","tabularx")
                .replace("\\{", "{")
                .replace("\\}","}")
                .replace("texttt","\\texttt") + "\n")

