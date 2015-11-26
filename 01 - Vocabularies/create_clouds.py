#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import itertools
from operator import itemgetter

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

remove = re.compile(r"\b\S{1,2}\b|#\S+|@\w+|\bhttps?\S+\b")
replace = re.compile(r"\s+|[!\"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]")
shorten = re.compile(r"\s+")

# this is enough for now.
normalize_text = lambda text: shorten.sub(" ", (replace.sub(" ", \
        remove.sub("", unidecode(text).lower())))).strip()

def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" %
                value)
    return ivalue

def gather_tweets(filename, tweets):
    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:
        parsed_json = json.loads(f.read())

        for tweet in parsed_json:
            tweets[tweet["user"]["screen_name"]].append(normalize_text(tweet["text"]))
        return len(parsed_json)

def tokenize(text):
    return word_tokenize(text)

parser = ap.ArgumentParser(description = "Selects the highest scoring words " \
    "for media outlet communities and a set of tweets.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
    "The JSON file with the outlet communities. If not specified, the standard input will be used.")

parser.add_argument("-n", "--num_words", type=check_positive, default=10, help = \
    "The number of top-scoring words to select for each community")


parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")
args = parser.parse_args()

folder = args.folder

tweets = defaultdict(list)

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

i = 0
for f in files:
    i += gather_tweets(f, tweets)

for k, v in tweets.items():
    n_tweets = len(v)
    # sys.stderr.write(k + " " + str(n_tweets) + "\n")
    tweets[k] = " ".join(v)


names = tweets.keys()
news_data = tweets.values()

stop_words = set(map(normalize_text, stopwords.words("spanish"))) | set(["via", "dia", "uso", "fotos", "foto", "video", "chile", "2015", "2014", "ver", "tras", "galeria", "informate", "registrate","http"] )


vectorizer = TfidfVectorizer(tokenizer=tokenize,
        stop_words=stop_words)

tfidfs = vectorizer.fit_transform(news_data)

feature_words = vectorizer.get_feature_names()

vocab_size = len(vectorizer.idf_)
with args.in_file as in_file:
    parsed_json = json.loads(in_file.read())

    communities = { i: set(x["name"] for x in parsed_json["nodes"] if
        x["color_value"] == i) for i in set(n["color_value"] for n in
            parsed_json["nodes"]) }


    indexed_names = { j: i for i, j in enumerate(names) }

    scores = defaultdict(lambda : np.ndarray([1, vocab_size]))

    for community, members in communities.iteritems():
        for name in members:
            scores[community] += tfidfs[indexed_names[name], :]

    community_words = dict()

    for community, tfidf in scores.iteritems():
        scores = list(map(lambda x: (feature_words[x[0]], x[1] ),
            itertools.islice(sorted(enumerate(list(tfidf.A1)), key = itemgetter(1),
                reverse=True), 0, args.num_words))) 

        max_score = max(map(itemgetter(1), scores))
        min_score = min(map(itemgetter(1), scores))

        if min_score == max_score:
            max_score += 0.01
        
        community_words[community] = dict(map(lambda x:
            (x[0], (x[1] - min_score)/(max_score - min_score)), scores))

    parsed_json["words"] = community_words 
    with args.out_file as out_file:
        if args.pretty:
            out_file.write(json.dumps(parsed_json,\
                    indent = 4, separators = (",", ":")))
        else:
            out_file.write(json.dumps(parsed_json))
