#!/usr/bin/python
import sys
import time

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
import tweepy

consumer_key = "AGIHoohA7Ymc1EQHjYGbLJnR3"
consumer_secret = "36T9pEefyqAN169I6RQP7VWbzCjsoNxxem9RNyzriBDECh01j6"

access_token = "344739490-NMCoBccIwoCv78AXxlO0DtFdJouMyajiOleX3QPs"
access_token_secret = "izjgLNuBUAeBGcVuBKqOenUqLIuVCTU6dBvivY0IdkJUq"

with open(sys.argv[1]) as news_file:

    news_accounts = news_file.readlines()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    user = api.get_user("tuttikiwi")
    for handle in news_accounts:

	user = api.get_user(handle)
    
	print handle.strip() + " " + str(user.followers_count)
