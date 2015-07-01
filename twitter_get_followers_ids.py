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
#can use userid or sn (e.g. user_id=12345)
for page in tweepy.Cursor(api.followers_ids, screen_name="gymboxofficial").pages():
    ids.extend(page)
    print (str(ids))
    time.sleep(60)

print (len(ids))

# naive ranking...
# favorite count
# retweat count

# friends count
# followers count
# status count
# tweet_score = (comment_percentile_weight * comment_percentile) + (views_percentile_weight * views_percentile)
