import json, time, re, datetime, math, requests
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from sngsql.database import Base, db_session, engine
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from nlp_textblob import *
from sqlalchemy import and_
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from pubnub import Pubnub
from config import *
from helper import *

import urllib.request

api = None

# pubnub functions
pubnub = Pubnub(publish_key=pubnub_publish_key, subscribe_key=pubnub_subscribe_key)
def callback(message, channel):
    print(message)
def error(message):
    print("PUBNUB ERROR : " + str(message))
def connect(message):
    print("PUBNUB CONNECTED")
    pubnub.publish(channel='pubnub-sng', message='Hello from the PubNub Python SDK')
def reconnect(message):
    print("PUBNUB RECONNECTED")
def disconnect(message):
    print("PUBNUB DISCONNECTED")
pubnub.subscribe(channels='pubnub-sng', callback=callback, error=callback,
                 connect=connect, reconnect=reconnect, disconnect=disconnect)


def twitter_crawl():
    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()
    # set twitter keys/tokens
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(twitter_access_token, access_token_secret)
    # create instance of the tweepy stream
    stream = Stream(auth, listener)
    # api used for checking rate limits
    global api 
    api = API(auth)
    # search twitter for keywords
    stream.filter(languages=['en'], track=SEARCH_TERM)


class TweetStreamListener(StreamListener):

    # on success
    def on_data(self, data):
        # sometimes tweepy send NoneType objects
        if data is None:
            return

        # decode json
        dict_data = json.loads(data)
        
        if "user" not in dict_data:
            print ("invalid format: no user found, skip." + "\n")
            return

        # check if retweet/quote/retweet-quote
        retweeted_quoted_status = False
        retweeted_status = bool("retweeted_status" in dict_data)
        if retweeted_status:
            retweeted_quoted_status = bool("quoted_status" in dict_data["retweeted_status"])
        quoted_status = bool("quoted_status" in dict_data)


        # check if duplication and skip tweets with users with less than req threshold
        if retweeted_quoted_status:
            if dict_data["retweeted_status"]["quoted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["retweeted_status"]["quoted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('retweeted_quoted_status')
            id_str = dict_data["retweeted_status"]["quoted_status"]["id_str"]
            tweet = dict_data["retweeted_status"]["quoted_status"]["text"]
            favorite_count = dict_data["retweeted_status"]["favorite_count"] # pull fav count from retweet level
            share_count = dict_data["retweeted_status"]["retweet_count"] # pull share count from retweet level
            user_id = dict_data["retweeted_status"]["quoted_status"]["user"]["id"]
            screen_name = dict_data["retweeted_status"]["quoted_status"]["user"]["screen_name"]
            location = dict_data["retweeted_status"]["quoted_status"]["user"]["location"]
            followers_count = dict_data["retweeted_status"]["quoted_status"]["user"]["followers_count"]
            friends_count = dict_data["retweeted_status"]["quoted_status"]["user"]["friends_count"]
            statuses_count = dict_data["retweeted_status"]["quoted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["retweeted_status"]["quoted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        elif retweeted_status:
            if dict_data["retweeted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["retweeted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('retweeted_status')
            id_str = dict_data["retweeted_status"]["id_str"]
            tweet = dict_data["retweeted_status"]["text"]
            favorite_count = dict_data["retweeted_status"]["favorite_count"]
            share_count = dict_data["retweeted_status"]["retweet_count"]
            user_id = dict_data["retweeted_status"]["user"]["id"]
            screen_name = dict_data["retweeted_status"]["user"]["screen_name"]
            location = dict_data["retweeted_status"]["user"]["location"]
            followers_count = dict_data["retweeted_status"]["user"]["followers_count"]
            friends_count = dict_data["retweeted_status"]["user"]["friends_count"]
            statuses_count = dict_data["retweeted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["retweeted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        elif quoted_status:
            if dict_data["quoted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["quoted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('quoted_status')
            id_str = dict_data["quoted_status"]["id_str"]
            tweet = dict_data["quoted_status"]["text"]
            favorite_count = dict_data["quoted_status"]["favorite_count"]
            share_count = dict_data["quoted_status"]["retweet_count"]
            user_id = dict_data["quoted_status"]["user"]["id"]
            screen_name = dict_data["quoted_status"]["user"]["screen_name"]
            location = dict_data["quoted_status"]["user"]["location"]
            followers_count = dict_data["quoted_status"]["user"]["followers_count"]
            friends_count = dict_data["quoted_status"]["user"]["friends_count"]
            statuses_count = dict_data["quoted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["quoted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        else:
            if dict_data["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('normal_status')
            id_str = dict_data["id_str"]
            tweet = dict_data["text"]
            favorite_count = dict_data["favorite_count"] # should be 0
            share_count = dict_data["retweet_count"] # should be 0
            user_id = dict_data["user"]["id"]
            screen_name = dict_data["user"]["screen_name"]
            location = dict_data["user"]["location"]
            followers_count = dict_data["user"]["followers_count"]
            friends_count = dict_data["user"]["friends_count"]
            statuses_count = dict_data["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        item_url = 'https://twitter.com/' + str(screen_name) + '/status/' + str(id_str)

        # minumum threshold by elapsed time
        timedelta = datetime.datetime.utcnow()-datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
        minutes_elapsed = td_to_minutes(timedelta)
        if minutes_elapsed<20:
            minimum_rt =  3*minutes_elapsed
        elif minutes_elapsed<120:
            minimum_rt =  80*math.log(minutes_elapsed)-180
        else:
            minimum_rt = 233

        try:
            record = db_session.query(Item).filter(Item.item_id==id_str).one()
            if quoted_status or retweeted_quoted_status:
                # quoted tweets contain no new data
                print ('Quoted / Retweeted_quoted tweet caught. No update. ID: ' + str(id_str) + '\n')
                return
            record.favorite_count=favorite_count
            record.share_count=share_count
            db_session.flush()
            if 1:
            # if share_count>minimum_rt:
                print ('PUBLISHING TO PUBNUB!')
                pubnub_object = ({'sentiment': record.sentiment, 'group_item_id': record.group_item_id, 
                    'item_id': id_str, 'source': 'twitter', 'favorite_count': favorite_count,
                    'share_count': share_count, 'contestant': record.contestant, 
                    'item_url': item_url, 'date': date})
                pubnub.publish(channel='pubnub-sng',message=pubnub_object)
            print ('Retweet caught. Updated favorite and share count record. ID: ' + str(id_str) + '\n')
            return
        except NoResultFound:
            pass
        

        # preprocessing tweet in nlp_textblob
        try:
            expanded_url = str(dict_data["entities"]["urls"][0]["expanded_url"]).lower()
        except IndexError:
            expanded_url = None
        tweet_dict = analyse_tweet(tweet,expanded_url)
        if tweet_dict['contestant'] is None:
            print ('CONTESTANT NOT FOUND' + '\n')
            return
        words = clean_words(tweet_dict['tb_words'],tweet_dict['hashtags'])
        
        # for group_item_id
        url_record = db_session.query(Url).filter(Url.url==expanded_url).first()
        try:
            group_item_id = url_record.item_id
        except AttributeError:
            group_item_id = id_str

        # check tweet is from verified candidate twitter account
        if str(screen_name) in CANDIDATE_USERNAMES[tweet_dict['contestant']]['UserName']:
            print ('VERIFIED USER')
            verified = True
        else:
            verified = False

        # publish to pubnub
        # if (share_count>minimum_rt or verified):
        if 1:
            print ('PUBLISHING TO PUBNUB!')
            pubnub_object = ({'sentiment': tweet_dict['sentiment'], 'group_item_id': group_item_id, 
        'item_id': id_str, 'source': 'twitter', 'favorite_count': favorite_count,
        'share_count': share_count, 'contestant': tweet_dict['contestant'], 
        'item_url': item_url, 'date': date})
            pubnub.publish(channel='pubnub-sng',message=pubnub_object)

        ####################################
        # bayes = TextBlob(tweet_trim, analyzer=NaiveBayesAnalyzer())
        # if abs(bayes.sentiment.p_pos-bayes.sentiment.p_neg) < .2:
        #     sentiment_bayes = "neutral"
        # elif bayes.sentiment.classification == 'neg':
        #     sentiment_bayes = "negative"
        # elif bayes.sentiment.classification == 'pos':
        #     sentiment_bayes = "positive"
        # else:
        #     sentiment_bayes = 'Uhoh'
        ####################################

        # select correct fields
        if "media" not in dict_data["entities"]:
            item_type = "text"
        else:
            if dict_data["entities"]["media"][0]["type"] == "photo":
                item_type = "image"
            else:
                item_type = dict_data["entities"]["media"][0]["type"]

        item_data = ({'uid':user_id,
            'screen_name':screen_name,
            'followers_count':followers_count,
            'friends_count':friends_count,
            'statuses_count':statuses_count,
            'rank': 1, 
            'message': tweet,
            'contestant': tweet_dict['contestant'],
            'item_id': id_str,
            'group_item_id': group_item_id,
            'item_type': item_type,
            'item_url': item_url,
            'location': location,
            'date': date, 
            'source': "twitter",
            'sentiment': tweet_dict['sentiment'],
            'sentiment_textblob': tweet_dict['tb_sentiment'],
            'polarity': tweet_dict['tb_polarity'],
            'subjectivity': tweet_dict['tb_subjectivity'], 
            'favorite_count': favorite_count,
            'share_count': share_count,
            'verified_user': verified,
            'team': tweet_dict['team'],
            'data': json.dumps(data),
            'words': words,
            'hashtags': tweet_dict['hashtags'],
            'expanded_url': expanded_url})

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(URL + 'api/input_data/', data=json.dumps(item_data), headers=headers)
        print (r)
        print(r.text)



        # rate limit for oembed is 180 per 15 minutes
        # https://dev.twitter.com/rest/reference/get/statuses/oembed
        # t = time.process_time()
        # limits = api.rate_limit_status()
        # remain_oembed = limits['resources']['statuses']['/statuses/oembed']['remaining']
        # print (remain_oembed)
        # elapsed_time = time.process_time() - t
        # print ('api status check (sec): ' + str(elapsed_time) + '\n')



        # output key fields
        print (str(screen_name) + '   My score: ' + str(tweet_dict['sentiment']) + '   TB score: ' + tweet_dict['tb_sentiment'] ) # + '   Bayes score: ' + sentiment_bayes)
        print ('Tweet ID: ' + str(id_str) + '   ' + str(minutes_elapsed) + ' minutes ago')
        print ('Friends Count: ' + str(friends_count) + '    Followers Count: ' + str(followers_count))
        print ('Retweet Count: ' + str(share_count) + '    Favorite Count: ' + str(favorite_count))
        print (str(tweet))

        print (item_url + '\n')

        return True


    # on failure
    def on_error(self, status):
        print (str(status) + ' error with connection')

if __name__ == '__main__':
    while 1:
        try:
            twitter_crawl()
        except:
            print ('Error. sleeping 5 seconds... zzz...')
            time.sleep(5)
            continue
    # twitter_crawl()




