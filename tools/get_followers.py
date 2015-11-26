#!/usr/bin/python
import json
import argparse as ap
import os, sys

import warnings
warnings.filterwarnings('error')
date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Computes correlations for a " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read time series from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
import tweepy

consumer_key = "AGIHoohA7Ymc1EQHjYGbLJnR3"
consumer_secret = "36T9pEefyqAN169I6RQP7VWbzCjsoNxxem9RNyzriBDECh01j6"

access_token = "344739490-NMCoBccIwoCv78AXxlO0DtFdJouMyajiOleX3QPs"
access_token_secret = "izjgLNuBUAeBGcVuBKqOenUqLIuVCTU6dBvivY0IdkJUq"


with args.in_file as json_file:
    with args.out_file as out_file:
        parsed_json = json.loads(json_file.read())

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)
        
        for node in parsed_json["nodes"]:
            try:
                user = api.get_user(node["name"])
                node["size"] = user.followers_count
            except:
                sys.stderr.write(node["name"])
                node["size"] = 0



        if args.pretty:
            out_file.write(json.dumps( parsed_json, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps(parsed_json))


