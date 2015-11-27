#!/usr/bin/python
import json
import argparse as ap
import os, sys
import igraph as ig
import warnings
from itertools import combinations, chain
import codecs
from fuzzywuzzy import fuzz
from unidecode import unidecode
def clean_name(name):
    return unidecode(name.replace(" ","")).lower()

warnings.filterwarnings('error')

parser = ap.ArgumentParser(description = "Computes ownership similarities " \
    "from a (hardcoded for now) set of database JSON files.")

parser.add_argument("-i", "--in_file", type=ap.FileType("r"), default=None, help = \
    "An input file to choose names from. If not specified, all names will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

OUTLET_FILES     = [ "canaltv.json", "escrito.json", "mediodigital.json", "radio.json" ]
OWNERS_FILE      = "propietario.json" 
GROUPS_FILE      = "grupo.json"
TV_OWNERS_FILE   = "canaltv_propietario.json"
SOCIETIES_FILE   = "sociedad.json"


# Necesito una lista de todo  
nodes = []
types = [ " (Canal)", " (Escrito)", " (Digital)", " (Radio)" ]
outlets = [ dict(), dict(), dict(), dict() ]
i = 0 

for f, d, t  in zip(OUTLET_FILES, outlets, types):
    with codecs.open(f, "r", "utf-8") as json_file:
        for outlet in json.loads(json_file.read()):
            outlet["medio"] = unidecode(outlet["medio"]).decode( 'unicode-escape' )
            outlet["t"] = t
            outlet["node_id"] = i
            d[outlet["id"]] = outlet
            nodes.append(outlet)
            i += 1

owners = dict()
with codecs.open(OWNERS_FILE, "r", "utf-8") as json_file:
    for owner in json.loads(json_file.read()):
        owner["node_id"] = i
        owners[owner["id"]] = owner
        nodes.append(owner)
        i += 1
groups = dict()
with codecs.open(GROUPS_FILE, "r", "utf-8") as json_file:
    for group in json.loads(json_file.read()):
        group["node_id"] = i
        groups[group["id"]] = group
        nodes.append(group)
        i += 1

societies = dict()
with codecs.open(SOCIETIES_FILE, "r", "utf-8") as json_file:
    for society in json.loads(json_file.read()):
        society["node_id"] = i
        societies[society["id"]] = society
        nodes.append(society)
        i += 1

#False
g = ig.Graph(n = len(nodes), directed = False)
g.vs["fields"] = nodes

# society-society links
#TODO add other societies
for society in societies.values():
    if ( society["sociedadcontroladora_id"] is not None and
         society["sociedadcontroladora_id"] is not 0 ):
        v1 = society["node_id"]
        v2 = societies[society["sociedadcontroladora_id"]]["node_id"]
        g.add_edges([(v1,v2)])

    if ( society["controlador_id"] is not None and
         society["controlador_id"] is not 0 ):
        v1 = society["node_id"]
        v2 = societies[society["controlador_id"]]["node_id"]
        g.add_edges([(v1,v2)])

# group links
for group in groups.values():
    if ( group["controladorgrupo_id"] is not None and
         group["controladorgrupo_id"] is not 0 ):
        v1 = group["node_id"]
        v2 = societies[group["controladorgrupo_id"]]["node_id"]
        g.add_edges([(v1,v2)])


# owner links
for owner in owners.values():
    if ( owner["grupo_id"] is not None and
         owner["grupo_id"] is not 0 ):
        v1 = owner["node_id"]
        v2 = groups[owner["grupo_id"]]["node_id"]
        g.add_edges([(v1,v2)])

    if ( owner["propietariopropietario_id"] is not None and
         owner["propietariopropietario_id"] is not 0 ):
        v1 = owner["node_id"]
        v2 = owners[owner["propietariopropietario_id"]]["node_id"]
        g.add_edges([(v1,v2)])

    if ( owner["sociedadcontroladora_id"] is not None and
         owner["sociedadcontroladora_id"] is not 0 ):
        v1 = owner["node_id"]
        v2 = societies[owner["sociedadcontroladora_id"]]["node_id"]
        g.add_edges([(v1,v2)])

for outlet_dict in outlets:
    for outlet in outlet_dict.values():
        if ( outlet["asociadoacanaltv_id"] is not None and
             outlet["asociadoacanaltv_id"] is not 0 ):
            v1 = outlet["node_id"]
            v2 = outlets[0][outlet["asociadoacanaltv_id"]]["node_id"]
            g.add_edges([(v1,v2)])

        if ( outlet["asociadoaescrito_id"] is not None and
             outlet["asociadoaescrito_id"] is not 0 ):
            v1 = outlet["node_id"]
            v2 = outlets[1][outlet["asociadoaescrito_id"]]["node_id"]
            g.add_edges([(v1,v2)])

        if ( outlet["asociadoamediodigital_id"] is not None and
             outlet["asociadoamediodigital_id"] is not 0 ):
            v1 = outlet["node_id"]
            v2 = outlets[2][outlet["asociadoamediodigital_id"]]["node_id"]
            g.add_edges([(v1,v2)])

        if ( outlet["asociadoaradio_id"] is not None and
             outlet["asociadoaradio_id"] is not 0 ):
            v1 = outlet["node_id"]
            v2 = outlets[3][outlet["asociadoaradio_id"]]["node_id"]
            g.add_edges([(v1,v2)])

        if ( outlet["grupo_id"] is not None and
             outlet["grupo_id"] is not 0 ):
            v1 = outlet["node_id"]
            v2 = groups[outlet["grupo_id"]]["node_id"]
            g.add_edges([(v1,v2)])



with codecs.open(TV_OWNERS_FILE, "r", "utf-8") as json_file:
    for tv_owner in json.loads(json_file.read()):
        v1 = outlets[0][tv_owner["canaltv_id"]]["node_id"]
        v2 = owners[tv_owner["propietario_id"]]["node_id"]
        g.add_edges([(v1,v2)])
       
all_outlets = []

for d in outlets:
    all_outlets.extend(outlet for outlet in d.values())

selected_outlets = []
if args.in_file is not None:
    with args.in_file as in_file:
        parsed_json = json.loads(in_file.read())
        wanted_names = [ x["name"] for x in parsed_json["nodes"] ]

    outlet_names = list(enumerate((outlet["medio"],outlet["t"]) for outlet in all_outlets))
    for twitter_name in wanted_names:
        name = twitter_name
        options = list(sorted(outlet_names, 
                         key = lambda x: fuzz.partial_ratio(name,
                             clean_name(x[1][0])), reverse=True))

        n = 1
        while True:
            try:
                print "\n".join(("index : %d " % opt[0]) +
                                ("name: %s " % clean_name(opt[1][0]) ) +
                                ("type:%s" % opt[1][1])
                                for opt in options[0:(n * 20)])

                user_input  = raw_input("\nSelect index for %s: " % name)

                if len(user_input) is 0:
                    n += 1
                    continue
                else:
                    idx = int(user_input)
                    if idx >= -1:
                        break
            except ValueError:
                n = 1
                name = user_input
                options = list(sorted(outlet_names, 
                         key = lambda x: fuzz.partial_ratio(name,
                             clean_name(x[1][0])), reverse=True))


                
            print "Try again."
        if idx < 0:
            continue
        all_outlets[idx]["name"] = twitter_name
        selected_outlets.append(all_outlets[idx])
        print ""
    out_nodes = [ { "index": o["node_id"],
                    "name" : o["name"],
                    "full_name" : o["medio"] + o["t"],
                    "size" : 10 } for o in selected_outlets ]

else:
    selected_outlets = all_outlets
    out_nodes = [ { "index": o["node_id"],
                    "name" : o["medio"] + o["t"],
                    "size" : 10 } for o in selected_outlets ]

path_lengths = g.shortest_paths_dijkstra(mode=ig.ALL)
out_links = []

for i, j in combinations(selected_outlets, 2):
    if i["node_id"] == j["node_id"]:
        print "Warning - repeated node:"
        print i
        print j
        continue
    if path_lengths[i["node_id"]][j["node_id"]] < float('inf'):
        print (i["medio"] + " - " + j["medio"] + " : " +
               str(path_lengths[i["node_id"]][j["node_id"]]))

        out_links.append({
            "source": i["node_id"],
            "target": j["node_id"],
            "value" : 1.0/(path_lengths[i["node_id"]][j["node_id"]])
            })

with args.out_file as out_file:
    if args.pretty:
        out_file.write(json.dumps({
            "nodes" : out_nodes,
            "links" : out_links },
            indent = 4, separators = (",", ":")))
    else:
        out_file.write(json.dumps({
            "nodes" : out_nodes,
            "links" : out_links }))

