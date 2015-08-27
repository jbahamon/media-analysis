#!/usr/bin/python

import json
import argparse as ap
import os, sys
from collections import defaultdict
from unidecode import unidecode
import string, codecs, re, nltk
from sklearn.feature_extraction.text import TfidfVectorizer


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

def gather_tweets(filename, out_file):
    with codecs.open(os.path.join(folder, filename), "r", "utf-8") as f:
        parsed_json = json.loads(f.read())
        for tweet in parsed_json:
            out_file.write(normalize_text(tweet["text"]) + "\n")

def tokenize(text):
    return nltk.tokenize.word_tokenize(text)

parser = ap.ArgumentParser(description = "Extract tweet text " \
    "from a folder of JSON files containing tweets.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

folder = args.folder

files = [ filename for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]

with args.out_file as out_file:
    for f in files:
        gather_tweets(f, out_file)

