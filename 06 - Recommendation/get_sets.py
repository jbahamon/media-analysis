#!/usr/bin/python
import json, warnings, sys 
from collections import defaultdict
import argparse as ap
warnings.filterwarnings("error")

parser = ap.ArgumentParser(description = "Coalesces multiple community"
        "structures into sets for coverage analysis.")

parser.add_argument("files", metavar="file", type=ap.FileType("r"), nargs="+", help = \
    "The JSON files containing communities.")

parser.add_argument("-l", "--labels", type=str, nargs="+", default=[], help = \
    "Labels in order.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()
labels = [None] * len(args.files)

for i, f in enumerate(args.files):
    try:
        labels[i] = args.labels[i]
    except IndexError:
        labels[i] = f.name

outlets = defaultdict(lambda : {label : 0 for label in labels} )
sizes = {}
offset = 0
graphs = dict()

for i, f in enumerate(args.files):
    with f as community_file:
        parsed_json = json.loads(community_file.read())

        graphs[labels[i]] = parsed_json

        nodes = parsed_json["nodes"]
        
        sizes[labels[i]] = (len(set(elem["color_value"] for elem in nodes)))

        for elem in nodes:
            outlets[elem["name"].lower()][labels[i]] = elem["color_value"] 

out_json = {
    "graphs" : graphs,
    "communities" : outlets,
    "outlets" : map(lambda x: x.lower(), outlets.keys()),
    "sizes"   : sizes,
    "labels"  : labels
}

with args.out_file as out_file:
    out_file.write(json.dumps(out_json,
        indent = 2, separators = (",",":")))
