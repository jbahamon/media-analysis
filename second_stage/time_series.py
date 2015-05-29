#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re
from datetime import datetime
import math

date_format = "%Y-%m-%d"

class readable_dir(ap.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a valid" \
                    "path").format(prospective_dir)) 

        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a" \
            "readable dir".format(prospective_dir)))

# this is enough for now.
normalize_text = lambda text: unidecode(text).strip().lower()

parser = ap.ArgumentParser(description = "Computes time series for a" \
    "folder of JSON files containing tweets and a term.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("terms_file", type=ap.FileType("r"),  \
        help = "A file with a single term per line. Time series " \
        "will be created for each term.")

parser.add_argument("-t", "--threshold", default=0, type=float, \
        help = "The minimum average tweet-per-day to require. Default is no" \
        "threshold at all.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")


#TODO: add:
#   temporal granularity parameter
#   time interval parameter
#   method parameter

patch_value = 0.000001

args = parser.parse_args()

folder = args.folder
terms = []

with args.terms_file as f:
    terms = [ set(map(normalize_text, line.split())) for line in f.readlines() ]

media_histogram = defaultdict(int)

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

files = sorted(files)

mentions     = { "+".join(map(str, t)) : defaultdict(lambda: defaultdict(float)) for t in terms }
total_tweets = defaultdict(lambda: defaultdict(float))

all_days = set()

for filename in files:

    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:

        parsed_json = json.loads(f.read())
        day =  filename[0:10]
        all_days.add(day)
        
        for tweet in parsed_json:
            name = tweet["user"]["screen_name"]
            words = [ normalize_text(x) for x in tweet["text"].split() ]

            for x in [ "+".join(map(str,term)) for term in terms if any(w in words for w in term) ]:
                mentions[x][name][day] += 1

            total_tweets[name][day] += 1
            
all_days = sorted(list(all_days))

day_range = datetime.strptime(all_days[-1], date_format) - \
            datetime.strptime(all_days[ 0], date_format)

#FIXME: this might cause problems, as we're modifying things while reading them
# better ask someone.
for term in terms:
    term_mentions = mentions["+".join(map(str,term))]
    for name, days in term_mentions.items():

        # We remove the 
        if sum( [ x for x in total_tweets[name].values() ] )/float(day_range.days) < args.threshold :
            del term_mentions[name]
            del total_tweets[name]
            continue

        # We force every day to appear.
        for day in all_days:
            days[day]

        normalized_mentions = []

        for i in xrange(1,len(all_days)):
            prev_day = days[all_days[i - 1]] + patch_value
            day = days[all_days[i]] + patch_value
            total_for_day = total_tweets[name][day] + patch_value

            delta_amount = math.log( \
                         (day      / (float(total_for_day) + patch_value)) / \
                    float(prev_day / (float(total_for_day) + patch_value) ))

            normalized_mentions.append(delta_amount)

        term_mentions[name] = normalized_mentions

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
