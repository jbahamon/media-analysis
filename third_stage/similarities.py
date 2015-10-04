#!/usr/bin/python
import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import codecs, re
from datetime import datetime
from nltk.corpus import stopwords
from itertools import combinations, groupby, chain
from operator import itemgetter
from twitter_scripts import getKeywords_fromHeadlines
import igraph as ig
import re
from numpy.linalg import norm
from numpy import average, median
from scipy.stats import kurtosis
from math import sqrt, log

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

def filter_names(files) :

    names = defaultdict(float)

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

    return [ k for k, v in names.iteritems() if v/n_days >= MIN_TWEETS_PER_DAY]


def get_tweets_keywords(filenames):
    day_tweets = []
    day_keywords = []

    for filename in filenames:
        with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:    
            parsed_json = json.loads(f.read())
            
            tweets = [ (tweet["user"]["screen_name"],
                set(normalize_text(tweet["text"]).split()) - stop_words) for
                tweet in parsed_json ]

            day_keywords.append(get_keywords(tweet[1] for tweet in tweets if
                len(tweet[1]) > 0))
            day_tweets.extend(tweets)

    return (day_tweets, day_keywords)

def aggregate_tweets(files) :

    chosen_names = filter_names(files)
    similarities = defaultdict(list)
    days = []
    for day, filenames in groupby(sorted(files), lambda filename: filename[0:10]):
        days.append(day)

        (day_tweets, day_keywords) = get_tweets_keywords(filenames)
        """
        cosas para omaruchan
        print json.dumps( \
                sorted(map((lambda d: { k[0]: k[1] for k in d }),
                    day_keywords), key=lambda d: sum(v for k, v in
                        d.iteritems()),
                    reverse=True), \
            indent = 4, separators = (",", ":" ))
        
        """

        tf_idf = get_tf_idf(day_tweets, day_keywords, chosen_names)

        for n1, n2 in combinations(chosen_names, 2):
            pair_similarity = similarity(tf_idf[n1], tf_idf[n2])
            similarities[n1 + " " + n2].append(pair_similarity)

    return (chosen_names, similarities, days)

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

    if len(groups) > MAX_TOPICS_PER_HOUR:
        groups = groups[0:MAX_TOPICS_PER_HOUR]

    ret = []
    for g in groups:
        most_relevant_kws = sorted(g.iteritems(), key=itemgetter(1), reverse=True)
        ret.append(tuple(most_relevant_kws[0:KEYWORDS_PER_TOPIC]))
    return ret

def get_maxtf_idf(hourly_topics, keywords):
    maxtf_idf = dict()

    N = len(hourly_topics)
    hourly_keywords = map(lambda x: tuple(chain.from_iterable(x)),
            hourly_topics)

    # maximum frequency of any word for the given hour
    # FIXME this gives us a vector of values. how do we convert it to a
    # score? using its vector length? <- using this atm

    f2 =  [ max(sum(word in topic for topic in hour) for word in hour_keywords)
            for hour, hour_keywords in zip(hourly_topics, hourly_keywords) if
            len(hour_keywords) > 0 ]

    for word in keywords:
        # maximum number of topics the word appears in for any hour
        f1 = max(map(lambda hour: sum(word in topic for topic in hour),
                hourly_topics))

        idf = log(N/sum(word in hour for hour in hourly_keywords))
        
        maxtf_idf[word] = norm([( 0.5 + 0.5 * f1 / f2_i ) * idf for f2_i in f2 ])

    return maxtf_idf

