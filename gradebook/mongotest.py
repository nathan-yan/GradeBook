

from pymongo import MongoClient as mc 
from pprint import pprint
import time 
import random
import os 

import Crypto.Hash.SHA256 as sha

s = time.time()
client = mc(os.environ['connection'])

api = client.api
keys = api.keys

def add_user(api_key):
    if (keys.find_one({"API_KEY" : api_key})) != None:
        return False
    else:
        user = {
            "api_key" : api_key
        }
        
        keys.insert_one(user)
        return True


def validate_user(username, api_key):
    found = keys.find_one({"username" : username})

    if (found == None): 
        return False 
    
    else: 
        if (found['api_key'] == api_key):
            return True
    
    return False 

def generateToken(length = 256):
    chars = 'abcdefghijlkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

    base = ''
    for c in range (length):
        base += chars[random.randint(0, len(chars) - 1)]

    return base

newkey = generateToken(10)
digest = sha.new(newkey).hexdigest()
print(newkey)
print(add_user(digest))

