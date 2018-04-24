from flask import Flask, render_template, request, make_response, redirect, jsonify
from flask_socketio import SocketIO, emit, send

from bs4 import BeautifulSoup as bs

import requests
import time
import json

from . import messaging

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

from bson import BSON 
from bson import json_util

@messaging.route("/", methods = ['GET', 'POST'])
def show_chat():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Oops! Your password or your username was invalid!')
    
    cookies, username = verified 
        
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0", cookies = cookies).text
    grade_soup = bs(grade_page)

    # Check for an error, if there is one then the issue is LIKELY that the user's cookie was valid but expired
    # because of the way the error appears I don't think beautifulSoup catches it. So we're going to directly search for the error. 
    if "Object reference" in grade_page:
        return render_template("index.html", error = 'Your StudentVUE token has expired!')

    tables = util.get_info_tables(grade_soup, links = False)

    parsed_tables = util.parse_info_tables(tables)
    grade_table = parsed_tables[0]

    class_names = grade_table['Course Title']

    for c in class_names:
        classroom = db.CHAT_DB.classrooms.find_one({
            "class" : c
        })

        if not classroom:
            # add the class 
            db.CHAT_DB.classrooms.insert({
                "class" : c,
                "users" : [
                    {
                        "username" : username,
                        "color" : "#4455ff"
                    }
                ]
            })
    
    token = db.USERS_DB.userSecure.find_one({
        "username" : username
    })['token']

    return render_template("chat_template.html", class_names = class_names, token = token, username = username)

@messaging.route("/recap", methods = ['POST'])
def get_recap():
    try:
        verified = auth.auth_credentials(request, method = 'COOKIES')
    except exceptions.AuthError:
        return jsonify(
            {
                "status" : "failure",
                "error" : "Invalid credentials"
            }
        ), 401
    
    _, username = verified 
    
    class_name = request.form.get("class")

    messages = db.CHAT_DB.messages.find({
        "classroom" : class_name
    }).sort([
        ("_id", 1)
        ]).limit(100)

    messages = [json.dumps(message, default = json_util.default) for message in messages]

    print(str(messages))

    return jsonify(
        {
            'status' : "success",
            "messages" : messages
        }
    )

@messaging.route("/colors", methods = ['POST'])
def get_colors():
    try:
        verified = auth.auth_credentials(request, method = 'COOKIES')
    except exceptions.AuthError:
        return jsonify(
            {
                "status" : "failure",
                "error" : "Invalid credentials"
            }
        ), 401
    
    _, username = verified 
    
    class_name = request.form.get("class")

    classroom = db.CHAT_DB.classrooms.find_one({
        "class" : class_name
    })

    colors = {user['username'] : user['color'] for user in classroom['users']}

    print(str(colors))

    return jsonify(
        {
            'status' : "success",
            "colors" : colors
        }
    )


def init_application(application):
    @application.on('connect')
    def handle_connection():
        print("Connected to session ", request.sid)

        emit("connect", {"data" : "connect9ed"})

    @application.on("send")
    def handle_message(message):
        try:
            verified = auth.auth_credentials(message, method = 'SOCKET')
        except exceptions.AuthError as e:
            print(str(e))
            print('invalid credentials')
            return jsonify(
                {
                    "status" : "failure",
                    "error" : "Invalid credentials"
                }
            ), 401

        _, username = verified

        db.CHAT_DB.messages.insert({
            "classroom" : message['class'],
            "content" : {
                "payload" : message['payload'],
                "type" : message['type']
            },
            "timestamp" : int(time.time()),
            "author" : username
        })

        print('worked')

        emit("ack", {"status" : "success"}, room = request.sid)
        emit("message", message)
