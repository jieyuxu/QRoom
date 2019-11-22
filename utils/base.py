from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# import pgpasslib

Base = declarative_base()

# password = pgpasslib.getpass('localhost', 5555, 'qroom', 'postgres')
# if not password:
#     raise ValueError('Did not find a password in the .pgpass file')
#
# url = 'postgresql://postgres:{}@localhost:5555/qroom'.format(password)

# url = 'postgresql://postgresql-rectangular-86196'
url = 'postgresql://localhost:5432'
engine = create_engine(url)
session_factory = sessionmaker(bind=engine)
