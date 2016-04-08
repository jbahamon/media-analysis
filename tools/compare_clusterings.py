#!/usr/bin/python
import json, warnings, sys
import argparse as ap
import igraph.clustering as cl
from tabulate import tabulate
warnings.filterwarnings("error")

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

        nodes1 = { n["name"] : n for n in parsed_json_1["nodes"] }
        nodes2 = { n["name"] : n for n in parsed_json_2["nodes"] }

        names = set(nodes1.keys()) & set(nodes2.keys())
   
        membership1 = []
        membership2 = []

        for name in names:
            membership1.append(nodes1[name]["color_value"])
            membership2.append(nodes2[name]["color_value"])
       
        matrix = [ x[:] for x in [[0] * len(set(membership2))] *
                len(set(membership1)) ]

        sizes = { x: sum(1.0 for elem in membership1 if x == elem) for x in set(membership1) }

        for idx, community1 in enumerate(membership1):
            community2 = membership2[idx]
            matrix[community1][community2] += 1
        
        for community1 in set(membership1):
            matrix[community1] = map(lambda x : x * 100.0/sizes[community1],
                    matrix[community1])
            matrix[community1].insert(0, community1)


        headers=["Community", "Unknown %", "Mi Voz %", 
                 "El Mercurio %", "Copesa %"]

with args.out_file as out_file:
        out_file.write(
                tabulate(matrix, headers=headers, tablefmt="latex",
                    floatfmt=".1f")
                .replace('begin{tabular}',r'begin{tabular}{0.9\textwidth}')
                .replace("tabular","tabularx")
                .replace("\\{", "{")
                .replace("\\}","}")
                .replace("texttt","\\texttt") + "\n")

        #   print cl.compare_communities(membership1, membership2,
         #       method="split.join")
        
