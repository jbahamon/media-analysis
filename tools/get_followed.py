#!/usr/bin/python
import json
import os, sys
import argparse as ap
import warnings

key_file = "../keys.json"
warnings.filterwarnings('error')

with open(key_file,"r") as f:
    params = json.loads(f.read())

    consumer_key = params["consumer_key"]
    consumer_secret = params["consumer_secret"]

    access_token = params["access_token"]
    access_token_secret = params["access_token_secret"]

date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Gets Twitter IDs for a JSON objects"
        " with an 'outlets' property.")

parser.add_argument( "username", type=str, help = "The username to find friends"
        " for.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

args = parser.parse_args()

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
import tweepy

with args.out_file as out_file:

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    c = tweepy.Cursor(api.friends_ids, screen_name=args.username);
    
    ids = []

    for page in c.pages():
        while (True): 
            try:
                ids.extend(page)
                break
            except tweepy.RateLimitError as e:
                sys.stderr.write(str(e))
                sleep(60)

    if args.pretty:
        out_file.write(json.dumps(ids, \
            indent = 4, separators = (",",":")))
    else:
        out_file.write(json.dumps(ids))


