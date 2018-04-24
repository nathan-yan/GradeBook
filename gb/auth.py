from flask import render_template
from bs4 import BeautifulSoup as bs

import requests
from requests import session
import json
import hashlib

from . import db
from . import exceptions
from . import util

def authenticate_by_cookie(request):
    username = request.cookies.get("username")
    token = request.cookies.get("token")

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    if not user:
        raise exceptions.AuthError("Invalid Username. USERNAME=%s" % username)        # Invalid username
    
    if user['token'] == token:
        return json.loads(user['SynergyCookies']), username
    else:
        raise exceptions.AuthError("Invalid Token. USERNAME=%s, TOKEN=%s" % (username, token))        # Invalid token

def authenticate_by_post(request):
    s = session()
    
    username = request.form.get("username")
    password = request.form.get("password")

    s, returned_page = synergy_login(username, password)

    # Check returned_page to see if the credentials were valid.
    # Since we have no direct access to Synergy's backend, we'll have to parse this with BS and check the id = 'ERROR' tag for a "Invalid user id or password" error
    ret_soup = bs(returned_page.text)

    error = ret_soup.find(id = "ERROR")
    if error and error.text == "Invalid user id or password":
        raise exceptions.AuthError("Invalid Credentials. USERNAME=%s" % request.form.get('username'))        # Invalid credentials
    
    insert_user_based_on_credentials(request, ret_soup, s)

    return dict(s.cookies), request.form.get('username')

def auth_credentials(request, method = None):
    if method == 'COOKIES':
        return authenticate_by_cookie(request)
    elif method == 'PASSWORD':
        return authenticate_by_post(request)

    if request.method == 'GET': 
        return authenticate_by_cookie(request)
    return authenticate_by_post(request)

def auth_credentials_api(request):
    # The key is a 36 character alphanumeric.
    # There are 62 possibilities per character
    # The first 15 characters will represent a SHA-256 hash of the username truncated to 89 bits
    # The other 21 characters will be the actual access key. This ensures that the key itself is 128 bits and that a username is extractable from the key.  
    
    key = request.form.get("api_key")

    if not key:
        raise exceptions.AuthError("Invalid Credentials, no key")

    # Parse the key
    user_hash = key[:10]
    access_key = key

    user = db.API_KEY_DB.userKeys.find_one({
        "userHash" : user_hash
    })

    if not user:
        raise exceptions.AuthError("No user exists")

    if access_key not in user['apiKeys']:
        raise exceptions.AuthError("API key is invalid")

    return True

def synergy_login(username, password):
    s = session()

    login_page = s.get('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True').text
    
    # Get all form parameters
    soup = bs(login_page)
    inputs = soup.find_all('input')

    # Insert input values then complete the form with username and password 
    payload = { i.get("name") : i.get("value") for i in inputs }
    payload['username'] = username
    payload['password'] = password 

    # Post the payload to the login url, cookies are now in the session
    returned_page = s.post('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True', data=payload)

    ret_soup = bs(returned_page.text)

    error = ret_soup.find(id = "ERROR")
    if error and error.text == "Invalid user id or password":
        raise exceptions.AuthError("Invalid Credentials. USERNAME=%s" % request.form.get('username'))        # Invalid credentials

    return s, returned_page

def insert_user_based_on_credentials(request, ret_soup, s):
    # If the credentials seem fine, insert them into the database if the user isn't already in it
    user = db.USERS_DB.userSecure.find_one({
        "username" : request.form.get("username"),
    })

    if not user:
        # Get profile picture
        profile = ret_soup.find(attrs = {
            "alt" : "Student Picture"
        })

        db.USERS_DB.userSecure.insert({
            "username" : request.form.get("username"),
            "initialized" : False,
            "classLinks" : {
                "1" : [],
                "2" : [],
                "3" : [],
                "4" : [],
                "default" : []
            },
            "quarterLinks" : [],
            "settings" : {
                "theme" : "day", 
                "profilePicture" : "https://wa-bsd405-psv.edupoint.com/" + profile.get("src"),
                "backgroundPicture" : None,
                "assignmentColoring" : "regular"
            },
            "SynergyCookies" : json.dumps(dict(s.cookies)),
            "token" : None
        })

        # If the user doesn't exist, we need to populate all the empty links now 
        # this speeds stuff up in the future.
        # if Synergy changes the link code every session then we're screwed but i think we're ok

        # EDIT: Synergy uses the same link!

        # We'll implement link population by redirecting the user to a new /setup link
        # Since it's on the same domain it'll have access to the token we've generated

        raise exceptions.UninitializedUserError("")    # We need to fill user information

    else:
        # Update user synergy cookies
        db.USERS_DB.userSecure.update({
            "username" : request.form.get("username"),
        },{
            "$set" : {
                "SynergyCookies" : json.dumps(dict(s.cookies))
            }
        })

        if not user['initialized']:
            raise exceptions.UninitializedUserError("")

def derive_api_key(username, length = 36, hash_split = 15):
    """Derives a random api key given a username, desired api key length and length of the username hash that is included in the key 
    
    Args:
        username (string): the username of the person generating the api key 
        length (int): the length of the desired api key
        hash_split (int): the length of the truncated hash that is prepended onto the key to bring it to a length of `length`
    
    Returns:
        string: the api key
    """

    key = util.salt(length - hash_split)

    sha1 = hashlib.sha1()
    hash_ = int(sha1.update(username).hexdigest(), 16)

    # Convert the hash_ into a 62 base number. This is the number of possible characters util.salt can generate.

    hash_ = util.int_to_base(hash_, 62)

    alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    username = ''

    for i in range (hash_split):
        username += alpha[hash_[i]]
    
    return username + key

if __name__ == "__main__":
    pass
        


    