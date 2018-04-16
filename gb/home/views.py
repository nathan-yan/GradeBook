from flask import Flask, render_template, request, make_response, redirect
from bs4 import BeautifulSoup as bs

import requests
import time
import json

from . import home

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

# A set of users who have seen the update
updated_users = set()

@home.route("/")
def index():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html")
    
    return redirect("/grades")

@home.route("/grades", methods = ["GET", "POST"])
def show_home():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Oops! Your password or your username was invalid!')
    except exceptions.UninitializedUserError:
        # Generate a session token so that we can recognize the user in the /setup page
        username = request.form.get("username")

        token = util.salt(128)

        db.USERS_DB.userSecure.update({
            "username" : username
        }, {
            "$set" : {
                "token" : token
            }
        })

        response = make_response(redirect("/setup"))

        response.set_cookie("token", token, httponly = True)
        response.set_cookie("username", username, httponly = True)

        return response

    cookies, username = verified

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    quarter_number = request.args.get("q")     # TODO: If 4 < q <= 0 then raise an error

    link = 'PXP_Gradebook.aspx?AGU=0'
    if quarter_number:
        quarter_number = int(quarter_number)
        link = user['quarterLinks'][quarter_number - 1]

    # Get the grades
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + link, cookies = cookies).text
    grade_soup = bs(grade_page)

    # Check for an error, if there is one then the issue is LIKELY that the user's cookie was valid but expired
    # because of the way the error appears I don't think beautifulSoup catches it. So we're going to directly search for the error. 
    if "Object reference" in grade_page:
        return render_template("index.html", error = 'Your StudentVUE token has expired!')

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
   
    tables = util.get_info_tables(grade_soup)

    # Filter tables. Resources will be blacklisted
    tables[0] = util.filter_table_by_category(tables[0], blacklist = ['Resources'])

    parsed_tables = util.parse_info_tables(tables)
    grade_table = parsed_tables[0]
    periods = grade_table['Period']

    links = { bs(p).text : bs(p).find('a').get('href') for p in periods }

    # Reassign all the links so they don't look hella ass
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
            "token" : token,
            "classLinks.default" : links
        }
    })

    theme = variables.themes[user['settings']['theme']]
    bg_color, text_color, header_color = theme['bg_color'], theme['text_color'], theme['header_color']

    profile = user['settings']['profilePicture']

    seen_update = "true"
    if username not in updated_users:
        updated_users.add(username)
        seen_update = "false"

    response = make_response(
        render_template("home/dashboard_grade_start.html", profile = profile, quarter_links = quarters, current_quarter = current_quarter, grades = tables[0], bg_color = bg_color, header_color = header_color, text_color = text_color, seen_update = seen_update)
    )

    response.set_cookie("token", token, httponly = True)
    response.set_cookie("username", username, httponly = True)

    return response

@home.route("/class")
@home.route("/class/<period>", methods = ["GET"])
def show_class(period):
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    except exceptions.UninitializedUserError:
        # Generate a session token so that we can recognize the user in the /setup page
        username = request.form.get("username")

        token = util.salt(128)

        db.USERS_DB.userSecure.update({
            "username" : username
        }, {
            "$set" : {
                "token" : token
            }
        })

        response = make_response(redirect("/setup"))

        response.set_cookie("token", token, httponly = True)
        response.set_cookie("username", username, httponly = True)

        return response

    cookies, username = verified

    user = db.USERS_DB.userSecure.find_one({
        "username" : username
    })

    quarter_number = request.args.get("q")
    
    if quarter_number:
        class_link = user['classLinks'][str(int(quarter_number) - 1)][period]
    else:
        class_link = user['classLinks']['default'][period]

    # Get class info
    class_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + class_link, cookies = cookies).text
    class_soup = bs(class_page)

    # Check for an error, if there is one then the issue is LIKELY that the user's cookie was valid but expired
    # because of the way the error appears I don't think beautifulSoup catches it. So we're going to directly search for the error. 
    if "Object reference" in class_page:
        return render_template("index.html", error = 'Your StudentVUE token has expired!')

    tables = util.get_info_tables(class_soup, links = False)[:-1]     # Exclude the last table cuz it's some random stuff
    print(tables)
    if len(tables) == 2:
        two = True
        tables[1] = tables[1][1:-1]
        assignment_table = util.filter_table_by_category(tables[1], whitelist = ["Date", "Assignment", "Assignment Type", "Points", "Notes"])

        summary_table = tables[0]

        parsed_tables = util.parse_info_tables(tables)
        parsed_summary_table = parsed_tables[0]

    else:
        two = False
        tables[0] = tables[0][1:-1]
        assignment_table = util.filter_table_by_category(tables[0], whitelist = ["Date", "Assignment", "Assignment Type", "Points", "Notes"])

        summary_table = []
        
        parsed_summary_table = {
            'Assignment Type' : ['Assignment'],
            'Weight' : ['100%']
        }
    
    parsed_assignment_table = util.parse_table(assignment_table)
    for assignment in range (len(parsed_assignment_table['Points'])):
        if 'Possible' in parsed_assignment_table['Points'][assignment] or len(parsed_assignment_table['Points'][assignment].split('/')) != 2:
            parsed_assignment_table['Points'][assignment] = 'NA/NA'

   # print(tables)

    # There are two scenarios
        
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
        text_color = text_color,
        two = two)
    )

    return response

