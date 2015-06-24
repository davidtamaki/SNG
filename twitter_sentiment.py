import json
import time
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# import twitter keys and tokens
from config import *

# create instance of elasticsearch
es = Elasticsearch()

#change ID, search terms, min reqs for each event
EVENT_ID = 1
SEARCH_TERM = ['confederate flag']  # ['game of thrones','jon snow,daenerys,stannis,arya stark,sansa stark,tyrion,lannister,cersei']
MIN_FOLLOWERS = 1000 #2000
MIN_FRIENDS = 300 #500

class TweetStreamListener(StreamListener):

    # on success
    def on_data(self, data):
        global first_it

        # decode json
        dict_data = json.loads(data)

        # skip tweets with users with <2000 followers and <500 friends
        if "user" not in dict_data:
            print ("invalid format: no user found, skip.")
            return
        if dict_data["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["user"]["friends_count"]<MIN_FRIENDS:
            print ("less than user metric threshold for storage, skip.")
            return

        # check if retweet
        retweeted_status = bool("retweeted_status" in dict_data)

        # check if duplication and skip
        if not retweeted_status:
            id_str = dict_data["id_str"]
        else:
            id_str = dict_data["retweeted_status"]["id_str"]

        if first_it == False:
        ### Testing time to index es ###
            t = time.process_time() # T start
            s = Search(using=es, index=str(EVENT_ID)) \
                .query("match", item_id=str(id_str))
            response = s.execute()

            elapsed_time = time.process_time() - t # T end

            s2 = Search(using=es, index=str(EVENT_ID))
            all_records = s2.execute()

            # empty sequences (strings, lists, tuples) are false 
            if response:
                print ('Duplication caught. Not added to db. ID: ' + str(id_str) + '\n')
                return

            print ('es index time (sec): ' + str(elapsed_time) + '   records in es: ' + str(all_records.hits.total) + '\n')
            f = open("es_index_output.txt", "a")
            f.write(str(elapsed_time) + '  ' + str(all_records.hits.total) + '\n')
            f.close()


        # pass tweet into TextBlob
        if not retweeted_status:
            tweet = TextBlob(dict_data["text"])
        else:
            tweet = TextBlob(dict_data["retweeted_status"]["text"])

        # determine if sentiment is positive, negative, or neutral
        if tweet.sentiment.polarity < 0:
            sentiment = "negative"
        elif tweet.sentiment.polarity == 0:
            sentiment = "neutral"
        else:
            sentiment = "positive"

        # select correct fields
        if "media" not in dict_data["entities"]:
            item_type = "text"
        else:
            if dict_data["entities"]["media"][0]["type"] == "photo":
                item_type = "image"
            else:
                item_type = dict_data["entities"]["media"][0]["type"]

        if not retweeted_status:
            item_id = dict_data["id_str"]
            user_id = dict_data["user"]["id"]
            screen_name = dict_data["user"]["screen_name"]
            location = dict_data["user"]["location"]
            followers_count = dict_data["user"]["followers_count"]
            friends_count = dict_data["user"]["friends_count"]
            statuses_count = dict_data["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
            favorite_count = dict_data["favorite_count"] #should be 0
            share_count = dict_data["retweet_count"] #should be 0
            message = dict_data["text"]
        else:
            item_id = dict_data["retweeted_status"]["id_str"]
            user_id = dict_data["retweeted_status"]["user"]["id"]
            screen_name = dict_data["retweeted_status"]["user"]["screen_name"]
            location = dict_data["retweeted_status"]["user"]["location"]
            followers_count = dict_data["retweeted_status"]["user"]["followers_count"]
            friends_count = dict_data["retweeted_status"]["user"]["friends_count"]
            statuses_count = dict_data["retweeted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["retweeted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
            favorite_count = dict_data["retweeted_status"]["favorite_count"]
            share_count = dict_data["retweeted_status"]["retweet_count"]
            message = dict_data["retweeted_status"]["text"]


        # output key fields
        item_url = 'https://twitter.com/' + str(screen_name) + '/status/' + str(item_id)
        print (str(screen_name) + ' ' + str(sentiment) + ' ' + str(tweet.sentiment.polarity))
        print ('Tweet ID: ' + str(item_id))
        print ('Friends Count: ' + str(friends_count) + '    Followers Count: ' + str(followers_count))
        print ('Retweet Count: ' + str(share_count) + '    Favorite Count: ' + str(favorite_count))
        print (str(message))
        print (item_url + '\n')


        # add tweet data and sentiment info to elasticsearch
        es.index(index=str(EVENT_ID),
                 doc_type="item",
                 body={
                        "polarity": tweet.sentiment.polarity,
                        "subjectivity": tweet.sentiment.subjectivity,
                        "sentiment": sentiment,
                        "item_type": item_type,
                        "item_id": item_id,
                        "user_id": user_id,
                        "screen_name": screen_name,
                        "location": location,
                        "followers_count": followers_count,
                        "friends_count": friends_count,
                        "statuses_count": statuses_count,
                        "date": date,
                        "favorite_count": favorite_count,
                        "share_count": share_count,
                        "message": message,
                        "source" : "twitter",
                        "item_url": item_url})

        first_it = False
        return True

    # on failure
    def on_error(self, status):
        print (str(status) + ' error with connection')

if __name__ == '__main__':

    first_it = True
    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(twitter_access_token, access_token_secret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener)

    # search twitter for keywords
    stream.filter(languages=['en'], track=SEARCH_TERM)

