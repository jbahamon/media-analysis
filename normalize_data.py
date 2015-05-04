#!/usr/bin/python
import sys
from unidecode import unidecode
import string 
import codecs

remove_punctuation_map = string.maketrans(string.punctuation, ' '*len(string.punctuation))

acc = ""
with codecs.open(sys.argv[1], "r", "utf-8") as raw_file:
    with open(sys.argv[2], "w") as names_file:
        with open(sys.argv[3], "w") as tweets_file:
            for line in raw_file.readlines():
                if line.startswith("===="):
                    if len(acc) > 0:
                        names_file.write(line.strip() + "\n")
                        tweets_file.write(acc + "\n")
                    acc = ""
                else:
                    acc = acc + " " + \
                    unidecode(line).strip().lower().translate(remove_punctuation_map)
