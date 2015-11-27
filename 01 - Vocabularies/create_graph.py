#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from itertools import combinations

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

def gather_tweets(filename, tweets):
    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:
        parsed_json = json.loads(f.read())

        for tweet in parsed_json:
            tweets[tweet["user"]["screen_name"]].append(normalize_text(tweet["text"]))
        return len(parsed_json)

def tokenize(text):
    return word_tokenize(text)

parser = ap.ArgumentParser(description = "Extract tweet text " \
    "from a folder of JSON files containing tweets.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-m", "--min_tweets", type=int, default=0, help = "Minimum "
        "number of tweets required to be included in the analysis. Default is 0 "
        "(no filtering).")


parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the "  \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

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
    if n_tweets < args.min_tweets:
        #sys.stderr.write(k)
        del tweets[k]
    else:
        tweets[k] = " ".join(v)

names = tweets.keys()
news_data = tweets.values()

stop_words = set(map(normalize_text, stopwords.words("spanish"))) | set(["via",
"dia", "uso", "foto", "fotos", "video", "chile", "2015", "2014", "ver", "tras",
"galeria", "informate", "registrate","http", "hoy", "lunes", "martes",
"miercoles", "jueves", "viernes", "sabado", "domingo", "enero",
"febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
"octubre", "noviembre", "diciembre", "vivo", "ahora"] )

vectorizer = TfidfVectorizer(tokenizer=tokenize,
        stop_words=stop_words)

tfidfs = vectorizer.fit_transform(news_data)

sims = ((tfidfs * tfidfs.T).A)

out_arr = []

number_of_sources = len(names)

out_names = []
for i, name in enumerate(names):
    out_names.append({
        "index": i,
        "name" : name,
        "size" : 10})


for i, j in combinations(xrange(number_of_sources), 2):
    out_arr.append({
        "source": i,
        "target"  : j,
        "value": sims[i,j] }
        )

with args.out_file as out_file:
    if args.pretty:
        out_file.write(json.dumps({
            "nodes" : out_names,
            "links" : out_arr },
            indent = 4, separators = (",", ":")))
    else:
        out_file.write(json.dumps({
            "nodes" : out_names,
            "links" : out_arr }))

