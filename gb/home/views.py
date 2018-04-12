from flask import Flask, render_template, request, make_response
from bs4 import BeautifulSoup as bs

import requests
import json

from . import home

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

@home.route("/")
def index():
    return render_template("index.html")

@home.route("/grades", methods = ["GET", "POST"])
def show_home():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    except exceptions.UninitializedUserError:
        return redirect("/setup")

    cookies, username = verified

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    quarter_number = request.args.get("q")

    link = 'PXP_Gradebook.aspx?AGU=0'
    if quarter_number:
        link = user['quarterLinks'][quarter_number]

    # Get the grades
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + link, cookies = cookies).text
    grade_soup = bs(grade_page)

    # Get semester links
    heading_breadcrumb = grade_soup.find("div", attrs = {"class" : "heading_breadcrumb"})
    quarter_links = []
    current_quarter = 1
    q = 0

    for quarter_link in heading_breadcrumb.find_all('li'):
        if (quarter_link.text != '|'):
            q += 1

            link = quarter_link.find('a')

            if link:
                quarter_links.append(link.get('href'))
            else:
                quarter_links.append('selected')
                current_quarter = q
    
    quarters = ['grades?q=1', 'grades?q=2', 'grades?q=3', 'grades?q=4']
    quarter_links = { str(i + 1) : quarter_links[i] for i in range (len(quarter_links))}

    tables = util.get_info_tables(grade_soup)

    # Filter tables. Resources will be blacklisted
    tables[0] = util.filter_table_by_category(tables[0], blacklist = ['Resources'])

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

    # Generate a session token
    token = util.salt(128)

    db.USERS_DB.userSecure.update({
        "username" : username
    }, {
        "$set" : {
            "classLinks." + str(current_quarter) : links,
            "quarterLinks" : quarter_links,
            "token" : token
        }
    })

    theme = variables.themes[user['settings']['theme']]
    bg_color, text_color, header_color = theme['bg_color'], theme['text_color'], theme['header_color']

    profile = user['settings']['profilePicture']

    response = make_response(
        render_template("home/dashboard_grade_start.html", profile = profile, quarter_links = quarters, current_quarter = current_quarter, grades = tables[0], bg_color = bg_color, header_color = header_color, text_color = text_color)
    )

    response.set_cookie("token", token, httponly = True)
    response.set_cookie("username", username, httponly = True)

    return response

@home.route("/class")
@home.route("/class/<period>", methods = ["GET"])
def show_class(period):
    verified = auth.auth_credentials(request)

    if type(verified) == int:
        return render_template("index.html", error = 'Invalid Credentials')

    cookies, username = verified

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    quarter_number = request.args.get("q")
    
    class_link = user['classLinks'][quarter_number][period]

    # Get class info
    class_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + class_link, cookies = cookies).text
    class_soup = bs(class_page)

    tables = util.get_info_tables(class_soup, links = False)[:-1]     # Exclude the last table cuz it's some random stuff
    print(tables)
    tables[1] = tables[1][1:-1]
    summary_table = tables[0]
    
    assignment_table = util.filter_table_by_category(tables[1], whitelist = ["Date", "Assignment", "Assignment Type", "Points", "Notes"])

    parsed_assignment_table = util.parse_table(assignment_table)

   # print(tables)

    # There are two scenarios
    # If tables has a length of two, then there is no summary
    
    parsed_tables = util.parse_info_tables(tables)
    parsed_summary_table = parsed_tables[0]
    
    theme = variables.themes[user['settings']['theme']]
    bg_color, text_color, header_color = theme['bg_color'], theme['text_color'], theme['header_color']
    
    profile = user['settings']['profilePicture']

    """
    render_template(summary = info_tables[0], assignments = abbreviated_info_table, assignment_grades = assignment_grades, profile = src, name = name, school = school, bg_color = bg_color, text_color = text_color, header_color = header_color, dates = dates[::-1], js_summary = summary, js_assignments = assignments, three = 'true', class_name = class_name)
    """ 

    class_name = class_soup.find("option", attrs = {'selected' : "selected"}).text

    response = make_response(
        render_template("home/dashboard_class_start.html",
        profile = profile,
        summary = summary_table,
        assignments = assignment_table,
        parsed_summary = json.dumps(parsed_summary_table),
        parsed_assignments = json.dumps(parsed_assignment_table),
        class_name = class_name,
        bg_color = bg_color,
        header_color = header_color,
        text_color = text_color)
    )

    return response

#@home.route("/setup", methods = )
        

