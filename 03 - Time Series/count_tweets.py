#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re

class readable_dir(ap.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a valid" + \
                    "path").format(prospective_dir)) 

        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a" + \
            "readable dir".format(prospective_dir)))


parser = ap.ArgumentParser(description = "Computes the amount of tweets per day for a" + \
    "folder of JSON files containing tweets.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " + \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")
#TODO: add:
#   temporal granularity parameter
#   time interval parameter
#   method parameter

args = parser.parse_args()

folder = args.folder

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

files = sorted(files)

total_tweets = defaultdict(lambda: defaultdict(float))
all_days = set()

for filename in files:

    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:

        parsed_json = json.loads(f.read())
        
        day =  filename[0:10]
        all_days.add(day)
        
        for tweet in parsed_json:
            name = tweet["user"]["screen_name"]

            total_tweets[name][day] += 1
            
all_days = sorted(list(all_days))

#FIXME: this might cause problems, as we're modifying things while reading them
# better ask someone.
for name, days in total_tweets.items():

    # We force every day to appear.
    for day in all_days:
        days[day]

with args.out_file as out_file:
    for name, days in total_tweets.items():
        out_file.write( " ".join([ str(days[day]) for day in sorted(days.keys()) ]) + "\n")

    #    if args.pretty:
    #        out_file.write(json.dumps( \
    #            { "time_labels" : all_days, \
    #              "values": total_tweets}, \
    #              indent=4, separators = (",", ":" )))
    #    else:
    #        out_file.write(json.dumps( \
    #            { "time_labels" : all_days, \
    #              "values": total_tweets } ))
