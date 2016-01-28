#!/usr/bin/python
import json
import argparse as ap
import os, sys
from itertools import combinations
from collections import defaultdict
parser = ap.ArgumentParser(description = "Computes user distribution for a"
        " clustering from a (hardcoded for now) set of database JSON files.")

parser.add_argument("-i", "--clustering_file", type=ap.FileType("r"), default=sys.stdin, help = \
    "An input file with the clustering. If not specified, standard input will be used.")

parser.add_argument("followers", type=ap.FileType("r"), help = \
    "The JSON file containing followers. If not specified, the standard output will be used.")

parser.add_argument("cluster_followers", type=ap.FileType("w"), help = \
    "The file where the cluster sizes (in terms of followers) will be output.")

parser.add_argument("follower_clusters", type=ap.FileType("w"), help = \
    "The file where the cluster-follower histogram will be output.")

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

# how many clusters per follower?

clusters_per_follower = defaultdict(float)
clusters_per_follower_with_zeros = defaultdict(float)

followers_exclusive = 0.0
followers_nonexclusive = 0.0

for follower in all_followers:
    if follower in cluster_followers[0]:
        touched_clusters = sum(follower in followers for cluster, followers in
                cluster_followers.iteritems())
        clusters_per_follower_with_zeros[touched_clusters] += 1.0
        followers_nonexclusive += 1.0

    else:
        touched_clusters = sum(follower in followers for cluster, followers in
                cluster_followers.iteritems() if cluster != 0)
        clusters_per_follower[touched_clusters] += 1.0
        followers_exclusive += 1.0

with args.follower_clusters as follower_clusters_file:
    follower_clusters_file.write("clusters;exclusive;with_zero\n")

    full_range = sorted(list(set(clusters_per_follower.keys()) |
                             set(clusters_per_follower_with_zeros.keys())))

    follower_clusters_file.write("\n".join(("%d;%f;%f" % (c,
        clusters_per_follower[c]/followers_exclusive,
        clusters_per_follower_with_zeros[c]/followers_nonexclusive)) for c in
        full_range) + "\n")

with args.cluster_followers as cluster_followers_file:
    cluster_followers_file.write("ID;followers\n")
    cluster_followers_file.write("\n".join(("%d;%d" % (c, len(n))) for c, n in
        cluster_followers.iteritems()) + "\n")


