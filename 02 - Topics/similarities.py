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
replace = re.compile(r"\s+|[!\"#$%&\'()*+,./:;<=>?@\[\\\]^_`{|}~-]")
shorten = re.compile(r"\s+")

normalize_text = lambda text: shorten.sub(" ", (replace.sub(" ", \
        remove.sub("", unidecode(text).lower())))).strip()

stop_words = set(map(normalize_text, stopwords.words("spanish"))) | set(["via",
"dia", "uso", "foto", "fotos", "video", "chile", "2015", "2014", "ver", "tras",
"galeria", "informate", "registrate","http", "hoy", "lunes", "martes",
"miercoles", "jueves", "viernes", "sabado", "domingo", "enero",
"febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
"octubre", "noviembre", "diciembre", "vivo", "ahora"] )

def filter_names(files) :

    names = defaultdict(float)
    days = set()
    for filename in files:
        with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:
            days.add(filename[0:10])

            parsed_json = json.loads(f.read())

            for tweet in parsed_json:
                name = tweet["user"]["screen_name"]
                names[name] += 1

    return [ k for k, v in names.iteritems() if float(v)/len(days) >= MIN_TWEETS_PER_DAY]


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

    if COUNT_KEYWORDS:
        keyword_count = defaultdict(lambda : defaultdict(int))
    else:
        keyword_count = None

    for day, filenames in groupby(sorted(files), lambda filename: filename[0:10]):
        days.append(day)

        if VERBOSE:
            sys.stderr.write(day + "\n" )

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

        tf_idf = get_tf_idf(day_tweets, day_keywords, chosen_names,
                keyword_count)

        for n1, n2 in combinations(chosen_names, 2):
            pair_similarity = similarity(tf_idf[n1], tf_idf[n2])
            similarities[n1 + " " + n2].append(pair_similarity)

    if COUNT_KEYWORDS:
        return (chosen_names, similarities, days, keyword_count)
    else:
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

    N = float(len(hourly_topics))
    hourly_keywords = map(lambda x: tuple(chain.from_iterable(x)),
            hourly_topics)

    # maximum frequency of any word for every given hour
    # FIXME this gives us a vector of values. how do we convert it to a
    # score? using its vector length? <- using this atm
    f2 = [ max(sum(word in topic for topic in hour_topics)/float(len(hour_topics))
                for word in hour_keywords)
            for hour_topics, hour_keywords in zip(hourly_topics, hourly_keywords) 
            if len(hour_keywords) > 0 ]
        
    for word in keywords:
        # maximum number of topics the word appears in for any hour
        f1 = max(map(lambda hour: sum(word in topic for topic in
            hour)/float(max(1,len(hour))), hourly_topics))
        idf = log(N/sum(word in hour for hour in hourly_keywords))
        
        maxtf_idf[word] = average([( 0.5 + 0.5 * f1 / f2_i ) * idf for f2_i in f2 ])

    return maxtf_idf

