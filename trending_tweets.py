import json, time, re, datetime
from sngsql.database import Base, db_session, engine
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from sqlalchemy import and_
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from config import *
from helper import *


def calc_growth():
	sql = (
		'''SELECT item_id, creation_date, date_time, elapsed_time, share_count
		FROM retweet_growth
		WHERE item_id IN 
			(SELECT item_id
			FROM retweet_growth
			GROUP BY item_id
			HAVING count(item_id)>1)
		AND current_timestamp - creation_date::timestamp <= INTERVAL '3 hours'
		ORDER BY item_id, date_time, share_count''')

	tweet_data = array_to_dicts(db_session.execute(sql))

	tweets_list = {}
	for row in tweet_data:
		key = row['item_id']
		rest = [row['date_time'],row['elapsed_time'],row['share_count']]
		tweets_list.setdefault(key, []).append(rest)

	print('Total %d hits found.' % len(tweet_data))
	
	for t in tweets_list:

	
	

	return True


if __name__ == '__main__':
    # while 1:
    #     try:
    #         calc_growth()
    #     except:
    #         print ('error. sleeping 5 seconds... zzz...')
    #         time.sleep(5)
    #         continue
    calc_growth()




