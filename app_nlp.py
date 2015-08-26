from flask import Flask, request, redirect, url_for, send_from_directory, render_template, Blueprint
from flask.ext.paginate import Pagination
from flask.ext.sqlalchemy import SQLAlchemy
from sngsql.database import db_session
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from sqlalchemy import and_, distinct
from sqlalchemy.sql import exists, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from flask.ext.cache import Cache
import json, requests, datetime
from datetime import date, timedelta
from config import *
from helper import *


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Check Configuring Flask-Cache section for more details
cache = Cache(app,config={'CACHE_TYPE': 'simple'})



def get_timeseries_data():
	sql = (
		'''SELECT contestant,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '60 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '50 minute') THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '60 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '50 minute')
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS fiftyToSixtyMinAgo,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '50 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '40 minute') THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '50 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '40 minute')
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS fortyToFiftyMinAgo,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '40 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '30 minute') THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '40 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '30 minute') 
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS thirtyToFortyMinAgo,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '30 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '20 minute') THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '30 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '20 minute') 
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS twentyToThirtyMinAgo,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '20 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '10 minute') THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '20 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < (CURRENT_TIMESTAMP - INTERVAL '10 minute') 
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS tenToTwentyMinAgo,
			COALESCE(sum(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '10 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < CURRENT_TIMESTAMP THEN share_count ELSE NULL END) +
				count(CASE WHEN date::TIMESTAMP + INTERVAL '1 hour' >= (CURRENT_TIMESTAMP - INTERVAL '10 minute') 
				AND date::TIMESTAMP + INTERVAL '1 hour' < CURRENT_TIMESTAMP
				AND share_count = '0' THEN item_id ELSE NULL END),0) AS lastTenMin
			FROM item
			GROUP BY contestant
			HAVING sum(share_count)>1000
			ORDER BY sum(share_count) DESC''')
	timeseries_data = array_to_dicts(db_session.execute(sql))

	sixty_min = str(datetime.datetime.utcnow()+timedelta(minutes=10))
	fifty_min = str(datetime.datetime.utcnow()+timedelta(minutes=20))
	forty_min = str(datetime.datetime.utcnow()+timedelta(minutes=30))
	thirty_min = str(datetime.datetime.utcnow()+timedelta(minutes=40))
	twenty_min = str(datetime.datetime.utcnow()+timedelta(minutes=50))
	ten_min = str(datetime.datetime.utcnow()+timedelta(minutes=60))

	ts_data = {}
	ts_data['json'] = {}
	ts_data['x'] = 'x'
	for row in timeseries_data:
		ts_data['json'][row['contestant']] = [row['fiftytosixtyminago'],row['fortytofiftyminago'],row['thirtytofortyminago'],row['twentytothirtyminago'],row['tentotwentyminago'],row['lasttenmin']]
	ts_data['json']['x'] = [sixty_min[0:16],fifty_min[0:16],forty_min[0:16],thirty_min[0:16],twenty_min[0:16],ten_min[0:16]]
	timeseries_data = json.dumps(ts_data)
	print (timeseries_data)
	return ({'timeseries_data': timeseries_data})



def get_barchart_data():
	sql = (
		'''SELECT contestant,
			ROUND(-100*SUM(CASE WHEN sentiment ='negative' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_negative,
			ROUND(100*SUM(CASE WHEN sentiment ='neutral' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_neutral,
			ROUND(100*SUM(CASE WHEN sentiment ='positive' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_positive,
			SUM(share_count) AS total_retweet_count
		FROM item
		WHERE date > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
		GROUP BY contestant
		HAVING SUM(share_count) > 100
		ORDER BY pc_positive DESC''')
	bar_data = array_to_dicts(db_session.execute(sql))

	b_data = {}
	b_data['type'] = 'bar'
	b_data['json'] = {}
	b_data['json']['negative'] = []
	b_data['json']['positive'] = []
	bar_categories = []
	for row in bar_data:
		b_data['json']['negative'].append(row['pc_negative'])
		b_data['json']['positive'].append(row['pc_positive'])
		bar_categories.append(row['contestant'])
	b_data['groups'] = [['negative','positive']]
	b_data['order'] = None
	b_data['colors'] = {'positive': '#2ca02c','negative': '#ff7f0e'}
	bar_data = json.dumps(b_data)
	print (bar_data)
	return ({'bar_data': bar_data, 'bar_categories': bar_categories})

def get_hashtag_count_data():
	sql = (
		'''SELECT hashtag,
			COUNT(share_count) AS tweet_count
		FROM item_hashtag
		JOIN item ON item_hashtag.item_id=item.id
		JOIN hashtag ON item_hashtag.hashtag_id=hashtag.id
		GROUP BY hashtag
		HAVING count(hashtag) > 10
		ORDER BY tweet_count DESC
		LIMIT 100''')
	hashtag_data = array_to_dicts(db_session.execute(sql))
	h_counts = []
	h_data = []
	for row in hashtag_data:
		h_counts.append(float(row['tweet_count']))
	total = sum(h_counts)
	smallest_relative_size = min(h_counts)/total
	for row in hashtag_data:
		relative_size = ((float(row['tweet_count'])/total))
		size = min((relative_size/smallest_relative_size)*20,70)
		h_data.append({"text": row['hashtag'], "size": round(size)})
	hashtag_data = json.dumps(h_data)
	print (hashtag_data)
	return hashtag_data



if __name__ == '__main__':
	app.run(debug=True)


