import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from elasticsearch import Elasticsearch

# import twitter keys and tokens
from config import *

# create instance of elasticsearch
es = Elasticsearch()


class TweetStreamListener(StreamListener):

    # on success
    def on_data(self, data):

        # decode json
        dict_data = json.loads(data)

        #skip tweets with users with <100 followers
        if dict_data["user"]["followers_count"]<2000 or dict_data["user"]["friends_count"]<500:
            return

        #need to check for duplications here!!

        # pass tweet into TextBlob
        tweet = TextBlob(dict_data["text"])

        # determine if sentiment is positive, negative, or neutral
        if tweet.sentiment.polarity < 0:
            sentiment = "negative"
        elif tweet.sentiment.polarity == 0:
            sentiment = "neutral"
        else:
            sentiment = "positive"

        # output key fields
        print (dict_data["user"]["screen_name"] + ' ' + str(sentiment) + ' ' + str(tweet.sentiment.polarity))
        print ('Friends Count: ' + str(dict_data["user"]["friends_count"]) + '    Followers Count: ' + str(dict_data["user"]["followers_count"]))
        print (dict_data["text"] + '\n')


        # add tweet data and sentiment info to elasticsearch
        es.index(index="1", #event_id
                 doc_type="item",
                 body={"user_id": dict_data["user"]["id"],
                        "screen_name": dict_data["user"]["screen_name"],
                        "location": dict_data["user"]["location"],
                        "followers_count": dict_data["user"]["followers_count"],
                        "friends_count": dict_data["user"]["friends_count"],
                        "favorite_count": dict_data["favorite_count"], #USELESS!!
                        "retweet_count": dict_data["retweet_count"], #USELESS!!
                        "date": dict_data["created_at"],
                        "message": dict_data["text"],
                        "polarity": tweet.sentiment.polarity,
                        "subjectivity": tweet.sentiment.subjectivity,
                        "sentiment": sentiment,
                        "source" : 'twitter'})
                        # # source url, image, vide

                        # if retweeted_status exists
                        #     use retweeted_status for
                        #         retweeted_status-id_str
                        #         retweeted_status-user-screenname

                        # item_url = 'https://twitter.com/' + dict_data["user"]["screen_name"] + '/status/' + id_str
        return True

    # on failure
    def on_error(self, status):
        print (status)

if __name__ == '__main__':

    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener)

    # search twitter for keywords
    stream.filter(languages=['en'], track=['game of thrones','jon snow,daenerys,stannis,arya stark,sansa stark,tyrion,lannister,cersei'])

