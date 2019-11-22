release: python inserts.py
web: gunicorn app:app
heroku ps:scale web=1
