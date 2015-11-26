#!/usr/bin/python
import json
import argparse as ap
import os, sys
from itertools import combinations
parser = ap.ArgumentParser(description = "Computes follower-bassed similarities from a" \
    " JSON file containing outlet's followers' IDs")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-i", "--in_file", type=ap.FileType("r"), default=sys.stdout, help = \
    "The JSON file containing followers. If not specified, the standard output will be used.")
parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

outlet_sets = dict()

with args.in_file as in_file:
    outlets_followers = json.loads(in_file.read())
    
    for outlet, followers in outlets_followers.iteritems():
        outlet_sets[outlet] = set(followers)


similarities = dict()
for o1, o2 in combinations(outlet_sets.keys(), 2):
    similarities[(o1, o2)] = (float(len(outlet_sets[o1] & outlet_sets[o2])) / \
                              max(len(outlet_sets[o1]), len(outlet_sets[o2])),
                              float(len(outlet_sets[o1] & outlet_sets[o2])))

name_to_index = { v : k for k, v in enumerate(outlet_sets.keys()) }

nodes = [ { "index": name_to_index[name], "name" : name,
            "size":len(followers) } for name, followers in
            outlet_sets.iteritems() ]

links = []

for k, v in similarities.iteritems():

    links.append( { "source": name_to_index[k[0]],
                    "target": name_to_index[k[1]],
                    "value" : v  } )

with args.out_file as out_file:

    if args.pretty:
        out_file.write(json.dumps( \
                { "nodes": nodes, 
                  "links" : links },
            indent = 4, separators = (",", ":" )))
    else:
        out_file.write(json.dumps( \
                { "nodes": nodes, 
                    "links" : links }))
