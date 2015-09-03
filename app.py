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
			WHERE date > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
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
		HAVING count(hashtag) > 5
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
		size = min((relative_size/smallest_relative_size)*20,60)
		h_data.append({"text": row['hashtag'], "size": round(size)})
	hashtag_data = json.dumps(h_data)
	print (hashtag_data)
	return hashtag_data



# send_static_file default to 'static' for js folder
@app.route('/<path:path>/')
def static_proxy(path):
	return app.send_static_file(path)


##### POSTGRES ######

@app.route('/')
def root():
	sql = ('''DISCARD TEMP;

			CREATE TEMPORARY TABLE pos AS
			SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, item_url, sentiment, source
			FROM item WHERE item_id IN
				(SELECT DISTINCT ON (group_item_id) item_id
				FROM item
				WHERE sentiment = 'positive'
				AND date > (CURRENT_TIMESTAMP - interval '24 hours')
				ORDER BY group_item_id)
			ORDER BY share_count DESC
			LIMIT 3;

			CREATE TEMPORARY TABLE neg AS
			SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, item_url, sentiment, source
			FROM item WHERE item_id IN
				(SELECT DISTINCT ON (group_item_id) item_id
				FROM item
				WHERE sentiment = 'negative'
				AND date > (CURRENT_TIMESTAMP - interval '24 hours')
				ORDER BY group_item_id)
			ORDER BY share_count DESC
			LIMIT 3;

			CREATE TEMPORARY TABLE neu AS
			SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, item_url, sentiment, source
			FROM item WHERE item_id IN
				(SELECT DISTINCT ON (group_item_id) item_id
				FROM item
				WHERE sentiment = 'neutral'
				AND date > (CURRENT_TIMESTAMP - interval '24 hours')
				ORDER BY group_item_id)
			ORDER BY share_count DESC
			LIMIT 3;

			SELECT * FROM pos
			UNION ALL
			SELECT * FROM neg
			UNION ALL
			SELECT * FROM neu;''')
	tweet_data = array_to_dicts(db_session.execute(sql))

	# for charts
	timeseries_result = get_timeseries_data()
	timeseries_data = timeseries_result['timeseries_data']
	bar_result = get_barchart_data()
	bar_data = bar_result['bar_data']
	bar_categories = bar_result['bar_categories']
	hashtag_data = get_hashtag_count_data()


	return render_template('index.html',tweet_data=tweet_data,hashtag_data=hashtag_data,
		timeseries_data=timeseries_data,bar_data=bar_data,bar_categories=bar_categories)


#source type (e.g. twitter or instagram)
@app.route('/source/<s>/item/<int:p>/', methods=['GET'])
def get_source(s,p):
	results = db_session.query(Item).filter(Item.source == s).order_by(Item.share_count.desc()).all()
	response_left = results[10*(p-1):10*p]
	print('Total %d hits found.' % len(results))
	for h in response_left:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)
	pagination = Pagination(page=p, href= URL + 'source/' + s + '/item/{0}/',
		total=len(results), search=False, record_name='item')
	return render_template('source.html',css_framework='bootstrap',
		jsondata_left=response_left,pagination=pagination)


# candidate last name (e.g. Trump or Clinton)
@app.route('/candidate/<c>/item/<int:p>/', methods=['GET'])
def get_candidate(c,p):
	sql = ('''SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, item_url, sentiment, source
			FROM item WHERE contestant ILIKE ('%{0}%')
			ORDER BY share_count DESC'''.format(c))
	print (sql)
	results = array_to_dicts(db_session.execute(sql))
	tweet_data = results[30*(p-1):30*p]
	print (tweet_data)
	print('Total %d hits found.' % len(results))

	pagination = Pagination(page=p, href= URL + 'candidate/' + c + '/item/{0}/',per_page=30,
		total=int(len(results)/3), search=False, record_name='item',format_total=True,format_number=True)
	return render_template('source.html',css_framework='bootstrap',
		tweet_data=tweet_data,pagination=pagination)


# refresh data
@app.route('/api/chart/<c>/', methods=['GET'])
def refresh_chart(c):
	if c=='hashtagcloud':
		return get_hashtag_count_data()
	elif c=='bar':
		bar_result = get_barchart_data()
		bar_data = bar_result['bar_data']
		bar_categories = bar_result['bar_categories']
		concat_dict = {'bar_data':json.loads(bar_data), 'bar_categories':bar_categories }
		concat_json = json.dumps(concat_dict)
		return (concat_json)
	elif c=='time':
		timeseries_result = get_timeseries_data()
		timeseries_data = timeseries_result['timeseries_data']
		concat_dict = {'timeseries_data':json.loads(timeseries_data)}
		concat_json = json.dumps(concat_dict)
		return (concat_json)
	else:
		return ('error url route incorrect')


# saving data into db
@app.route('/api/input_data/', methods=['POST'])
def input():
	req = json.loads(request.data.decode())

	try:
		try:
			u = db_session.query(User).filter_by(uid=str(req['uid'])).one()
		except NoResultFound:
			u = User(uid=req['uid'],
				screen_name=req['screen_name'],
				followers_count=req['followers_count'],
				friends_count=req['friends_count'],
				statuses_count=req['statuses_count'],
				rank=req['rank'])
		db_session.add(u)
		db_session.commit()

		tw = Item(message=req['message'],
				contestant=req['contestant'],
				item_id=req['item_id'],
				group_item_id=req['group_item_id'], # for expanded url
				item_type=req['item_type'],
				item_url=req['item_url'],
				location=req['location'],
				date=req['date'], # all time is stored at UTC
				source=req['source'],
				sentiment=req['sentiment'],
				sentiment_textblob=req['sentiment_textblob'],
				sentiment_bayes=req['sentiment_bayes'],
				polarity=req['polarity'], # tbc
				subjectivity=req['subjectivity'], # tbc
				favorite_count=req['favorite_count'],
				share_count=req['share_count'],
				user_id=u.id,
				verified_user=req['verified_user'],
				team=req['team'],
				data=req['data'])
		db_session.add(tw)
		db_session.commit()

		# words
		for w in req['words']:
			if len(w)>100:
				continue
			w_obj = Word(word=w)
			db_session.add(w_obj)
			db_session.commit()
			tw.words.append(w_obj)
			u.words.append(w_obj)

		# hashtags
		for t in req['hashtags']:
			if len(t)>100:
				continue
			t_obj = Hashtag(hashtag=t)
			db_session.add(t_obj)
			db_session.commit()
			tw.hashtags.append(t_obj)
			u.hashtags.append(t_obj)

		# url
		if req['expanded_url'] and len(req['expanded_url'])<200:
			url = Url(item_id=req['item_id'],
				url=req['expanded_url'])
			db_session.add(url)
			db_session.commit()

	except OperationalError:
		db_session.rollback()

	print (tw.id)
	return str(tw.id)



if __name__ == '__main__':
	app.run(debug=True)


