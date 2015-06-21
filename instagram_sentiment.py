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
SEARCH_TERM = 'jonsnow'


api = InstagramAPI(client_id=client_id, client_secret=client_secret,client_ips= client_ip,access_token= instagram_access_token)


def instagram():
    while 1:
        #returns 33 objects at a time, cannot get pagination to work (count set to 40)
        recent_media, next_ = api.tag_recent_media(tag_name=SEARCH_TERM, count=40)
        for item in recent_media:

            # get user details
            recent_user = api.user(user_id=item.user.id)


            # check if duplication and skip
            s = Search(using=es, index=str(EVENT_ID)) \
                .query("match", item_id=str(item.id))
            response = s.execute()

            # empty sequences (strings, lists, tuples) are false 
            if response:
                print ('Duplication caught. Not added to db. ID: ' + str(item.id) + '\n')
                break


            # pass text into TextBlob
            text = TextBlob(item.caption.text)

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
            print (item.caption.text)
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
                            "message": item.caption.text,
                            "source": "instagram",
                            "item_url": item.link,
                            "comment_count": item.comment_count}) 

        print('sleeping...')
        time.sleep(10) # 6*60 seconds = 360 calls per hour (limit is 5,000)
        print('awake! \n')


if __name__ == '__main__':
    instagram()


