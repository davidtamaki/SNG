from flask import Flask, request, redirect, url_for, send_from_directory
import json, urllib
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
	url = "http://localhost:9200/_search?q=events=" + event_id
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	print (json.dumps(data))
	return json.dumps(data)


@app.route('/api/events/<int:event_id>/item', methods=['GET'])
def get_blurbs(event_id):
	url = "http://localhost:9200/_search?q=events=" + event_id
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	print (json.dumps(data))
	return json.dumps(data)


if __name__ == '__main__':
	app.run(debug=True)







