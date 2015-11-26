#!/usr/bin/python
import json, warnings, sys
import argparse as ap
from operator import itemgetter
from itertools import product 
warnings.filterwarnings("error")

def jaccard(nodes1, nodes2, i, j):
    A = set(x["name"] for x in nodes1 if x["color_value"] == i)
    B = set(x["name"] for x in nodes2 if x["color_value"] == j)
    
    return float(len(A & B)) / float(len(A | B))

parser = ap.ArgumentParser(description = "Computes jaccard similarities for two" 
"clusterings")

parser.add_argument("file1", type=ap.FileType("r"), default=sys.stdin, help = \
    "The first JSON input file.")

parser.add_argument("file2", type=ap.FileType("r"), default=sys.stdin, help = \
    "The second JSON input file.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

with args.file1 as file1:
    with args.file2 as file2:
        parsed_json_1 = json.loads(file1.read())
        parsed_json_2 = json.loads(file2.read())

        nodes1 = parsed_json_1["nodes"]
        nodes2 = parsed_json_2["nodes"]
    
        ids1 = set(x["color_value"] for x in nodes1)
        ids2 = set(x["color_value"] for x in nodes2)


        with args.out_file as out_file:
            scores = sorted( [ (i, j, jaccard(nodes1, nodes2, i, j)) for i, j in
                    product(ids1,ids2) ] , key=itemgetter(2), reverse=True)

            matchings = []

            while len(matchings) < min(len(ids1), len(ids2)):
                best_matching = scores[0]

                matchings.append(best_matching)
                scores = [ x for x in scores if x[0] != best_matching[0] and
                                                x[1] != best_matching[1] ]


            for matching in matchings:
                out_file.write("%d - %d : %f\n" % matching)
