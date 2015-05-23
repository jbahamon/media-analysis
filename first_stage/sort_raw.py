#!/usr/bin/python
import sys, operator
from tabulate import tabulate
import math
percentage = float(sys.argv[3]) if len(sys.argv) > 2 else 0.05

count = True if (len(sys.argv) > 4 and sys.argv[4] == "count") else False
with open(sys.argv[1]) as nodes_file:
    nodes_data = nodes_file.readlines()
    names = [ line.rstrip("\r\n") for line in nodes_data ]


d = { name : 0 for name in names }


with open(sys.argv[2]) as edges_file:
    edges_data = edges_file.readlines()
    edges_list = []
    for line in edges_data:
        edge = line.split(" ")
        edges_list.append((int(edge[0]), int(edge[1]), float(edge[2])))
        
    target_length = int(math.ceil(len(edges_data) * percentage))
    edges_list.sort(key = lambda x: -float(x[2]))
    chosen_edges = edges_list[0:target_length]

    for edge in chosen_edges:
        if count:
            d[names[int(edge[0])]] += 1
            d[names[int(edge[1])]] += 1
        else:
            d[names[int(edge[0])]] += float(edge[2])
            d[names[int(edge[1])]] += float(edge[2])

lst = sorted(d.items(), key=operator.itemgetter(1), reverse = True)

for item in lst:
    print str(item[1])
    
sys.stdout.flush()
