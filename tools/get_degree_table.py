#!/usr/bin/python
import json, warnings, sys
import argparse as ap
from operator import itemgetter
from itertools import product 
warnings.filterwarnings("error")

parser = ap.ArgumentParser(description = "Computes a list of degrees for a "
        "similarity graph.") 

parser.add_argument("similarities", type=ap.FileType("r"), default=sys.stdin, help = \
    "The JSON file containing similarity scores.")

parser.add_argument("-t", "--threshold", type=float, default=0,help="Minimum "
        "similarity score to consider. Defaults to 0.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

with args.similarities as similarities:
        parsed_json = json.loads(similarities.read())

        indices = [ node["index"] for node in parsed_json["nodes"] ]

        edges = parsed_json["links"]

        degrees = ("%f\n" % sum(edge["value"] > args.threshold and 
                        (edge["source"] == index or edge["target"] == index) 
                        for edge in edges)
                    for index in indices )



        with args.out_file as out_file:
            out_file.writelines(degrees)

