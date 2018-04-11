from flask import Flask, render_template, request, make_response
from bs4 import BeautifulSoup as bs

import requests

from .. import auth
from .. import util
from .. import db
from .. import variables

from . import home

@home.route("/")
def index():
    return render_template("index.html")

@home.route("/home", methods = ["GET", "POST"])
def show_home():
    verified = auth.auth_credentials(request)

    if type(verified) == int:   # We've encountered an error
        return render_template("index.html", error = 'Invalid Credentials')

    cookies, username = verified
    
    # Get the grades
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0", cookies = cookies).text
    grade_soup = bs(grade_page)

    tables = util.get_info_tables(grade_soup)

    parsed_tables = util.parse_info_tables(tables)
    grade_table = parsed_tables[0]
    periods = grade_table['Period']

    # Reassign all the links so they don't look hella ass
    # Store the links inside the db for future reference
    links = { bs(p).text : bs(p).find('a').get('href') for p in periods }

    # Replace the old urls with more pleasing and easily memorizable links
    # Skip the first row since there are no links
    for row in range(1, len(tables[0])):
        for column in range(len(tables[0][row])):
            tables[0][row][column] = "<a href = %s>%s</a>" % ("/class/" + bs(tables[0][row][0]).text, bs(tables[0][row][column]).text)
    
    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    db.USERS_DB.userSecure.update({
        "username" : username
    }, {
        "$set" : {
            "classLinks" : links
        }
    })

    theme = variables.themes[user['settings']['theme']]
    bg_color, text_color, header_color = theme['bg_color'], theme['text_color'], theme['header_color']

    profile = user['settings']['profilePicture']

    response = make_response(
        render_template("home/dashboard_grade_start.html", profile = profile, grades = tables[0], bg_color = bg_color, header_color = header_color, text_color = text_color)
    )

    return response

        
        

