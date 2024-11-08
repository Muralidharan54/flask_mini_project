import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'abcde'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

class PostgresConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:abc123@localhost/climate_db'

class MySQLConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:abc123@localhost/climate_db'