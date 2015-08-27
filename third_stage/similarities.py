#!/usr/bin/python
import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import codecs, re
from datetime import datetime
from nltk.corpus import stopwords
from itertools import combinations, groupby
from operator import itemgetter
from twitter_scripts import getKeywords_fromHeadlines
import igraph as ig
import re
from scipy import stats

date_format = "%Y-%m-%d"

class readable_dir(ap.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a valid " \
                    "path").format(prospective_dir)) 

        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a " \
            "readable dir".format(prospective_dir)))

remove = re.compile(r"\b\S{1,2}\b|#\S+|@\w+|\bhttps?\S+\b")
replace = re.compile(r"\s+|[!\"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]")
shorten = re.compile(r"\s+")

normalize_text = lambda text: shorten.sub(" ", (replace.sub(" ", \
        remove.sub("", unidecode(text).lower())))).strip()

stop_words = set(map(normalize_text, stopwords.words("spanish")))

def aggregate_tweets(files) :

    names = defaultdict(float)
    tweets = defaultdict(lambda: defaultdict(list))

    for filename in files:
        with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:
            try:
                if day != last_day:
                    n_days += 1
            except NameError:
                n_days = 1

            parsed_json = json.loads(f.read())
            for tweet in parsed_json:
                name = tweet["user"]["screen_name"]
                names[name] += 1

    chosen_names = [ k for k, v in names.iteritems() if v/n_days >= MIN_TWEETS_PER_DAY]

    topics = dict()
    day_keywords = []
    day_tweets = []

    similarities = defaultdict(list)

    
    for day, filenames in groupby(sorted(files), lambda filename: filename[0:10]):

        day_tweets = []
        day_keywords = []

        for filename in filenames:
            with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:    
                parsed_json = json.loads(f.read())
                
                tweets = [ (tweet["user"]["screen_name"],
                    set(normalize_text(tweet["text"]).split()) - stop_words) for
                    tweet in parsed_json ]
                day_keywords.extend(get_keywords(tweet[1] for tweet in tweets if
                    len(tweet[1]) > 0))
                day_tweets.extend(tweets)

        topics = sorted(get_topics(day_keywords))
        
        descriptors = dict()

        for name in chosen_names:
            outlet_tweets = set().union(*(d[1] for d in day_tweets if d[0] ==
                    name))

            scores = [ 1 if len(t & outlet_tweets) > 0 else 0
                    for t in topics ]
            total = float(sum(scores))

            try:
                descriptors[name] = [ sc/total for sc in scores ]
            except ZeroDivisionError:
                descriptors[name] = scores

        for n1, n2 in combinations(chosen_names, 2):
            pair_similarity = similarity(descriptors[n1], descriptors[n2])
            similarities[n1 + " " + n2].append(pair_similarity)

    return (chosen_names, similarities)

def compare(e1, e2):
    """
    e1 = {kw1: sc1, kw2: sc2}
    e2 = {kw3: sc3, kw4: sc4}
    """
    score1 = sum(e1.values()) / len(e1.values())
    score2 = sum(e2.values()) / len(e2.values())
    return score2 - score1

def get_keywords(list_of_tweets):
    groups = getKeywords_fromHeadlines(list_of_tweets)
    groups = sorted(groups, cmp = compare)

    if len(groups) > MAX_TOPICS_PER_DAY:
        groups = groups[0:MAX_TOPICS_PER_DAY]

    ret = []
    for g in groups:
        most_relevant_kws = sorted(g.iteritems(), key=itemgetter(1), reverse=True)
        ret.append(tuple(map(itemgetter(0), most_relevant_kws[0:KEYWORDS_PER_TOPIC])))
    return ret

def get_topics(pairs_of_keywords):

    all_keywords = set(map(itemgetter(0), pairs_of_keywords)) |\
                   set(map(itemgetter(1), pairs_of_keywords))

    index_to_word = { k:v for k, v in enumerate(all_keywords) }
    word_to_index = { v:k for k, v in enumerate(all_keywords) }

    g = ig.Graph(n = len(all_keywords),\
            edges = map(lambda p: (word_to_index[p[0]], word_to_index[p[1]]),\
            pairs_of_keywords), directed = False)

    connected_components = map( lambda c: set(map(lambda t: index_to_word[t],
        c)), g.components(mode=ig.WEAK))
    return connected_components

def similarity(desc1, desc2):
    return sum( v1 * v2 for (v1, v2) in zip(desc1, desc2) )

parser = ap.ArgumentParser(description = "Computes time series for a" \
    "folder of JSON files containing tweets and a term.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-t", "--threshold", default=0, type=float, \
        help = "The minimum average tweet-per-day to require. Default is no" \
        "threshold at all.")

parser.add_argument("-k", "--keywords_per_day", default=2, type=int, \
        help = "Number of keywords per day. Default is 2.")

parser.add_argument("-d", "--topics_per_day", default=0, type=int, \
        help = "Number of topics per day. Default is 6")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

folder = args.folder
MIN_TWEETS_PER_DAY = args.threshold
KEYWORDS_PER_TOPIC = args.keywords_per_day
MAX_TOPICS_PER_DAY = args.topics_per_day

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

(chosen_names, similarities) = aggregate_tweets(files)

for k, v in similarities:

    mean = stats.mean(similarities[k])
    kurtosis = stats.kurtosis(similarities[k])

    similarities[k] = { "mean" : mean , "kurtosis": kurtosis }

with args.out_file as out_file:

    if args.pretty:
        out_file.write(json.dumps( \
            similarities, \
            indent = 4, separators = (",", ":" )))
    else:
        out_file.write(json.dumps( \
            similarities))
