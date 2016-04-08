#!/usr/bin/python
import json, warnings, sys
import collections
import argparse as ap
from operator import itemgetter
from itertools import product 
warnings.filterwarnings("error")

parser = ap.ArgumentParser(description = "Computes a table of similarities for "
        "a graph with similarities as edges.")

parser.add_argument("similarities", type=ap.FileType("r"), default=sys.stdin, help = \
    "The JSON file containing similarity scores.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-t", "--term", type=str, help = \
    "If there are similarity score for different identifiers, the one to use.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

with args.similarities as similarities:
        parsed_json = json.loads(similarities.read())

        edges = parsed_json["links"]

        if isinstance(edges, collections.Mapping):
            try:
                edges = edges[args.term]
            except KeyError:
                keys = "".join("\t - %s\n" % term for term in edges.keys())
                sys.exit("A similarity score identifier is needed (-t option). The "
                        "following are available: \n" + keys)

        sims = ("%f\t%f\n" % (x["values"][0], x["values"][1]) for x in edges)


        with args.out_file as out_file:
            out_file.writelines(sims)

