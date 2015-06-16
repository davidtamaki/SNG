from flask import Flask, request, redirect, url_for, send_from_directory
app = Flask(__name__)

@app.route('/')
def root():
	return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
	# send_static_file will guess the correct MIME type
	return app.send_static_file(path)

if __name__ == '__main__':
	app.run(debug=True)