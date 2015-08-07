import json, time, re, datetime, math, requests
import urllib.request
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
from collections import deque
from words import *
from config import *
from helper import *
from distant_supervised_tweet_classification import *
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


def twitter_crawl():
    # for duplication tweet check
    global queue
    queue = deque([])

    # for bayes word count
    global hash_wordcount
    hash_wordcount = get_wordcount_data()

    # create instance of the tweepy tweet stream listener with keys and search filter
    listener = TweetStreamListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(twitter_access_token, access_token_secret)
    stream = Stream(auth, listener)
    stream.filter(languages=['en'], track=SEARCH_TERM)

    # api used for checking rate limits
    global api
    api = API(auth)
    


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
            key_fields = dict_data["retweeted_status"]["quoted_status"]
        elif retweeted_status:
            if dict_data["retweeted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["retweeted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('retweeted_status')
            key_fields = dict_data["retweeted_status"]
        elif quoted_status:
            if dict_data["quoted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["quoted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('quoted_status')
            key_fields = dict_data["quoted_status"]
        else:
            if dict_data["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('normal_status')
            key_fields = dict_data

        id_str = key_fields["id_str"]
        tweet = key_fields["text"]
        if retweeted_quoted_status or retweeted_status:
            favorite_count = dict_data["retweeted_status"]["favorite_count"]
            share_count = dict_data["retweeted_status"]["retweet_count"]
        else:
            favorite_count = key_fields["favorite_count"]
            share_count = key_fields["retweet_count"]
        user_id = key_fields["user"]["id"]
        screen_name = key_fields["user"]["screen_name"]
        location = key_fields["user"]["location"]
        followers_count = key_fields["user"]["followers_count"]
        friends_count = key_fields["user"]["friends_count"]
        statuses_count = key_fields["user"]["statuses_count"]
        date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(key_fields["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
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
        important = 'f'
        if share_count>minimum_rt:
            important = 't'


        # check if item already stored
        try:
            record = db_session.query(Item).filter(Item.item_id==id_str).one()
            if quoted_status or retweeted_quoted_status:
                # quoted tweets contain no new data
                print ('Quoted / Retweeted_quoted tweet caught. No update. ID: ' + str(id_str) + '\n')
                return
            record.favorite_count=favorite_count
            record.share_count=share_count
            db_session.commit()

            # publish to pubnub
            # pubnub_object = ({'sentiment': record.sentiment, 'group_item_id': record.group_item_id, 
            #         'item_id': id_str, 'source': 'twitter', 'favorite_count': favorite_count,
            #         'share_count': share_count, 'contestant': record.contestant, 
            #         'item_url': item_url, 'date': date, 'important': important})
            # pubnub.publish(channel='pubnub-sng',message=pubnub_object)
            print ('Retweet caught. Updated favorite and share count record. ID: ' + str(id_str) + '\n')
            return
        except NoResultFound:
            pass
        

        # queue storing previous 200 tweet texts for duplication check
        if tweet in queue:
            print ('Tweet already processed, repeat found in queue, skip.' + '\n')
            return
        queue.append(tweet)
        if len(queue)>200:
            queue.popleft()


        # preprocessing tweet in nlp_textblob
        try:
            expanded_url = str(dict_data["entities"]["urls"][0]["expanded_url"]).lower()
        except IndexError:
            expanded_url = None

        tweet_dict = analyse_tweet(tweet,expanded_url)
        if tweet_dict['contestant'] is None:
            print ('CONTESTANT NOT FOUND' + '\n')
            return
        words = clean_words(tweet_dict['tb_words'],tweet_dict['hashtags'],tweet_dict['shoutouts'])

        # distant supervised tweet classification bayes probability
        sentiment_bayes = accumulate_prob(hash_wordcount,words)

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
            important = 't'
        else:
            verified = False


        # publish to pubnub
        # print (pubnub_words)
        # pubnub_object = ({'sentiment': tweet_dict['sentiment'], 'group_item_id': group_item_id, 
        # 'item_id': id_str, 'source': 'twitter', 'favorite_count': favorite_count,
        # 'share_count': share_count, 'contestant': tweet_dict['contestant'], 
        # 'item_url': item_url, 'date': date, 'important': important})
        # pubnub.publish(channel='pubnub-sng',message=pubnub_object)


        # select correct fields
        if "media" not in dict_data["entities"]:
            item_type = "text"
        else:
            if dict_data["entities"]["media"][0]["type"] == "photo":
                item_type = "image"
            else:
                item_type = dict_data["entities"]["media"][0]["type"]


        # output key fields
        print (str(screen_name) + '   My score: ' + str(tweet_dict['sentiment']) + '   TB score: ' + tweet_dict['tb_sentiment'] + '   Bayes score: ' + sentiment_bayes)
        print ('Tweet ID: ' + str(id_str) + '   ' + str(minutes_elapsed) + ' minutes ago')
        print ('Friends Count: ' + str(friends_count) + '    Followers Count: ' + str(followers_count))
        print ('Retweet Count: ' + str(share_count) + '    Favorite Count: ' + str(favorite_count))
        print (str(tweet))
        print (item_url)

        # send to server
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
            'sentiment_bayes': sentiment_bayes,
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
        print(r.text + '\n')

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




