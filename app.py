from flask import Flask, request, redirect, url_for, send_from_directory, render_template, Blueprint
from flask.ext.paginate import Pagination
from flask.ext.sqlalchemy import SQLAlchemy
from sngsql.database import db_session
from sngsql.model import Hashtag, Item, User, Word, Url, Retweet_growth
from sqlalchemy import and_, distinct
from sqlalchemy.sql import exists
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

# for tweet embeding
# from flask.ext.twitter_oembedder import TwitterOEmbedder
# twitter_oembedder = TwitterOEmbedder()
# twitter_oembedder.init(app,cache,debug=False)


def get_timeseries_data():
	sql = (
		'''SELECT contestant,
			sum(CASE WHEN date::date = current_date-4 THEN share_count ELSE NULL END) +
				count(CASE WHEN date::date = current_date-4 AND share_count = '0' THEN item_id ELSE NULL END)AS fourdaysago,
			sum(CASE WHEN date::date = current_date-3 THEN share_count ELSE NULL END) +
				count(CASE WHEN date::date = current_date-3 AND share_count = '0' THEN item_id ELSE NULL END)AS threedaysago,
			sum(CASE WHEN date::date = current_date-2 THEN share_count ELSE NULL END) +
				count(CASE WHEN date::date = current_date-2 AND share_count = '0' THEN item_id ELSE NULL END)AS twodaysago,
			sum(CASE WHEN date::date = current_date-1 THEN share_count ELSE NULL END) +
				count(CASE WHEN date::date = current_date-1 AND share_count = '0' THEN item_id ELSE NULL END) AS yesterday,
			sum(CASE WHEN date::date = current_date THEN share_count ELSE NULL END) +
				count(CASE WHEN date::date = current_date AND share_count = '0' THEN item_id ELSE NULL END) AS today
		FROM item
		GROUP BY contestant
		HAVING sum(share_count)>1000
		ORDER BY sum(share_count) DESC''')
	timeseries_data = array_to_dicts(db_session.execute(sql))

	tp_data = {}
	ts_data = {}
	tp_data['json'] = {}
	ts_data['json'] = {}
	ts_data['x'] = 'x'
	for row in timeseries_data:
		if row['contestant'] == 'Donald Trump':
			tp_data['json'][row['contestant']] = [row['fourdaysago'],row['threedaysago'],row['twodaysago'],row['yesterday'],row['today']]
		else:
			ts_data['json'][row['contestant']] = [row['fourdaysago'],row['threedaysago'],row['twodaysago'],row['yesterday'],row['today']]
	ts_data['json']['x'] = [str(date.today()-timedelta(4)),str(date.today()-timedelta(3)),str(date.today()-timedelta(2)),str(date.today()-timedelta(1)),str(date.today())]
	timeseries_data = json.dumps(ts_data)
	trump_data = json.dumps(tp_data)
	print (timeseries_data)
	print (trump_data)
	return ({'timeseries_data': timeseries_data, 'trump_data': trump_data})

def get_barchart_data():
	sql = (
		'''SELECT contestant,
			ROUND(100*SUM(CASE WHEN sentiment ='negative' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_negative,
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
	b_data['json']['neutral'] = []
	b_data['json']['positive'] = []
	bar_categories = []
	for row in bar_data:
		b_data['json']['negative'].append(row['pc_negative'])
		b_data['json']['neutral'].append(row['pc_neutral'])
		b_data['json']['positive'].append(row['pc_positive'])
		bar_categories.append(row['contestant'])
	b_data['groups'] = [['negative','neutral','positive']]
	b_data['order'] = ['negative','neutral','positive']
	b_data['colors'] = {'positive': '#2ca02c','neutral': '#1f77b4','negative': '#ff7f0e'}
	bar_data = json.dumps(b_data)
	print (bar_data)
	return ({'bar_data': bar_data, 'bar_categories': bar_categories})



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
			LIMIT 10;

			CREATE TEMPORARY TABLE neg AS
			SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, item_url, sentiment, source
			FROM item WHERE item_id IN
				(SELECT DISTINCT ON (group_item_id) item_id
				FROM item
				WHERE sentiment = 'negative'
				AND date > (CURRENT_TIMESTAMP - interval '24 hours')
				ORDER BY group_item_id)
			ORDER BY share_count DESC
			LIMIT 10;

			SELECT * FROM pos
			UNION ALL
			SELECT * FROM neg;''')
	tweet_data = array_to_dicts(db_session.execute(sql))
	print (tweet_data)

	# for charts
	timeseries_result = get_timeseries_data()
	timeseries_data = timeseries_result['timeseries_data']
	trump_data = timeseries_result['trump_data']
	bar_result = get_barchart_data()
	bar_data = bar_result['bar_data']
	bar_categories = bar_result['bar_categories']


	return render_template('index.html',tweet_data=tweet_data,
		timeseries_data=timeseries_data,trump_data=trump_data,
		bar_data=bar_data,bar_categories=bar_categories)


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
	results = (db_session.query(Item).filter(and_(
		Item.contestant.like('%'+c.title()+'%'),Item.sentiment=='positive')).
		order_by(Item.share_count.desc()).all())
	response_left = results[10*(p-1):10*p]
	print('Total %d hits found.' % len(results))
	for h in response_left:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)

	pagination = Pagination(page=p, href= URL + 'candidate/' + c + '/item/{0}/',
		total=len(results), search=False, record_name='item')
	return render_template('source.html',css_framework='bootstrap',
		jsondata_left=response_left,pagination=pagination)


if __name__ == '__main__':
	app.run(debug=True)


