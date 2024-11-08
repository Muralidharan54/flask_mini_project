import os
from datetime import timedelta
from flask_pymongo import PyMongo

class Config:
    SECRET_KEY = 'abcde'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

class PostgresConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:abc123@localhost/climate_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class MongoDBConfig(Config):
    MONGO_URI = 'mongodb://localhost:27017/climate_db'