from flask import Flask, request, redirect, url_for, send_from_directory, render_template
import json, requests
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

es = Elasticsearch()
app = Flask(__name__)

@app.route('/')
def root():
	return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
	# send_static_file default to 'static' for js folder
	return app.send_static_file(path)


@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_events(event_id):
	url = "http://localhost:9200/" + event_id
	response = requests.get(url)
	print (response.json())
	return response.json()


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







