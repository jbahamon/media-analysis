#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re
from datetime import datetime

date_format = "%Y-%m-%d"

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

# this is enough for now.
normalize_text = lambda text: unidecode(text).strip().lower()

parser = ap.ArgumentParser(description = "Computes time series for a" + \
    "folder of JSON files containing tweets and a term.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("term", help = "The terms to create the time series for."+ \
        "These are treated as a single term")

parser.add_argument("-t", "--threshold", default=0, type=float, \
        help = "The minimum average tweet-per-day to require. Default is no" +\
        "threshold at all.")

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
term = normalize_text(args.term)

media_histogram = defaultdict(int)

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

files = sorted(files)

# Date 

mentions     = defaultdict(lambda: defaultdict(float))
total_tweets = defaultdict(lambda: defaultdict(float))

all_days = set()

for filename in files:

    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:

        parsed_json = json.loads(f.read())
        day =  filename[0:10]
        all_days.add(day)
        
        for tweet in parsed_json:
            name = tweet["user"]["screen_name"]
            text = normalize_text(tweet["text"])
            
            if args.term in text.split():
                mentions[name][day] += 1

            total_tweets[name][day] += 1
            
all_days = sorted(list(all_days))

day_range = datetime.strptime(all_days[-1], date_format) - \
            datetime.strptime(all_days[ 0], date_format)

#FIXME: this might cause problems, as we're modifying things while reading them
# better ask someone.
for name, days in mentions.items():

    # We remove the 
    if sum( [ x for x in total_tweets[name].values() ] )/float(day_range.days) < args.threshold :
        del mentions[name]
        del total_tweets[name]
        continue

    # We force every day to appear.
    for day in all_days:
        days[day]

    for day, amount in days.items():
        total_for_day = total_tweets[name][day]
        mentions[name][day] = amount/total_for_day if total_for_day > 0 else 0

    dayz = mentions[name]
    mentions[name] = [ dayz[key] for key in sorted(dayz.keys()) ] 


with args.out_file as out_file:

    if args.pretty:
        out_file.write(json.dumps( \
            { "time_labels" : all_days, \
              "series": mentions }, \
              indent = 4, separators = (",", ":" )))
    else:
        out_file.write(json.dumps( \
            { "time_labels" : all_days, \
              "series": mentions }))
              

        
