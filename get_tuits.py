#!/usr/bin/python
import sys
import time

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
import tweepy

consumer_key = "nWmMC7VZZ2Ae3ZlINMbvurrUb"
consumer_secret = "c4qPBpmzDBrXznx17pgydy4FdQwUC3jJ780U6yx8MKEbsD4k2Y"

access_token = "344739490-NMCoBccIwoCv78AXxlO0DtFdJouMyajiOleX3QPs"
access_token_secret = "izjgLNuBUAeBGcVuBKqOenUqLIuVCTU6dBvivY0IdkJUq"

with open(sys.argv[1]) as news_file:

    news_accounts = news_file.readline().split(",")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    for handle in news_accounts:

        print "==== " + handle + " ===="
    
        try:
            for status in tweepy.Cursor(api.user_timeline, id=handle, page = 3).items():
                print status.text
        except:
            time.sleep(960)

