from flask import Flask, request, redirect, url_for, send_from_directory, json
from elasticsearch import Elasticsearch

es = Elasticsearch()
app = Flask(__name__)

@app.route('/')
def root():
	return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
	# send_static_file default to 'static' for js folder
	return app.send_static_file(path)


@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
    	filename, as_attachment=True)


if __name__ == '__main__':
	app.run(debug=True)




