import json, time, re, datetime
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from sngsql.database import Base, db_session, engine
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from nlp_textblob import *
from sqlalchemy import and_
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from config import *
from helper import *


def twitter_crawl():
    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(twitter_access_token, access_token_secret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener)

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
        elif retweeted_status:
            if dict_data["retweeted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["retweeted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('retweeted_status')
            id_str = dict_data["retweeted_status"]["id_str"]
            tweet = dict_data["retweeted_status"]["text"]
            favorite_count = dict_data["retweeted_status"]["favorite_count"]
            share_count = dict_data["retweeted_status"]["retweet_count"]
        elif quoted_status:
            if dict_data["quoted_status"]["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["quoted_status"]["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('quoted_status')
            id_str = dict_data["quoted_status"]["id_str"]
            tweet = dict_data["quoted_status"]["text"]
            favorite_count = dict_data["quoted_status"]["favorite_count"]
            share_count = dict_data["quoted_status"]["retweet_count"]
        else:
            if dict_data["user"]["followers_count"]<MIN_FOLLOWERS or dict_data["user"]["friends_count"]<MIN_FRIENDS:
                print ("less than user metric threshold for storage, skip." + "\n")
                return
            print ('normal_status')
            id_str = dict_data["id_str"]
            tweet = dict_data["text"]
            favorite_count = dict_data["favorite_count"] # should be 0
            share_count = dict_data["retweet_count"] # should be 0

        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        ### Testing time to index postgres ###
        # t = time.process_time() # T start

        (ret, ), = db_session.query(exists().where(Item.item_id==id_str))
        if ret: 
            # quoted tweets contain no new data
            if quoted_status or retweeted_quoted_status:
                print ('Quoted / Retweeted_quoted tweet caught. No update. ID: ' + str(id_str) + '\n')
                return

            # Item already exists. Update share_count, favorite_count, and add retweet growth
            record = db_session.query(Item).filter(Item.item_id==id_str).one()
            record.favorite_count=favorite_count
            record.share_count=share_count
            db_session.flush()

            timedelta = datetime.datetime.utcnow()-datetime.datetime.strptime(str(record.date),'%Y-%m-%d %H:%M:%S')
            minutes_elapsed = td_to_minutes(timedelta)

            # only store one record per minute (only update share count)
            (ret2, ), = db_session.query(exists().where(and_(Retweet_growth.item_id==id_str,
                Retweet_growth.elapsed_time==minutes_elapsed)))
            if ret2:
                record2 = db_session.query(Retweet_growth).filter(and_(Retweet_growth.item_id==id_str),
                    Retweet_growth.elapsed_time==minutes_elapsed).one()
                record2.share_count=share_count
                db_session.flush()
                print ('Retweet caught. Updated favorite, share count, retweet_growth. ID: ' + str(id_str) + '\n')
                return

            try:
                rt = Retweet_growth(item_id=id_str,
                    date_time=now,
                    creation_date=record.date,
                    elapsed_time=minutes_elapsed,
                    share_count=share_count)
                db_session.add(rt)
                db_session.commit()
            except OperationalError:
                db_session.rollback()

            print ('Retweet caught. Updated favorite, share count, and new retweet_growth record. ID: ' + str(id_str) + '\n')
            return

        # elapsed_time = time.process_time() - t # T end
        # print ('pg index time (sec): ' + str(elapsed_time) + '   records in pg: ' + str(db_session.query(Item).count()) + '\n')
        # f = open("tests/pg_index_output.txt", "a")
        # f.write(str(elapsed_time) + '  ' + str(db_session.query(Item).count()) + '\n')
        # f.close()


        # preprocess tweet in nlp_textblob
        expanded_url = None
        if dict_data["entities"]["urls"]:
            expanded_url = str(dict_data["entities"]["urls"][0]["expanded_url"]).lower()
        tweet_dict = analyse_tweet(tweet,expanded_url)

        # could not locate candidate, skip
        if tweet_dict['contestant'] is None:
            print ('CONTESTANT NOT FOUND' + '\n')
            return

        ####### temporary for comparison #######
        tweet_trim = tweet
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet_trim)
        for u in urls:
            tweet_trim = tweet_trim.replace(u,'')
        TB = TextBlob(tweet_trim)

        if TB.sentiment.polarity < 0:
            sentiment_textblob = "negative"
        elif TB.sentiment.polarity == 0:
            sentiment_textblob = "neutral"
        else:
            sentiment_textblob = "positive"

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

        if retweeted_quoted_status:
            user_id = dict_data["retweeted_status"]["quoted_status"]["user"]["id"]
            screen_name = dict_data["retweeted_status"]["quoted_status"]["user"]["screen_name"]
            location = dict_data["retweeted_status"]["quoted_status"]["user"]["location"]
            followers_count = dict_data["retweeted_status"]["quoted_status"]["user"]["followers_count"]
            friends_count = dict_data["retweeted_status"]["quoted_status"]["user"]["friends_count"]
            statuses_count = dict_data["retweeted_status"]["quoted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["retweeted_status"]["quoted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        elif retweeted_status:
            user_id = dict_data["retweeted_status"]["user"]["id"]
            screen_name = dict_data["retweeted_status"]["user"]["screen_name"]
            location = dict_data["retweeted_status"]["user"]["location"]
            followers_count = dict_data["retweeted_status"]["user"]["followers_count"]
            friends_count = dict_data["retweeted_status"]["user"]["friends_count"]
            statuses_count = dict_data["retweeted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["retweeted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        elif quoted_status:
            user_id = dict_data["quoted_status"]["user"]["id"]
            screen_name = dict_data["quoted_status"]["user"]["screen_name"]
            location = dict_data["quoted_status"]["user"]["location"]
            followers_count = dict_data["quoted_status"]["user"]["followers_count"]
            friends_count = dict_data["quoted_status"]["user"]["friends_count"]
            statuses_count = dict_data["quoted_status"]["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["quoted_status"]["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        else:
            user_id = dict_data["user"]["id"]
            screen_name = dict_data["user"]["screen_name"]
            location = dict_data["user"]["location"]
            followers_count = dict_data["user"]["followers_count"]
            friends_count = dict_data["user"]["friends_count"]
            statuses_count = dict_data["user"]["statuses_count"]
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(dict_data["created_at"],'%a %b %d %H:%M:%S +0000 %Y'))
        item_url = 'https://twitter.com/' + str(screen_name) + '/status/' + str(id_str)


        # check tweet is from verified candidate twitter account
        print ('checking for match in: ' + str(CANDIDATE_USERNAMES[tweet_dict['contestant']]['UserName']))
        if str(screen_name) in CANDIDATE_USERNAMES[tweet_dict['contestant']]['UserName']:
            print ('VERIFIED USER')
            verified = True
        else:
            verified = False

        # for retweet growth
        timedelta = datetime.datetime.utcnow()-datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
        minutes_elapsed = td_to_minutes(timedelta)
        # print (str(minutes_elapsed))

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

        tw = Item(message=tweet,
                contestant=tweet_dict['contestant'],
                item_id=id_str,
                item_type=item_type,
                item_url=item_url,
                location=location,
                date=date, # all time is stored at UTC
                source="twitter",
                sentiment=tweet_dict['sentiment'],
                sentiment_textblob=sentiment_textblob,
                # sentiment_bayes=sentiment_bayes,
                polarity=TB.sentiment.polarity, # tbc
                subjectivity=TB.sentiment.subjectivity, # tbc
                favorite_count=favorite_count,
                share_count=share_count,
                user_id=u.id,
                verified_user=verified,
                team=tweet_dict['team'],
                data=json.dumps(data))

        try:
            # words
            words = clean_words(TB) # nlp_textblob.py
            for w in words:
                if len(w)>100:
                    continue
                w_obj = Word(word=w)
                db_session.add(w_obj)
                db_session.commit()
                tw.words.append(w_obj)
                u.words.append(w_obj)

            # hashtags
            if tweet_dict['hashtags']:
                for t in tweet_dict['hashtags']:
                    if len(t)>100:
                        continue
                    t_obj = Hashtag(hashtag=t)
                    db_session.add(t_obj)
                    db_session.commit()
                    tw.hashtags.append(t_obj)
                    u.hashtags.append(t_obj)

            # to add... URL table!!

            # retweet growth
            rt = Retweet_growth(item_id=id_str,
                date_time=now,
                creation_date=date,
                elapsed_time=minutes_elapsed,
                share_count=share_count)

            db_session.add(u)
            db_session.commit()
            db_session.add(tw)
            db_session.commit()
            db_session.add(rt)
            db_session.commit()

        except OperationalError:
            db_session.rollback()


        # output key fields
        print (str(screen_name) + '   My score: ' + str(tweet_dict['sentiment']) + '   TB score: ' + sentiment_textblob ) # + '   Bayes score: ' + sentiment_bayes)
        print ('Tweet ID: ' + str(id_str))
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
            print ('protocol error. sleeping 5 seconds... zzz...')
            time.sleep(5)
            continue
    # twitter_crawl()




