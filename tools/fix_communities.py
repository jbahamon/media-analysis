#!/usr/bin/python
import json
import argparse as ap
import os, sys

import warnings
warnings.filterwarnings('error')

parser = ap.ArgumentParser(description = "Computes correlations for a " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read time series from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument( "min_weight", type=float, default=0, help = \
        "The minimum edge weight to allow.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

min_weight = args.min_weight

with args.in_file as json_file:
    with args.out_file as out_file:
        parsed_json = json.loads(json_file.read())
        
        new_links = []

        for edge in parsed_json["links"]:
            if edge["value"] > min_weight:
                new_links.append(edge)

        parsed_json["links"] = new_links
        if args.pretty:
            out_file.write(json.dumps( parsed_json, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps(parsed_json))


