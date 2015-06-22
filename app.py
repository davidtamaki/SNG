from flask import Flask, request, redirect, url_for, send_from_directory, render_template
import json, requests
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

client = Elasticsearch()

app = Flask(__name__)


# send_static_file default to 'static' for js folder
@app.route('/<path:path>')
def static_proxy(path):
	return app.send_static_file(path)


@app.route('/')
def root():
	# url = "http://localhost:9200/1/_search?"

	#s = Search(using=client, index='1').query("match", source="instagram").sort('-_timestamp')
	#s = Search(using=client, index='1').sort('-_timestamp')
	s = Search(using=client, index='1').sort('-date')
	s = s[0:100] # {"from": 0, "size": 100}
	response = s.execute()

	# print query params and responses
	print(s.to_dict())
	print('Total %d hits found.' % response.hits.total)
	for h in response:
		print(h.date, h.source, h.item_type, h.screen_name, h.item_url)

	return render_template('index.html',jsondata=response)



@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_events(event_id):
	url = "http://localhost:9200/" + str(event_id) + "/_search?"
	response = requests.get(url)
	data = response.json()
	# data = data["hits"]["hits"] NEED TO UPDATE
	return render_template('request.html',jsondata=data)


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







