from flask import render_template
from bs4 import BeautifulSoup as bs

import requests
from requests import session
import json

from . import db

def authenticate_by_cookie(request):
    username = request.cookies.get("username")
    token = request.cookies.get("token")

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    if not user:
        return 1        # Invalid username
    
    if user['token'] == token:
        return json.loads(user['SynergyCookies']), username
    else:
        return 2        # Invalid token

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
        return 3        # Invalid credentials

    # If the credentials seem fine, insert them into the database if the user isn't already in it
    user = db.USERS_DB.userSecure.find_one({
        "username" : request.form.get("username"),
    })

    if not user:
        # Get profile picture
        profile = ret_soup.find(attrs = {
            "alt" : "Student Picture"
        })

        print(profile)

        db.USERS_DB.userSecure.insert({
            "username" : request.form.get("username"),
            "classLinks" : [],
            "settings" : {
                "theme" : "day", 
                "profilePicture" : "https://wa-bsd405-psv.edupoint.com/" + profile.get("src"),
                "backgroundPicture" : None,
                "assignmentColoring" : "regular"
            },
            "SynergyCookies" : json.dumps(dict(s.cookies)),
            "token" : None
        })
    else:
        # Update user cookies
        db.USERS_DB.userSecure.update({
            "username" : request.form.get("username"),
        },{
            "$set" : {
                "SynergyCookies" : json.dumps(dict(s.cookies))
            }
        })

    return dict(s.cookies), request.form.get('username')

def auth_credentials(request):
    # If GET then we're authenticating via cookies
    if request.method == 'GET': 
        return authenticate_by_cookie(request)
    
    return authenticate_by_post(request)

if __name__ == "__main__":
    pass
        


    