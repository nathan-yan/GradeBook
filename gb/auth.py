from flask import render_template
from bs4 import BeautifulSoup as bs

import requests
from requests import session

import hashlib
import hmac
import json

from . import db
from . import exceptions
from . import variables

def string_equals(s1, s2):
    """
        check if two strings are equal. Do NOT break when characters don't match, as a timing attack can be used to exploit the system
    """

    if (len(s1) != len(s2)):
        return False

    c = len(s1)

    equal = True

    for i in range (c):
        if s1[i] != s2[i]:
            equal = False 
    
    return equal

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

def authenticate_by_socket(data):
    username = data.get("username")
    token = data.get("token")

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    if not user:
        raise exceptions.AuthError("Invalid Username. USERNAME=%s" % username)        # Invalid username
    
    if user['token'] != token:
        raise exceptions.AuthError("Invalid Token. USERNAME=%s, TOKEN=%s" % (username, token))        # Invalid token
    
    # verify the classname
    class_name = data.get("class")
    class_token = data.get("class-token")

    print(class_name, class_token, user['token'])

    if not auth_class_token(class_token, class_name, user['token']):
        raise exceptions.AuthError("User does not belong in class %s" % class_name)

    return json.loads(user['SynergyCookies']), username

def authenticate_by_post(request):
    s = session()
    
    login_page = s.get('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True').text
    
    # Get all form parameters
    soup = bs(login_page)
    inputs = soup.find_all('input')

    # Insert input values then complete the form with username and password 
    payload = { i.get("name") : i.get("value") for i in inputs }
    payload['username'] = request.form.get("username")
    payload['password'] = request.form.get("password")

    # Post the payload to the login url, cookies are now in the session
    returned_page = s.post('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True', data=payload)

    # Check returned_page to see if the credentials were valid.
    # Since we have no direct access to Synergy's backend, we'll have to parse this with BS and check the id = 'ERROR' tag for a "Invalid user id or password" error
    ret_soup = bs(returned_page.text)

    error = ret_soup.find(id = "ERROR")
    if error and error.text == "Invalid user id or password":
        raise exceptions.AuthError("Invalid Credentials. USERNAME=%s" % request.form.get('username'))        # Invalid credentials
    
    insert_user_based_on_credentials(request, ret_soup, s)

    return dict(s.cookies), request.form.get('username')

def authenticate_for_messaging(request):
    username = request.cookies.get("username")
    token = request.cookies.get("token")

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    if not user:
        raise exceptions.AuthError("Invalid Username. USERNAME=%s" % username)        # Invalid username
    
    if user['token'] != token:
        raise exceptions.AuthError("Invalid Token. USERNAME=%s, TOKEN=%s" % (username, token))        # Invalid token
    
    # verify the classname
    class_name = request.form.get("class")
    class_token = request.form.get("class-token")

    if not auth_class_token(class_token, class_name, user['token']):
        raise exceptions.AuthError("User does not belong in class %s" % class_name)

    print("HMAC HAS BEEN VERIFIED")

    return json.loads(user['SynergyCookies']), username

def auth_credentials(request, method = None):
    # If GET then we're authenticating via cookies
    if method == 'COOKIES':                     # authentication by cookies
        return authenticate_by_cookie(request)
    elif method == 'PASSWORD':                  # authentication by login form
        return authenticate_by_post(request)
    elif method == 'SOCKET':                    # authentication by socket data message, checks both the cookie and the class-token 
        return authenticate_by_socket(request)
    elif method == 'MESSAGING':                 # authentication for messaging, checks both the cookie as well as the class-token
        return authenticate_for_messaging(request)

    if request.method == 'GET': 
        return authenticate_by_cookie(request)
    
    return authenticate_by_post(request)

def auth_class_token(token, class_name, salt):
    """
    A way of authenticating that a student indeed belongs to a class without having to store class names serverside.

    Args:
        token (string): a HMAC-MD5 keyed hash of the class name and a salt.
        class_name (string): the class a user "supposedly" belongs in
        salt (string): the necessary salt to recover the HMAC-MD5
    
    Returns:
        boolean: is the token valid
    """

    auth = hmac.new(variables.HMAC_MESSAGING_SECRET.encode(),
                    (class_name + salt).encode())

    recovered_token = auth.hexdigest()

    return string_equals(recovered_token, token)

def generate_class_token(class_name, salt):
    auth = hmac.new(variables.HMAC_MESSAGING_SECRET.encode(),
                    (class_name + salt).encode())

    return auth.hexdigest();

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

if __name__ == "__main__":
    pass
        


    