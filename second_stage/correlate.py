#!/usr/bin/python

import json
import argparse as ap
import os, sys
from datetime import datetime
from scipy.stats import spearmanr
date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Computes correlations for a " + \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON files to read time series from. If not specified, standard " +\
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " + \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")


args = parser.parse_args()

with args.in_file as json_file:
    with args.out_file as out_file:
        parsed_json = json.loads(json_file.read())

        names = sorted(parsed_json["series"].keys())
        n_names = len(names)
        nodes = [ { \
                  "name": names[i], \
                  "index": i, \
                  "color_value": 0, \
                  "size": 20 } \
                  for i in range(n_names) ] 
        links = []

        for i in range(n_names):
            for j in range(i + 1, n_names):
                spearman = spearmanr(parsed_json["series"][names[i]], \
                            parsed_json["series"][names[j]])
                links.append( { "source": i, "target": j, "value": spearman })


        if args.pretty:
            out_file.write(json.dumps( { \
                "nodes" : nodes, \
                "links" : links }, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps( { \
                "nodes" : nodes, \
                "links" : links } ))


