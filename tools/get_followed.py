#!/usr/bin/python

from flask import Flask
from flask.ext.cors import CORS, cross_origin

import json
import sys
import warnings
import tweepy
warnings.filterwarnings('error')

key_file = "../keys.json"

with open(key_file,"r") as f:
    params = json.loads(f.read())

    consumer_key = params["consumer_key"]
    consumer_secret = params["consumer_secret"]

    access_token = params["access_token"]
    access_token_secret = params["access_token_secret"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

app = Flask(__name__)
cors = CORS(app, resources={r"/foo": {"origins": "*"}})
app.config['SECRET_KEY'] = 'meowth thats right'
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/*": {"origins": "localhost"},})

@app.route('/screen_name/<screen_name>')
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def getFriendListFromScreenName(screen_name):
    c = tweepy.Cursor(api.friends_ids, screen_name=screen_name);
    friend_list = getFriendListFromCursor(c)
    return json.dumps(friend_list)

@app.route('/user_id/<user_id>')
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def getFriendListFromUserId(user_id):
    c = tweepy.Cursor(api.friends_ids, user_id=user_id);
    friend_list = getFriendListFromCursor(c)
    return json.dumps(friend_list)

def getFriendListFromCursor(c):
    ids = []

    for page in c.pages():
        while (True): 
            try:
                ids.extend(page)
                break
            except tweepy.RateLimitError as e:
                sys.stderr.write(str(e))
                sleep(60)
    
    return ids


if __name__ == "__main__":
        app.run()
