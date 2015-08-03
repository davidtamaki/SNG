web: gunicorn app:app
worker: python twitter_sentiment_postgres.py

upgrade: python manage.py db upgrade
init: python db_create.py #TODO!