import json, time, re, datetime
from sngsql.database import Base, db_session, engine
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from sqlalchemy import and_
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from config import *
from helper import *

def string_div(a,b):
	if a=='0' or b=='0.0':
		return 1
	return (float(a)/float(b))

def calc_growth():
	sql = (
		'''SELECT item_id, creation_date, date_time, elapsed_time, share_count
		FROM retweet_growth
		WHERE item_id IN 
			(SELECT item_id
			FROM retweet_growth
			GROUP BY item_id
			HAVING count(item_id)>1)
		AND current_timestamp - creation_date::timestamp <= INTERVAL '5 hours'
		ORDER BY item_id, date_time, share_count''')

	tweet_data = array_to_dicts(db_session.execute(sql))

	# create dict by item_id: [date_time, share_count, elapsed_time, rate] 
	tweet_list = {}
	for row in tweet_data:
		key = row['item_id']
		sc, et = int(row['share_count']),float(row['elapsed_time'])
		# rest = [row['date_time'],sc,et,string_div(sc,et)]
		rest = (sc,et)
		tweet_list.setdefault(key, []).append(rest)

	f = open("tests/retweet_growth.txt", "w")
	for key, value in tweet_list.items():
		f.write(str(key) + ';' + str(value) + '\n')
	f.close()

	print('Total %d hits found.' % len(tweet_list))

	

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