@home.route("/setup", methods = ['GET'])
def show_setup(): 
    return render_template("setup/setup.html")

@home.route("/setup_", methods = ['GET'])
def do_setup():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    except exceptions.UninitializedUserError:
        pass

    user = db.USERS_DB.userSecure.find_one({
        "username" : request.cookies.get("username")
    })

    cookies, username = json.loads(user['SynergyCookies']), user['username']

    # Get the grades
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0", 
    cookies = cookies).text
    grade_soup = bs(grade_page)

    tables = util.get_info_tables(grade_soup)

    parsed_tables = util.parse_info_tables(tables)
    grade_table = parsed_tables[0]
    periods = grade_table['Period']

    # Get the links
    class_links = {}

    links = { bs(p).text : bs(p).find('a').get('href') for p in periods }
    class_links['default'] = links

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
    
    # Find first non-selected quarter_link
    non_selected_quarter_link = None
    for quarter_link in quarter_links: 
        if quarter_link != 'selected':
            non_selected_quarter_link = quarter_link
            break; 
    
    # This is super ugly but we're going to use the first non-selected quarter_link to load another grade page to get the quarter_link that IS selected 
    grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + non_selected_quarter_link, 
    cookies = cookies).text
    grade_soup = bs(grade_page)

    # Get semester links
    heading_breadcrumb = grade_soup.find("div", attrs = {"class" : "heading_breadcrumb"})
    current_quarter = 1
    q = 0

    for quarter_link in heading_breadcrumb.find_all('li'):
        if (quarter_link.text != '|'):
            q += 1

            link = quarter_link.find('a')

            if link:
                quarter_links[q - 1] = link.get('href')
            
            # If there is no link that's fine, because we can ensure that the link has already been collected in the previous iteration of getting quarter_links
    
    # OHHHH MY GOOODD IT JUST KEEPS GETTING WORSE AND WORSE
    # We'll go through each of the quarter_links to get class_links
    q = 0
    for quarter_link in quarter_links:
        grade_page = requests.get("https://wa-bsd405-psv.edupoint.com/" + quarter_link, 
    cookies = cookies).text
        grade_soup = bs(grade_page)

        tables = util.get_info_tables(grade_soup)

        parsed_tables = util.parse_info_tables(tables)
        grade_table = parsed_tables[0]
        periods = grade_table['Period']

        # Get the links
        links = { bs(p).text : bs(p).find('a').get('href') for p in periods }

        class_links[str(q)] = links
        q += 1
    
    db.USERS_DB.userSecure.update({
        "username" : username
    }, {
        "$set" : {
            "classLinks" : class_links,
            "quarterLinks" : quarter_links,
            "initialized" : True 
        }
    })

    time.sleep(5)
    
    return json.dumps({
        "status" : "success"
    })

@home.route("/profile", methods = ['GET', 'POST'])
def show_profile():
    print("\n\n" + str(request.form) + "\n\n")
    try:
        verified = auth.auth_credentials(request, 'COOKIES')
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    except exceptions.UninitializedUserError:
        # Generate a session token so that we can recognize the user in the /setup page
        username = request.form.get("username")

        token = util.salt(128)

        db.USERS_DB.userSecure.update({
            "username" : username
        }, {
            "$set" : {
                "token" : token
            }
        })

        response = make_response(redirect("/setup"))

        response.set_cookie("token", token, httponly = True)
        response.set_cookie("username", username, httponly = True)

        return response

    cookies, username = verified

    if request.method == 'GET':
        user = db.USERS_DB.userSecure.find_one({
            "username" : username
        })

        theme = variables.themes[user['settings']['theme']]
        bg_color, text_color, header_color = theme['bg_color'], theme['text_color'], theme['header_color']
        
        profile = user['settings']['profilePicture']

        current_settings = user['settings']
        parsed_settings = json.dumps(current_settings)

        return render_template("home/profile_template.html",
                               bg_color = bg_color,
                               text_color = text_color,
                               header_color = header_color,
                               profile = profile,
                               parsed_settings = parsed_settings)
    
    # If this was a POST, the user wants to change something about their account
    change_type = request.form.get("change")
    change_value = request.form.get("value")

    if change_type == "theme":
        if change_value in ['day', 'night']:
            # Set the user's theme
            db.USERS_DB.userSecure.update({
                "username" : username
            }, {
                '$set' : {
                    'settings.theme' : change_value
                }
            })
        
        return "success"

@home.route("/logout", methods = ['GET'])
def logout():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    
    cookies, username = verified 

    # log the user out of the ACTUAL synergy account.
    requests.get("https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?Logout=1", cookies = cookies)

    # set cookies to some random value
    # it's important that it's random, otherwise an attacker could just guess the new cookie

    db.USERS_DB.userSecure.update({
        "username" : username
    }, {
        "$set" : {
            "token" : util.salt(128)
        }
    })

    return redirect("/")

@home.route("/delete", methods = ['POST'])
def delete_account():
    try:
        verified = auth.auth_credentials(request, 'COOKIES')
    except exceptions.AuthError:
        return render_template("index.html", error = 'Invalid Credentials')
    
    cookies, username = verified

    # delete the user's account

    db.USERS_DB.userSecure.delete_one({
        "username" : username
    })

    return render_template("misc/deleted.html")

@home.route("/info/data", methods = ['GET'])
def show_info():
    return render_template("info/data.html")

