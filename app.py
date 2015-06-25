from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from flask.ext.cache import Cache
from flask.ext.twitter_oembedder import TwitterOEmbedder
import json, requests
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

client = Elasticsearch()

app = Flask(__name__)
# Check Configuring Flask-Cache section for more details
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

twitter_oembedder = TwitterOEmbedder(app,cache)


# send_static_file default to 'static' for js folder
@app.route('/<path:path>')
def static_proxy(path):
	return app.send_static_file(path)


@app.route('/')
def root():
	# url = "http://localhost:9200/1/_search?"
	# s = Search(using=client, index='1').sort('-date')

	l = (Search(using=client, index='1').
			# query("match", source="twitter").
			query("range", ** {"polarity": {"gte": 0.2}}).
			sort('-favorite_count'))
	l = l[0:10] # {"from": 0, "size": 10}
	response_left = l.execute()

	print(l.to_dict())
	print('Total %d hits found.' % response_left.hits.total)
	for h in response_left:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)
		if h.source == "twitter":
			h.item_url = "https://api.twitter.com/1/statuses/oembed.json?url=" + h.item_url
		else:
			h.item_url = "http://api.instagram.com/oembed?url=" + h.item_url + "&maxwidth=320"
		# print(h.date, h.source, h.item_type, h.screen_name, h.item_url)


	r = (Search(using=client, index='1').
			# query("match", source="twitter").
			query("range", ** {"polarity": {"lte": -0.2}}).
			sort('-favorite_count'))
	r = r[0:10]
	response_right = r.execute()

	print(r.to_dict())
	print('Total %d hits found.' % response_right.hits.total)
	for h in response_right:
		h.polarity = round(h.polarity,2)
		h.subjectivity = round(h.subjectivity,2)
		if h.source == "twitter":
			h.item_url = "https://api.twitter.com/1/statuses/oembed.json?url=" + h.item_url
		else:
			h.item_url = "http://api.instagram.com/oembed?url=" + h.item_url + "&maxwidth=320"
		# print(h.date, h.source, h.item_type, h.screen_name, h.item_url)


	return render_template('index.html',jsondata_left=response_left,jsondata_right=response_right)


@app.route('/api/events', methods=['GET'])
def get_events():
	url = "http://localhost:9200/_all/_mapping"
	response = requests.get(url)
	data = response.json()
	# data = data["hits"]["hits"] NEED TO UPDATE
	return data


# @app.route('/api/events/<int:event_id>', methods=['GET'])
# def get_events(event_id):
# 	url = "http://localhost:9200/" + str(event_id) + "/_search?"
# 	response = requests.get(url)
# 	data = response.json()
# 	# data = data["hits"]["hits"] NEED TO UPDATE
# 	return render_template('request.html',jsondata=data)


@app.route('/api/events/<int:event_id>/user/<int:user_id>', methods=['GET'])
def get_user_items(event_id,user_id):
	url = "http://localhost:9200/" + str(event_id) + "/_search?q=user_id:" + str(user_id)
	response = requests.get(url)
	data = response.json()
	data = data["hits"]["hits"]
	return render_template('request.html',jsondata=data)


@app.route('/api/events/<int:event_id>/item/<item_id>', methods=['GET'])
def get_event_itemid(event_id,item_id):
	url = "http://localhost:9200/" + str(event_id) + "/_search?q=item_id:" + str(item_id)
	response = requests.get(url)
	data = response.json()
	data = data["hits"]["hits"]
	return render_template('request.html',jsondata=data)	


if __name__ == '__main__':
	app.run(debug=True)







