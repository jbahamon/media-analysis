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

def aggregate_tweets(terms, files):
    files = sorted(files)

    mentions = { "+".join(map(str, t)) : defaultdict(lambda: defaultdict(float)) for t in terms }
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

                for x in [ "+".join(map(str,term)) for term in terms \
                        if any(w in words for w in term) ]:
                    mentions[x][name][day] += 1

                total_tweets[name][day] += 1
                
    all_days = sorted(list(all_days))

    return (mentions, total_tweets, all_days)


def normalize_series(time_series, all_days, threshold):

    if len(time_series.items()) < threshold:
        return None
    for k, v in time_series.items():
        total_for_day = total_tweets[name][k]
        time_series[k] = v/float(total_for_day)

    try:
        prev_value = float(time_series[time_series.keys()[0]])
        del time_series[time_series.keys()[0]]
    except KeyError:
        return None

    for k in sorted(time_series.keys()[1:]):
        current_value = time_series[k]
        time_series[k] = current_value/prev_value
        prev_value = current_value
        
    # Finally, we force every day to appear.
    for day in all_days:
        days[day]

    return [ time_series[day] for day in all_days ]

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

parser.add_argument("-m", "--minimum_tweets", default=3, type=float, \
        help = "The minimum number of tweets with a term to require. Defaults to" \
        " three (less than that would mess up the normalization procedure).")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")
#TODO: add:
#   temporal granularity parameter
#   time interval parameter
#   method parameter

args = parser.parse_args()

folder = args.folder
terms = []

with args.terms_file as f:
    terms = [ set(map(normalize_text, line.split())) for line in f.readlines() ]

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

(mentions, total_tweets, all_days) = aggregate_tweets(terms, files)

day_range = datetime.strptime(all_days[-1], date_format) - \
            datetime.strptime(all_days[ 0], date_format)

#FIXME: this might cause problems, as we're modifying things while reading them
# better ask someone.
for term in terms:
    term_mentions = mentions["+".join(map(str,term))]
    
    for name, days in term_mentions.items():

        if sum( [ x for x in total_tweets[name].values() ] )/float(day_range.days) < args.threshold :
            del term_mentions[name]
            continue

        normalized_mentions = normalize_series(days, all_days, \
                args.minimum_tweets)

        if normalized_mentions is not None:
            term_mentions[name] = normalized_mentions
        else:
            del term_mentions[name]

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
