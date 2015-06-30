import time
from tweepy import OAuthHandler
import tweepy

# import twitter keys and tokens
from config import *

# set twitter keys/tokens
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(twitter_access_token, access_token_secret)



api = tweepy.API(auth)

ids = []
for page in tweepy.Cursor(api.followers_ids, screen_name="gymboxofficial").pages():
    ids.extend(page)
    print (str(ids))
    time.sleep(60)

print (len(ids))