def get_tf_idf(tweets, topic_keywords, names, keyword_count = None):

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
    components = g.decompose(mode=ig.STRONG)

    for component in components:
        if len(component.vs) <= 2*KEYWORDS_PER_TOPIC:
            continue

        component_words = sorted(component.vs["name"], key= lambda x:
                maxtf_idf[x])
        
        to_delete = set()
        for word in component_words:
            if word in component.vs(component.articulation_points())["name"]:
                if VERBOSE:
                    sys.stderr.write("deleting " + word + "\n")
                to_delete.add(word)
            else: 
                break
    
        component.delete_vertices(to_delete)
        g.delete_vertices(to_delete)
        all_keywords -= to_delete
       
    event_components = g.components(mode=ig.STRONG)
    event_membership = event_components.membership

    if VERBOSE:
        sys.stderr.write("".join([ "\t" + " ".join(map(lambda z:
            g.vs.find(z)["name"], x)) + "\n" for x
            in event_components ]))
    n_events = len(event_components)
   
    tf = dict()

    if keyword_count is not None:
        daily_keyword_count = defaultdict(lambda : defaultdict(float))
        kw_idfs = defaultdict(set)

    for name in names:

        if keyword_count is not None:
            daily_count = daily_keyword_count[name]

        outlet_tweets = [ d[1] for d in tweets if d[0] == name ]

        # don't panic.
        # for events, terms = events. documents = twitter accounts. 
        # occurences =  # tweets,

        # for keywords, terms = keywords, documents = twitter accounts
        # occurences = # tweets
        # we count how many tweets touch on a given event. we repeat this
        # for each event, and divide this count over the amount of tweets
        # for that outlet. this gives us t

        tf[name] = [0.0] * n_events

        for tweet in outlet_tweets:
            tweet_keywords = tweet & all_keywords

            if keyword_count is not None:
                for kw in tweet_keywords:
                    daily_count[kw] += 1.0

            tfs = [0] * n_events

            for k1, k2 in combinations(tweet_keywords, 2):
                try:
                    # if the pair corresponds to a keyword pair...
                    if g.are_connected(k1, k2):

                        # first, we touched the event. so we set it as touched.
                        tfs[event_membership[g.vs.find(name=k1).index]] = 1.0
                except ValueError:
                    pass
            
            # now we sum the tf values for this tweet
            tf[name] = map(sum, zip(tf[name], tfs))

        # we have all f's. we get max_f and normalize tf.
        max_f = len(outlet_tweets) # max(tf[name])

        # well, the outlet might have not talked about anything.
        if max_f == 0.0:
            max_f = 1.0

        tf[name] = map(lambda f:  f/max_f, tf[name])
        
        if keyword_count is not None:
            for kw, f in daily_count.iteritems():
                daily_count[kw] =  f/max_f

    # now we compute idf

    N = float(len(names))

    idf = [0] * n_events
    
    for i in xrange(n_events):
        total = sum(tf[name][i] > 0 for name in names) 
        if total > 0:
            idf[i] = log(N/total)

    if keyword_count is not None:
        
        kw_idfs = defaultdict(float)

        for kw in all_keywords:

            # As we only ever put positive values in keyword counts (we use a
            # lazy defaultdict) it's enough to see if the keyword appears
            # amongst its keys. This form also avoids to fill keyword counts
            # with useless zeroes.
            total = sum((kw in kw_count) for kw_count in daily_keyword_count.values())

            if total > 0:
                kw_idfs[kw] = log(N/total)

        for name in names:
            daily_count = daily_keyword_count[name]
            for kw in daily_count.keys():
                daily_count[kw] *= kw_idfs[kw]


            magnitude = norm(daily_count.values())

            if magnitude is 0:
                magnitude = 1.0
            
            for kw, val in daily_count.iteritems():
                keyword_count[name][kw] += val/magnitude

    tf_idf = dict()

    for name in names:
        for i in xrange(n_events):
            tf[name][i] *= idf[i]

        magnitude = norm(tf[name])
        
        if magnitude == 0.0:
            magnitude = 1.0

        tf_idf[name] = [ t/magnitude for t in tf[name] ]

    
    return tf_idf

def similarity(tf1, tf2):
    return sum( v1 * v2 for (v1, v2) in zip(tf1, tf2) )


parser = ap.ArgumentParser(description = "Computes topic-based similarities for a " \
    "folder of JSON files containing tweets and a term.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-c", "--count_keywords", action="store_true", \
        help = "Enable keyword count for each media outlet.")

parser.add_argument("-t", "--threshold", default=0, type=float, \
        help = "The minimum average tweet-per-day to require. Default is no" \
        "threshold at all.")

parser.add_argument("-k", "--keywords_per_topic", default=2, type=int, \
        help = "Number of keywords per topic. Default is 2.")

parser.add_argument("-d", "--topics_per_hour", default=6, type=int, \
        help = "Number of topics per hour. Default is 6")

parser.add_argument("-v", "--verbose", action="store_true",
        help = "Whether to print the computed topics.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

folder = args.folder
COUNT_KEYWORDS = args.count_keywords
MIN_TWEETS_PER_DAY = args.threshold
KEYWORDS_PER_TOPIC = args.keywords_per_topic
MAX_TOPICS_PER_HOUR = args.topics_per_hour
VERBOSE = args.verbose

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

if COUNT_KEYWORDS:
    (chosen_names, similarities, days, keyword_count) = aggregate_tweets(files)
else:
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
                    "values" : [ sim_avg, kurt, sim_median ],
                    "value" : sim_avg } )
output = { "nodes": nodes, 
           "links" : links,
           "days" : days }

if COUNT_KEYWORDS:
    output["keyword_count"] = keyword_count

with args.out_file as out_file:

    if args.pretty:
        out_file.write(json.dumps(output,
            indent = 4, separators = (",", ":" )))
    else:
        out_file.write(json.dumps(output))
