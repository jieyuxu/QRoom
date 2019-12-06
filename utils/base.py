from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pgpasslib
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

# password = pgpasslib.getpass('localhost', 5555, 'qroom', 'postgres')
# if not password:
#     raise ValueError('Did not find a password in the .pgpass file')

# url = 'postgresql://postgres:{}@localhost:5555/qroom'.format(password)

# url = 'postgresql://postgresql-rectangular-86196'

# the values of those depend on your setup

# url = 'postgresql+psycopg2://user:password@hostname/mydb'

# THIS URL IS FOR HEROKU POSTGRES. PLEASE COMMENT ONLY, DON'T DELETE
# url = os.environ['DATABASE_URL']

# url = 'postgresql+psycopg2://bob:hi@localhost/mydb'
url = 'postgresql://localhost/mydb'
engine = create_engine(url)
session_factory = sessionmaker(bind=engine)
