#!/usr/bin/python
import json
import argparse as ap
import os, sys

import warnings
warnings.filterwarnings('error')

key_file = "../keys.json"

with open(key_file,"r") as f:
    params = json.loads(f.read())

    consumer_key = params["consumer_key"]
    consumer_secret = params["consumer_secret"]

    access_token = params["access_token"]
    access_token_secret = params["access_token_secret"]

date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Gets Twitter IDs for a JSON objects"
        " with an 'outlets' property.")

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

with args.in_file as json_file:
    with args.out_file as out_file:
        parsed_json = json.loads(json_file.read())

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)
        
        ids = dict()
        for username in parsed_json["outlets"]:
            try:
                user = api.get_user(username)
                ids[str(user.id)] = username
            except:
                sys.stderr.write("Failed to obtain %s.\n" % username)

        parsed_json["ids"] = ids;

        if args.pretty:
            out_file.write(json.dumps( parsed_json, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps(parsed_json))


