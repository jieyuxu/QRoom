from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pgpasslib
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

# password = pgpasslib.getpass('localhost', 5432, 'qroom', 'postgres')
# if not password:
#     raise ValueError('Did not find a password in the .pgpass file')

# url = 'postgresql://postgres:{}@localhost:5555/qroom'.format(password)

# url = 'postgresql://postgresql-rectangular-86196'

# the values of those depend on your setup

# export POSTGRES_URL="127.0.0.1:5432"
# export POSTGRES_USER="postgres"
# export POSTGRES_PW="dbpw"
# export POSTGRES_DB="mydb"

# POSTGRES_URL = get_env_variable("POSTGRES_URL")
# POSTGRES_USER = get_env_variable("POSTGRES_USER")
# POSTGRES_PW = get_env_variable("POSTGRES_PW")
# POSTGRES_DB = get_env_variable("POSTGRES_DB")

# url = 'postgresql+psycopg2://user:password@hostname/mydb'


url = 'postgresql+psycopg2://localhost/mydb'
engine = create_engine(url)
session_factory = sessionmaker(bind=engine)
