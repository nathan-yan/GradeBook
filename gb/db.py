import pymongo
from pymongo import MongoClient as mc

import os
from . import variables

db_credential = variables.DB_CREDENTIAL

CONNECTION_STRING = "mongodb://admin:%s@recordbookcluster0-shard-00-00-l24me.mongodb.net:27017,recordbookcluster0-shard-00-01-l24me.mongodb.net:27017,recordbookcluster0-shard-00-02-l24me.mongodb.net:27017/test?ssl=true&replicaSet=RecordBookCluster0-shard-0&authSource=admin" % db_credential

db = mc(CONNECTION_STRING)

USERS_DB = db.users
CHAT_DB = db.chat
