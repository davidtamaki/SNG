from instagram.client import InstagramAPI
from textblob import TextBlob
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import json
import time

# import instagram keys and tokens
from config import *

# create instance of elasticsearch
es = Elasticsearch()

#change ID and search terms for each event
EVENT_ID = 1
SEARCH_TERM = 'confederateflag'
MIN_FOLLOWERS = 100
MIN_LIKES = 0
SLEEP = 20

api = InstagramAPI(client_id=client_id, client_secret=client_secret,client_ips= client_ip,access_token= instagram_access_token)


def instagram():
    first_it = True
    while 1:

        #returns 33 objects at a time, cannot get pagination to work (count set to 40)
        recent_media, next_ = api.tag_recent_media(tag_name=SEARCH_TERM, count=40)
        for item in recent_media:

            # get user details
            recent_user = api.user(user_id=item.user.id)


            # check if duplication and skip
            if first_it == False:
                s = Search(using=es, index=str(EVENT_ID)) \
                    .query("match", item_id=str(item.id))
                response = s.execute()
                # empty sequences (strings, lists, tuples) are false 
                if response:
                    print ('Duplication caught. Not added to db. ID: ' + str(item.id) + '\n')
                    break


            if recent_user.counts['followed_by']<MIN_FOLLOWERS or item.like_count<MIN_LIKES:
                print ("less than user metric threshold for storage, skip.")
                continue

            # pass text into TextBlob (check if empty string)
            if hasattr(item.caption, 'text'):
                text = TextBlob(item.caption.text)
            else:
                text = TextBlob("")
                print ("no text!!")

            # determine if sentiment is positive, negative, or neutral
            if text.sentiment.polarity < 0:
                sentiment = "negative"
            elif text.sentiment.polarity == 0:
                sentiment = "neutral"
            else:
                sentiment = "positive"

            # output key fields
            print (item.user.username + ' ' + str(sentiment) + ' ' + str(text.sentiment.polarity))
            print ('Instagram ID: ' + str(item.id))
            print ('Statuses Posts: ' + str(recent_user.counts['media']) + '    Followers Count: ' + str(recent_user.counts['followed_by']))
            print ('Comment Count: ' + str(item.comment_count) + '    Favorite Count: ' + str(item.like_count))
            print (text)
            print (item.link + '\n')

            # instagram only has comment count
            es.index(index=str(EVENT_ID),
                     doc_type="item",
                     body={
                            "polarity": text.sentiment.polarity,
                            "subjectivity": text.sentiment.subjectivity,
                            "sentiment": sentiment,
                            "item_type": item.type,
                            "item_id": item.id,
                            "user_id": item.user.id,
                            "screen_name": item.user.username,
                            #"location": location,
                            "followers_count": recent_user.counts['followed_by'],
                            #"friends_count": friends_count,
                            "statuses_count": recent_user.counts['media'],
                            "date": item.created_time,
                            "favorite_count": item.like_count,
                            #"share_count": share_count,
                            "message": str(text),
                            "source": "instagram",
                            "item_url": item.link,
                            "comment_count": item.comment_count}) 

        print('sleeping for ' + str(SLEEP) + ' seconds... zzz...')
        time.sleep(SLEEP) # 3*60 seconds = 180 calls per hour (limit is 5,000; including oembed!!)
        print('awake! \n')
        first_it = False


if __name__ == '__main__':
    instagram()


