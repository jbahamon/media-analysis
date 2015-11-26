#!/usr/bin/python
import json, warnings, sys
import argparse as ap
warnings.filterwarnings("error")

parser = ap.ArgumentParser(description = "Remaps indices for d3 c:")

parser.add_argument("-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
    "The JSON input file. If omitted, standard input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

with args.in_file as in_file:
    parsed_json = json.loads(in_file.read())

    old_to_new = { node["index"]:i for i, node in enumerate(parsed_json["nodes"]) }

    for node in parsed_json["nodes"]:
        node["index"] = old_to_new[node["index"]]

    for link in parsed_json["links"]:
        link["source"] = old_to_new[link["source"]]
        link["target"] = old_to_new[link["target"]]

    with args.out_file as out_file:
        if args.pretty:
            out_file.write(json.dumps(
                parsed_json,
                indent = 4, separators = (",", ":")))
        else:
            out_file.write(json.dumps(parsed_json))





