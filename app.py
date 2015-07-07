from flask import Flask, request, redirect, url_for, send_from_directory, render_template, Blueprint
from flask.ext.paginate import Pagination
from flask.ext.sqlalchemy import SQLAlchemy
from sngsql.database import db_session
from sngsql.model import Hashtag, Item, User, Word, Url
from sqlalchemy import and_
from sqlalchemy.sql import exists
from flask.ext.cache import Cache
from flask.ext.twitter_oembedder import TwitterOEmbedder
import json, requests
from config import *

# # from elasticsearch import Elasticsearch
# # from elasticsearch_dsl import Search, Q

# client = Elasticsearch()

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Check Configuring Flask-Cache section for more details
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

# for tweet embeding
twitter_oembedder = TwitterOEmbedder(app,cache)

# send_static_file default to 'static' for js folder
@app.route('/<path:path>/')
def static_proxy(path):
	return app.send_static_file(path)



##### POSTGRES ######

@app.route('/')
def root():
	l = db_session.query(Item).filter(Item.sentiment == 'positive').order_by(Item.share_count).all()
	response_left = l[0:10]
	print('Total %d hits found.' % len(l))
	for h in response_left:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)

	r = db_session.query(Item).filter(Item.sentiment == 'negative').order_by(Item.share_count).all()
	response_right = r[0:10]
	print('Total %d hits found.' % len(r))
	for h in response_right:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)

	return render_template('index.html',jsondata_left=response_left,jsondata_right=response_right)


#source type (e.g. twitter or instagram)
@app.route('/source/<s>/item/<int:p>/', methods=['GET'])
def get_source(s,p):
	results = db_session.query(Item).filter(Item.source == s).order_by(Item.share_count).all()
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
		order_by(Item.share_count).all())
	response_left = results[10*(p-1):10*p]
	print('Total %d hits found.' % len(results))
	for h in response_left:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)

	pagination = Pagination(page=p, href= URL + 'candidate/' + c + '/item/{0}/',
		total=len(results), search=False, record_name='item')
	return render_template('source.html',css_framework='bootstrap',
		jsondata_left=response_left,pagination=pagination)



@app.route('/test/')
def test():
	return render_template('d3_test.html')
	

if __name__ == '__main__':
	app.run(debug=True)



# postgres - ids
# @app.route('/test/')
# def test():
# 	results = db_session.query(Item.item_url).all()
# 	response_left =[]
# 	for r in results:
# 		url = str(r)
# 		response_left.append("https://api.twitter.com/1/statuses/oembed.json?url=" + url[2:-3])
# 	response_left = response_left[0:10]
# 	print (response_left)
# 	return render_template('source.html',jsondata_left=response_left,total=len(results))



##### ELASTICSEARCH ######

# @app.route('/')
# def root():
# 	l = (Search(using=client, index='1').
# 			#query("match", source="twitter").
# 			query("range", ** {"polarity": {"gte": 0.3}}).
# 			#sort('-favorite_count'))
# 			sort('-share_count'))
# 	l = l[0:10] # {"from": 0, "size": 10}
# 	response_left = l.execute()

# 	print(l.to_dict())
# 	print('Total %d hits found.' % response_left.hits.total)
# 	for h in response_left:
# 		h.polarity = round(h.polarity,2)
# 		h.subjectivity = round(h.subjectivity,2)
# 		# if h.source == "twitter":
# 		# 	h.item_url = "https://api.twitter.com/1/statuses/oembed.json?url=" + h.item_url
# 		# for instragram --> h.item_url = "http://api.instagram.com/oembed?url=" + h.item_url + "&maxwidth=320"
# 		# print(h.date, h.source, h.item_type, h.screen_name, h.item_url)

# 	r = (Search(using=client, index='1').
# 			#query("match", source="twitter").
# 			query("range", ** {"polarity": {"lte": -0.3}}).
# 			#sort('-favorite_count'))
# 			sort('-share_count'))
# 	r = r[0:10]
# 	response_right = r.execute()

# 	print(r.to_dict())
# 	print('Total %d hits found.' % response_right.hits.total)
# 	for h in response_right:
# 		h.polarity = round(h.polarity,2)
# 		h.subjectivity = round(h.subjectivity,2)
# 		# if h.source == "twitter":
# 		# 	h.item_url = "https://api.twitter.com/1/statuses/oembed.json?url=" + h.item_url
# 		# print(h.date, h.source, h.item_type, h.screen_name, h.item_url)

# 	return render_template('index.html',jsondata_left=response_left,jsondata_right=response_right)


# # e.g. http://localhost:5000/source/instagram/item/1
# @app.route('/source/<s>/item/<int:page>/', methods=['GET'])
# def get_items(s,page):
# 	l = (Search(using=client, index='1').
# 		query("match", source=s).
# 		#query("range", ** {"polarity": {"gte": 0.1}}).
# 		sort('-favorite_count'))
# 	l = l[10*(page-1):10*page]
# 	response_left = l.execute()

# 	print(l.to_dict())
# 	print('Total %d hits found.' % response_left.hits.total)
# 	for h in response_left:
# 		h.polarity = round(h.polarity,2)
# 		h.subjectivity = round(h.subjectivity,2)
# 		# if h.source == "twitter":
# 		# 	h.item_url = "https://api.twitter.com/1/statuses/oembed.json?url=" + h.item_url
# 	return render_template('source.html',jsondata_left=response_left,total=response_left.hits.total)



# BELOW NOT IN USE

# @app.route('/api/events/', methods=['GET'])
# def get_events():
# 	url = "http://localhost:9200/_all/_mapping"
# 	response = requests.get(url)
# 	data = response.json()
# 	# data = data["hits"]["hits"] NEED TO UPDATE
# 	return data



# @app.route('/api/events/<int:event_id>/user/<int:user_id>/', methods=['GET'])
# def get_user_items(event_id,user_id):
# 	url = "http://localhost:9200/" + str(event_id) + "/_search?q=user_id:" + str(user_id)
# 	response = requests.get(url)
# 	data = response.json()
# 	data = data["hits"]["hits"]
# 	return render_template('request.html',jsondata=data)



# @app.route('/api/events/<int:event_id>/item/<item_id>/', methods=['GET'])
# def get_event_itemid(event_id,item_id):
# 	url = "http://localhost:9200/" + str(event_id) + "/_search?q=item_id:" + str(item_id)
# 	response = requests.get(url)
# 	data = response.json()
# 	data = data["hits"]["hits"]
# 	return render_template('request.html',jsondata=data)	



