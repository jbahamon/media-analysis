#!/usr/bin/python
import json
import argparse as ap
import os, sys

import warnings
warnings.filterwarnings('error')
date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Gets all followers " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The file to read outlet names from, one name per line. If not specified, standard " \
        "input will be used.")

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


with args.in_file as in_file:
    with args.out_file as out_file:
        outlet_names = in_file.readlines()

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth, wait_on_rate_limit=True,
                wait_on_rate_limit_notify=True)

        followers = dict()
        for outlet in outlet_names:
            out_file.write(outlet)

            for page in tweepy.Cursor(api.followers_ids, screen_name=outlet).pages():
                out_file.writelines(map(lambda x: str(x) + "\n", page))

