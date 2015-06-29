import json
import time
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from sngsql.database import Base, db_session, engine
from sngsql.model import Hashtag, Item, User, Word
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
# from elasticsearch import Elasticsearch
# from elasticsearch_dsl import Search

# import twitter keys and tokens
from config import *

# create instance of elasticsearch
# es = Elasticsearch()

#change ID, search terms, min reqs for each event
EVENT_ID = 1
SEARCH_TERM = (['Bobby Jindal','Donald Trump','Jeb Bush','Rick Perry',
    'Lindsey Graham','George Pataki','Rick Santorum','Mike Huckabee','Marco Rubio',
    'Rand Paul','Ted Cruz','Chris Christie','Scott Walker','Hillary Clinton'])
MIN_FOLLOWERS = 1000 #2000
MIN_FRIENDS = 500 #500

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

        # check if retweet
        retweeted_status = bool("retweeted_status" in dict_data)

        # check if duplication and skip tweets with users with less than req threshold
        if not retweeted_status:
            if dict_data["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            id_str = dict_data["id_str"]

        else:
            if dict_data["retweeted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["retweeted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return            
            id_str = dict_data["retweeted_status"]["id_str"]



        ### Testing time to index postgres ###
        t = time.process_time() # T start

        (ret, ), = db_session.query(exists().where(Item.item_id==str(id_str)))
        if ret: 
            # Item already exists. Update share_count & favorite_count
            if retweeted_status:
                record = db_session.query(Item).filter(Item.item_id==id_str).one()
                record.favorite_count=dict_data["retweeted_status"]["favorite_count"]
                record.share_count=dict_data["retweeted_status"]["retweet_count"]
                db_session.flush()
            print ('Duplication caught. Updated favorite & share count. ID: ' + str(id_str) + '\n')
            return

        elapsed_time = time.process_time() - t # T end
        print ('pg index time (sec): ' + str(elapsed_time) + '   records in pg: ' + str(db_session.query(Item).count()) + '\n')
        f = open("tests/pg_index_output.txt", "a")
        f.write(str(elapsed_time) + '  ' + str(db_session.query(Item).count()) + '\n')
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
        item_id = id_str
        item_url = 'https://twitter.com/' + str(screen_name) + '/status/' + str(item_id)

        try:
            u = db_session.query(User).filter_by(uid=str(user_id)).one()
        except NoResultFound:
            u = User(uid=user_id,
                    screen_name=screen_name,
                    followers_count=followers_count,
                    friends_count=friends_count,
                    statuses_count=statuses_count,
                    rank=1)
            db_session.add(u)
            db_session.commit()

        tw = Item(message=message,
                item_id=item_id,
                item_type=item_type,
                item_url=item_url,
                location=location,
                date=date,
                source="twitter",
                polarity=tweet.sentiment.polarity,
                subjectivity=tweet.sentiment.subjectivity,
                sentiment=sentiment,
                favorite_count=favorite_count,
                share_count=share_count,
                user_id=u.id,
                data=json.dumps(data))

        try:
            # words
            words = tw.message.split()
            for w in words:
                try:
                    w_obj = db_session.query(Word).filter(Word.word == w).one()
                except MultipleResultsFound:
                    pass
                except NoResultFound:
                    w_obj = Word(word=w)
                    db_session.add(w_obj)
                    db_session.commit()
                    tw.words.append(w_obj)
                    u.words.append(w_obj)

            # hashtags
            if dict_data["entities"]["hashtags"]:
                tags = dict_data["entities"]["hashtags"]
                for t in tags:
                    t_obj = Hashtag(hashtag=t["text"])
                    db_session.add(t_obj)
                    db_session.commit()
                    tw.hashtags.append(t_obj)
                    u.hashtags.append(t_obj)

            db_session.add(u)
            db_session.commit()
            db_session.add(tw)
            db_session.commit()
        except OperationalError:
            db_session.rollback()


        # output key fields
        item_url = 'https://twitter.com/' + str(screen_name) + '/status/' + str(item_id)
        print (str(screen_name) + ' ' + str(sentiment) + ' ' + str(tweet.sentiment.polarity))
        print ('Tweet ID: ' + str(item_id))
        print ('Friends Count: ' + str(friends_count) + '    Followers Count: ' + str(followers_count))
        print ('Retweet Count: ' + str(share_count) + '    Favorite Count: ' + str(favorite_count))
        print (str(message))
        item_tag = ""
        if dict_data["entities"]["hashtags"]:
            for t in dict_data["entities"]["hashtags"]:
                item_tag = t["text"] + " " + item_tag
            item_tag.strip()
        print ('Tags: ' + item_tag)
        print (item_url + '\n')

        return True


    # on failure
    def on_error(self, status):
        print (str(status) + ' error with connection')

if __name__ == '__main__':

    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(twitter_access_token, access_token_secret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener)

    # search twitter for keywords
    stream.filter(languages=['en'], track=SEARCH_TERM)

