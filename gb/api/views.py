from flask import Flask, render_template, request, make_response, redirect, jsonify

from bs4 import BeautifulSoup as bs

import requests
import time
import json

from . import api

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

@api.route("/v1/cookies", methods = ['POST'])
def api_v1_get_cookie():
    try:
        verified = auth.auth_credentials_api(request)
    except exceptions.AuthError:
        return jsonify(
            {
                "status" : "failure",
                "error" : "Invalid API key"
            }
        ), 401
    
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        s, returned_page = auth.synergy_login(username, password)
    except exceptions.AuthError:
        return jsonify(
            {
                "status" : "failure",
                "error" : "Invalid username/password"
            }
        ), 401

    cookies = dict(s.cookies)

    return jsonify({
        "status" : "successful",
        "cookies" : cookies
    })

@api.route("/v1/grades", methods = ['POST'])
def api_v1_get_grades():
    try:
        verified = auth.auth_credentials_api(request)
    except exceptions.AuthError:
        return jsonify(
            {
                "status" : "failure",
                "error" : "Invalid API key"
            }
        ), 401

    cookies = {
        "ASP.NET_SessionID" : request.cookies.get("ASP.NET_SessionId"),
        "BellevuePVUECookie" : request.cookies.get("BellevuePVUECookie")
    }

    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0", cookies = cookies).text
    grade_soup = bs(grade_page)

    # Check for an error, if there is one then the issue is LIKELY that the user's cookie was valid but expired
    # because of the way the error appears I don't think beautifulSoup catches it. So we're going to directly search for the error. 
    if "Object reference" in grade_page:
        return jsonify({
            "status" : "failure",
            "error" : "Invalid cookies"
        }), 401
   
    tables = util.get_info_tables(grade_soup)

    # Filter tables. Resources will be blacklisted
    tables[0] = util.filter_table_by_category(tables[0])

    parsed_tables = util.parse_info_tables(tables)
    grade_table = parsed_tables[0]

    # Parse the grade_table for json 
    grade_json = [{} for _ in grade_table['Period']]

    for category in grade_table:
        for class_ in range(len(grade_table[category])):
            item = bs(grade_table[category][class_])

            link = None
            if item: 
                link = item.find('a')
                
                if link:
                    link = link.get("href")
            
            content = item.text

            item_json = {
                "content" : content,
                "link" : link
            }

            grade_json[class_][util.cleanse_underscore(category)] = item_json 

    return jsonify({
        "status" : "successful",
        "content" : {
            "classes" : grade_json
        }
    })




    