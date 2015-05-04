#!/usr/bin/python
import sys, operator
from tabulate import tabulate

threshold = float(sys.argv[3]) if len(sys.argv) > 2 else 0

count = True if (len(sys.argv) > 4 and sys.argv[4] == "count") else False

with open(sys.argv[1]) as nodes_file:
    nodes_data = nodes_file.readlines()
    names = [ line.rstrip("\r\n") for line in nodes_data ]


d = { name : 0 for name in names }
with open(sys.argv[2]) as edges_file:
    edges_data = edges_file.readlines()

    for line in edges_data:
        edge = line.split(" ")

        if threshold == 0 or (float(edge[2]) > 0 and float(edge[2]) > threshold):

            if count:
                d[names[int(edge[0])]] += 1
                d[names[int(edge[1])]] += 1
            else:
                d[names[int(edge[0])]] += float(edge[2])
                d[names[int(edge[1])]] += float(edge[2])




lst = sorted(d.items(), key=operator.itemgetter(1), reverse = True)
print tabulate(lst, tablefmt="grid")
sys.stdout.flush()