def get_tf_idf(tweets, topic_keywords, names):

    hourly_topics = map(lambda hour: map(lambda topic: tuple(map(lambda kw:
        kw[0], topic)), hour), topic_keywords)
    
    day_topics = map(lambda topic: tuple(map(lambda keyword: keyword[0], topic)),
            chain.from_iterable(topic_keywords))

    all_keywords = set().union(*(set(d) for d in day_topics))

    maxtf_idf = get_maxtf_idf(hourly_topics, all_keywords)

    g = ig.Graph(n = len(all_keywords), directed = False)
    g.vs["name"] = list(all_keywords)

    edges = set()

    for topic in day_topics:
        edges.update((p1, p2) for p1, p2 in combinations(topic, 2))


    g.add_edges(edges)

    # Idea: what if we use strongly-connected components?
    components = g.decompose(mode=ig.WEAK)

    for component in components:
        
        component_words = sorted(component.vs["name"], key= lambda x:
                maxtf_idf[x])

        for word in component_words:

            if word in component.vs(component.articulation_points())["name"]:
                component.delete_vertices(word)
                g.delete_vertices(word)
            else: 
                break
    
    event_components = g.components(mode=ig.WEAK)
    event_membership = event_components.membership
    n_events = len(event_components)
   
    tf = dict()

    for name in names:

        outlet_tweets = [ d[1] for d in tweets if d[0] == name ]
        total_tweeets = float(len(outlet_tweets))

        # don't panic.
        # we count how many tweets touch on a given event. we repeat this
        # for each event, and divide this count over the amount of tweets
        # for that outlet. this gives us tf

        tf[name] = [0] * n_events

        for tweet in outlet_tweets:
            tweet_keywords = tweet & all_keywords

            tfs = [0] * n_events

            for k1, k2 in combinations(tweet_keywords, 2):
                try:
                    if g.are_connected(k1, k2):
                        tfs[event_membership[g.vs.find(name=k1).index]] = 1
                except ValueError:
                    pass
            tf[name] = map(sum, zip(tf[name], tfs))

    # now we compute idf

    N = float(len(names))

    idf = [ log(N/(sum(tf[name][i] > 0 for name in names)
        + 1)) for i in xrange(n_events) ]

    tf_idf = dict()

    for name in names:
        for i in xrange(n_events):
            tf[name][i] *= idf[i]

        magnitude = norm(tf[name])
        if magnitude > 0:
            tf_idf[name] = [ t/magnitude for t in tf[name] ]
        else:
            tf_idf[name] = tf[name]

    return tf_idf

def similarity(tf1, tf2):
    return sum( v1 * v2 for (v1, v2) in zip(tf1, tf2) )


parser = ap.ArgumentParser(description = "Computes time series for a" \
    "folder of JSON files containing tweets and a term.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-t", "--threshold", default=0, type=float, \
        help = "The minimum average tweet-per-day to require. Default is no" \
        "threshold at all.")

parser.add_argument("-k", "--keywords_per_topic", default=2, type=int, \
        help = "Number of keywords per topic. Default is 2.")

parser.add_argument("-d", "--topics_per_hour", default=0, type=int, \
        help = "Number of topics per hour. Default is 6")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

folder = args.folder
MIN_TWEETS_PER_DAY = args.threshold
KEYWORDS_PER_TOPIC = args.keywords_per_topic
MAX_TOPICS_PER_HOUR = args.topics_per_hour

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

(chosen_names, similarities, days) = aggregate_tweets(files)

name_to_index = { v : k for k, v in enumerate(chosen_names) }

nodes = [ { "index": name_to_index[name], "name" : name, "size":10 } for name in chosen_names ]

links = []

for k, v in similarities.iteritems():

    sim_median = median(similarities[k])
    sim_avg = average(similarities[k])
    kurt = kurtosis(similarities[k])

    links.append( { "source": name_to_index[k.split()[0]],
                    "target": name_to_index[k.split()[1]],
                    "values" : [ sim_avg, kurt, sim_median ]  } )

with args.out_file as out_file:

    if args.pretty:
        out_file.write(json.dumps( \
                { "nodes": nodes, 
                  "links" : links,
                  "days" : days },
            indent = 4, separators = (",", ":" )))
    else:
        out_file.write(json.dumps( \
                { "nodes": nodes, 
                    "links" : links,
                    "days" : days }))
