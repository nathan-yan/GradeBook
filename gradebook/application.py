from login import login_pipeline

from bs4 import BeautifulSoup as bs

from flask import Flask
from flask import request, redirect, render_template, make_response, jsonify, Response

import random

from Crypto.Hash import SHA256 as sha 

import json

from user import User

import requests as r
from requests import Session as session

from pymongo import MongoClient as mc 
import os 

client = mc(os.environ['connection'])

api = client.api
keys = api.keys

def add_user(api_key):
    if (keys.find_one({"api_key" : api_key})) != None:
        return False
    else:
        user = {
            "api_key" : api_key
        }
        
        keys.insert_one(user)
        return True

def validate_user(api_key):
    api_key = sha.new(api_key.encode()).hexdigest()

    found = keys.find_one({"api_key" : api_key})

    if (found == None): 
        return False 
    
    else: 
        if (found['api_key'] == api_key):
            return True
    
    return False 

application = Flask(__name__)

users = {}
user_logins = {}

# API SECTION
GRADEBOOK_PREFIX = "https://wa-bsd405-psv.edupoint.com"

def getValue(field):
    s = field.split('=')
    if len(s) <= 1:
        return ''
    else:
        return '='.join(s[1:]).replace('"', '')

def getInputParams(split):
    params = []

    for s in split[1:-1]:
        content = s.split(' ')
        type_ = getValue(content[1])
        name = getValue(content[2])
        id_ = getValue(content[3])
        value = getValue(content[4])

        params.append([type_, name, id_, value])
    
    return params

def completeForm(givens, needed):
    form = {}

    for g in givens:
        name = g[2]
        value = g[3]

        form[name] = value
    
    for n in needed:
        form[n[0]] = n[1]

    return form

def loginPipeline(username, password):
    s = session()

    login_page = s.get('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True').text
    
    # get all form parameters
    split = login_page.split("<input")
    p = getInputParams(split)

    # complete the form with username and password 
    payload = (completeForm(p, [['username' , username], ['password', password]]))

    # post the payload to the login url
    returned = s.post('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True', data=payload)
    
    return s

def findSession(username):
    for s in most_recent:
        if s[0] == username:
            return s[1]
    
    return False

def generateToken(length = 256):
    chars = 'abcdefghijlkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-'

    base = ''
    for c in range (length):
        base += chars[random.randint(0, len(chars) - 1)]

    return base

def dictionarify(a):
    # a is a two dimensional array, arranged in rows x columns
    print(a)
    categories = a[0]
    categories_ = {_ : [] for _ in categories}

    for r in a[1:]:
        for c in range(len(r)):
            categories_[a[0][c]].append(r[c])

    return categories_

def infoTables(soup):
    return soup.find_all("table", attrs = {"class" : 
                                           "info_tbl"})

def splitTable(table, links = False):
    elements = []
    element_links = {}

    rows = table.find_all("tr")
    for r in rows:
        elements.append([])
        
        columns = r.find_all("td")
        for c in columns:
            # god damn it
            try:
                content = c.get_text().encode()
            except UnicodeEncodeError:
                content = ''
            
            elements[-1].append(content)

            if (links):
                print(c)
                l = c.find('a')
                if l != None:
                    l = l.get("href")
                    element_links[content] = l

    return elements, element_links 

def stripChars(str, character_list):
    build = ''
    for l in str:
        if l not in character_list:
            build += l
    
    return build 

@application.route("/api/v1/cookie", methods = ["POST"])
def fetchCookie():
    """
        POST Payload:
        {
            "username" : "s-yann",
            "password" : "example",
            "api_key" : "aEfj3Olp" 
        }
    """
    try:
        json_content = request.get_json()
        if (json_content == None):
                json_content = json.loads(request.data)

        if (not validate_user(json_content['API_KEY'])):
            return Response(json.dumps({
                "error" : "INVALID_CREDENTIALS"
            }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

        session = loginPipeline(json_content['username'], json_content['password'])
        html = session.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0").text

        if "Unknown error while accessing the web site. Please check back later as we address the problem" in html:
            return Response(json.dumps({
                    "error" : "INVALID_CREDENTIALS"
                }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

        cookies = session.cookies.get_dict()
        return Response(json.dumps(cookies), headers = {"Access-Control-Allow-Origin": '*'})
    except Exception as e:
        return (str(e))
        

@application.route("/api/v1/grade", methods = ["POST", "GET"])
def _gradebook():
    """
        POST Payload:
        {
            "cookies" : {
                "BellevuePVUECookie" : "",
                "ASP.NET_SessionId"  : ""
            },

            "api_key" : "aEfj3Olp" 
        }
    """

    try:
        json_content = request.get_json()
        if (json_content == None):
            json_content = json.loads(request.data)

        if (not validate_user(json_content['API_KEY'])):
            return Response(json.dumps({
                "error" : "INVALID_CREDENTIALS"
            }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

        cookies = json_content['cookies']

        url = GRADEBOOK_PREFIX + "/PXP_gradebook.aspx?AGU=0"
        print(cookies)
        content = r.get(url, cookies = cookies).text
        print(content)
        soupfied = bs(content)

        info_tables = infoTables(soupfied)[0]

        grades, links = splitTable(info_tables, links = True)
        d = dictionarify(grades)
        d['links'] = links

        return Response(json.dumps(d), headers = {"Access-Control-Allow-Origin": '*'})
    except:
        return Response(json.dumps({
                "error" : "EXPIRED_TOKEN"
            }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

@application.route("/api/v1/class", methods = ["POST"])
def _gradeclass():
    """
        POST payload:
        {
            "username" : "s-yann",
            "password" : "example",
            "link" : "some long ass link dayum",
            "api_key" : "aEfj3Olp"
        }
    """
    try:
        json_content = request.get_json()
        
        if (json_content == None):
            json_content = json.loads(request.data)

        if (not validate_user(json_content['API_KEY'])):
            return Response(json.dumps({
                "error" : "INVALID_CREDENTIALS"
            }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

        cookies = json_content['cookies']

        url = GRADEBOOK_PREFIX + "/" + json_content['link']
        content = r.get(url, cookies = cookies).text
        soupified = bs(content)

        info_tables = infoTables(soupified)

        summary = {}
        assignments = {}

        categories = False
        metadata = None
        
        # non-assignment category class
        if (len(info_tables) == 2):
            
            assignments_, _ = splitTable(info_tables[0])    
            
            # strip the first row off since it's not useful
            metadata = assignments_[0][0]
            assignments_ = assignments_[1:]

            assignments = dictionarify(assignments_)

        # assignment category class
        elif (len(info_tables) == 3):
            categories = True 

            summary_, _ = splitTable(info_tables[0])
            assignments_, _ = splitTable(info_tables[1])

            # strip the first row off since it's not useful
            metadata = assignments_[0][0]
            assignments_ = assignments_[1:]
        
            summary = dictionarify(summary_)
            assignments = dictionarify(assignments_)

        metadata = metadata.split(' / ')
        classname = ''.join(metadata[0].split(' ')[3:])     # hellaaaaaa janky but it works
        period = metadata[1].split(': ')[1]
        teacher = metadata[2]
        grade = stripChars(metadata[3].split(" ")[1], ['(', ')', '%'])

        return_json = {
            "summary" : summary, 
            "assignments" : assignments,
            "categories" : categories,
            "metadata" : {
                "classname" : classname,
                "period" : period,
                "teacher" : teacher, 
                "grade" : grade
            }
        }

        return Response(json.dumps(return_json), headers = {"Access-Control-Allow-Origin": '*'})

    except:
        return Response(json.dumps({
                "error" : "EXPIRED_TOKEN"
            }), status = 403, mimetype = 'application/json', headers = {"Access-Control-Allow-Origin": '*'})

# API SECTION END

#title, author, desc, closed
list_of_issues = [
    ["https://grades.newportml.com/issues?issue=1", 'Add a grade calculator', 'anonymous', 'I think we need a grade calculator. It would be really nice to see how your grade would change if specific assignments were scored differently', False]
]

# title, author, desc
issue_comments = [
    [],
    [["Does commenting work on GradeBook issues?", "Nathan Yan", "heck yeah it does"]]
]

def generate_token(length = 256):
    chars = 'abcdefghijlkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-'

    base = ''
    for c in range (length):
        base += chars[random.randint(0, len(chars) - 1)]

    return base

@application.route("/")
def gradebook():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    return render_template(path + "index.html")

@application.route("/api")
def showapi():
    return render_template("api.html")

@application.route("/api/docs")
def showdocs():
    return render_template("docs.html")


@application.route("/issues", methods = ["GET", "POST"])
def issues():
    try:
        issue_id = int(request.args.get('issue'))
    except:
        issue_id = ''

    if (issue_id == ''):

        try:
        	username, password = request.form['username'], request.form['password']
        except:
            username = "anonymous"
            password = "*********"

        return render_template("issues.html", issues = list_of_issues, username = username, password = password)

    else:
        return render_template("issue.html", issue = list_of_issues[int(issue_id) - 1], comments = issue_comments[int(issue_id) - 1])

@application.route("/record", methods = ["GET", "POST"])
def record():
    return render_template("record.html")

@application.route("/record_", methods = ["GET", "POST"])
def record_():
    try:
        password = sha.new(request.form['password'].encode()).hexdigest()
    except:
        return render_template("forbidden.html")

    if (password == "99c9e860a1f6099ae962ed2269aac0210409b403b4f5e25d9c8d813c45544d52"):
        return jsonify(user_logins)
    else:
        return redirect("https://grades.newportml.com/record?password=invalid")

@application.route("/submit_issue", methods = ['POST'])
def submit_issue():
    author, email, title, description = request.form['author'], request.form['email'], request.form['title'], request.form['description']

    if title == '':
        title = 'no title'

    if author == '':
        author = 'anonymous'

    if description == '':
        return redirect("https://grades.newportml.com/issues?error=description")

    if email != '':
        list_of_issues.append(["https://grades.newportml.com/issues?issue=" + str(len(list_of_issues) + 1), title, author+ ", " + email, description, False])
    else:
        list_of_issues.append(["https://grades.newportml.com/issues?issue=" + str(len(list_of_issues) + 1), title, author, description, False])

    return render_template("issues.html", issues = list_of_issues, username = 'dank', password = 'meme')

@application.route("/community", methods = ["GET", "POST"])
def community():
    try:
    	username, password = request.form['username'], request.form['password']
    except:
        username = "anonymous"
        password = "*********"

    return render_template("community.html", username = username, password = password)

@application.route('/home', methods = ['POST', "GET"])
def home():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    session = False
    received_cookie = False
    token = ''

    try:
        username, password = request.form['username'], request.form['password']

        session = auth(username, password)
    except:
        # no uname/password because we're getting from the website, so check cookies
        username = request.cookies.get('username')
        token = request.cookies.get('token')

        print(username, token,  "token")

        if username not in users:
            return redirect("https://grades.newportml.com/?login=ummmm")
        else:
            # check token 
            if users[username].active_tokens[0] != token:
                return redirect("https://grades.newportml.com/?login=expired")
            else:
                session = users[username].session

                # if validated, set cookie flag to True
                received_cookie = True

    try:
        if (session != False):
            hexdigest = sha.new(username.encode()).hexdigest()
            if (user_logins.get(hexdigest) != None):
                user_logins[hexdigest] += 1
            else:
                user_logins[hexdigest] = 1

            # give a new token only if cookie was not received_cookie

            if not received_cookie:
                token = generate_token()
                users[username].active_tokens[0] = token
                print(token)
        
            grade_content = session.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0").text
            soupified = bs(grade_content)

            links = soupified.find_all('a')
            profile = soupified.find_all('img')

            heading_breadcrumb = soupified.find_all("div", attrs = {"class" : "heading_breadcrumb"})
            sem_links = []
            for sem_link in heading_breadcrumb[0].find_all('li'):
                if (sem_link.get_text() != '|'):
                    link = sem_link.find_all('a')
                    if link == [] or link == None: 
                        sem_links.append("selected")
                    else:
                        sem_links.append("https://grades.newportml.com/grades?" + link[0].get('href').split("?")[1])

            print(sem_links)

            classes = []
            classes_href = []

            temp = []
            temp_href = []
            class_hrefs = []

            c = 0
            for l in links[18:-3]:
                temp.append(l.get_text())

                href = l.get("href")
                split = href.split("?")

                # TODO: Categorize links to direct to correct place, by default rn every directs to class
                if split[0] == "https://wa-bsd405-psv.edupoint.com/PXP_SchoolInformation.aspx":
                    temp_href.append("https://grades.newportml.com/school?" + '?'.join(split[1:]))
                elif split[0] == "https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx":
                    temp_href.append("https://grades.newportml.com/class?" + '?'.join(split[1:]))
                else:
                    temp_href.append("https://grades.newportml.com/class?" + '?'.join(split[1:]))

                c += 1

                if c % 5 == 0:
                    classes.append(zip(temp, temp_href))
                    class_hrefs.append(temp_href[0])

                    temp_href = []
                    temp = []

            if users[username].profile_picture == None:
                for i in profile:
                    if i.get("src")[-10:] == "_Photo.PNG":
                        src = "https://wa-bsd405-psv.edupoint.com/" + i.get("src")
                        users[username].profile_picture = src


            for l in soupified.find_all(attrs= {'class' : 'student'}):
                name = l.find_all('img')[0].next_sibling
                school = l.find('h2').get_text()

            # Assign user name + school
            users[username].name = name
            users[username].school = school

            if users[username].dark_mode:
                bg_color = '#222'
                text_color = '#fff'
                header_color = '#000'
            else:
                bg_color = '#eee'
                text_color = '#000'
                header_color = '#fff'

            first = users[username].first
            users[username].first = "false"

            response = make_response(render_template(path + "grade_template.html", semester_links = sem_links, class_links = class_hrefs, categories = ["Period", "Course", "Room Name", "Teacher", "Grade"], links = classes, profile = users[username].profile_picture, name = name, school = school,  bg_color = bg_color, text_color = text_color, header_color = header_color, first = first))

            print(token)
            # for testing
            response.set_cookie("token", token, httponly = True)
            response.set_cookie("username", username, httponly = True)

            # real deal
            #response.set_cookie("token", token, domain = ".newportml.com", secure = True, httponly = True)
            #response.set_cookie("username", username, domain = ".newportml.com", secure = True, httponly = True)

            return response

        else:
            return redirect("https://grades.newportml.com/?login=invalid")
    except Exception as e:
        print(e)
        return redirect("https://grades.newportml.com/?login=session_expired")

@application.route("/grades", methods = ['POST', "GET"])
def grade():
    mobile = request.args.get('mobile', default = False, type = bool)
    agu = request.args.get("AGU", default = -1, type = int)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    session = None
    received_cookie = False
    token = ''

    # no uname/password because we're getting from the website, so check cookies
    username = request.cookies.get('username')
    token = request.cookies.get('token')

    print(username, token,  "token")

    if username not in users:
        return redirect("https://grades.newportml.com/?login=ummmm")
    else:
        # check token 
        if users[username].active_tokens[0] != token:
            return redirect("https://grades.newportml.com/?login=expired")
        else:
            session = users[username].session

            # if validated, set cookie flag to True
            received_cookie = True

    try:
        if (session != None):
            hexdigest = sha.new(username.encode()).hexdigest()
            if (user_logins.get(hexdigest) != None):
                user_logins[hexdigest] += 1
            else:
                user_logins[hexdigest] = 1

            if (agu == -1):
                grade_content = session.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0").text
            else:
                prefix_ = "https://grades.newportml.com"
                grade_content = session.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx" + request.url[len(prefix_) : ]).text
            
            soupified = bs(grade_content)

            links = soupified.find_all('a')
            profile = soupified.find_all('img')
            
            heading_breadcrumb = soupified.find_all("div", attrs = {"class" : "heading_breadcrumb"})
            sem_links = []
            for sem_link in heading_breadcrumb[0].find_all('li'):
                if (sem_link.get_text() != '|'):
                    link = sem_link.find_all('a')
                    if link == [] or link == None: 
                        sem_links.append("selected")
                    else:
                        sem_links.append("https://grades.newportml.com/grades?" + link[0].get('href').split("?")[1])

            classes = []
            classes_href = []

            temp = []
            temp_href = []

            class_hrefs = []

            c = 0
            print(links)
            for l in links[18:-3]:

                temp.append(l.get_text())

                href = l.get("href")
                split = href.split("?")

                # TODO: Categorize links to direct to correct place, by default rn every directs to class
                if split[0] == "https://wa-bsd405-psv.edupoint.com/PXP_SchoolInformation.aspx":
                    temp_href.append("https://grades.newportml.com/school?" + '?'.join(split[1:]))
                elif split[0] == "https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx":
                    temp_href.append("https://grades.newportml.com/class?" + '?'.join(split[1:]))
                else:
                    temp_href.append("https://grades.newportml.com/class?" + '?'.join(split[1:]))

                c += 1

                if c % 5 == 0:
                    classes.append(zip(temp, temp_href))
                    class_hrefs.append(temp_href[0])
                    temp_href = []
                    temp = []

            if users[username].profile_picture == None:
                for i in profile:
                    if i.get("src")[-10:] == "_Photo.PNG":
                        src = "https://wa-bsd405-psv.edupoint.com/" + i.get("src")
                        users[username].profile_picture = src

            for l in soupified.find_all(attrs= {'class' : 'student'}):
                name = l.find_all('img')[0].next_sibling
                school = l.find('h2').get_text()

            if users[username].dark_mode:
                bg_color = '#222'
                text_color = '#fff'
                header_color = '#000'
            else:
                bg_color = '#eee'
                text_color = '#000'
                header_color = '#fff'


            first = users[username].first
            users[username].first = "false"

            return render_template(path + "grade_template.html", semester_links = sem_links, categories = ["Period", "Course", "Room Name", "Teacher", "Grade"], class_links = class_hrefs, links = classes, profile = users[username].profile_picture, name = name, school = school,   bg_color = bg_color, text_color = text_color, header_color = header_color, first = first)
        else:
            return redirect("https://grades.newportml.com/?login=expired")
    
    except Exception as e:
        print(e)
        return redirect("https://grades.newportml.com/?login=session_expired")

@application.route("/school", methods = ['POST', 'GET'])
def school_info():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    session = None
    received_cookie = False
    token = ''

    # no uname/password because we're getting from the website, so check cookies
    username = request.cookies.get('username')
    token = request.cookies.get('token')

    print(username, token,  "token")

    if username not in users:
        return redirect("https://grades.newportml.com/?login=ummmm")
    else:
        # check token 
        if users[username].active_tokens[0] != token:
            return redirect("https://grades.newportml.com/?login=expired")
        else:
            session = users[username].session

            # if validated, set cookie flag to True
            received_cookie = True
    
    if (session != None):

        AGU = request.args['AGU']

        school_content = session.get(add_url_params("https://wa-bsd405-psv.edupoint.com/PXP_SchoolInformation.aspx", [["AGU", AGU]])).text
        soupified = bs(school_content)

        tables = soupified.find_all("table", attrs = {"class" : "info_tbl"})
        info_tables = []        # school info, contacts

        t_idx = 0
        for t in tables:

            temp_ = []
            for row in t.find_all("tr"):
                temp__ = []

                c = 0
                for element in row.find_all("td"):
                    temp__.append(element.get_text())

                    c += 1

                temp_.append(temp__)

            t_idx += 1
            info_tables.append(temp_)

        profile = soupified.find_all('img')

        hrefs = []
        for l in soupified.find_all('a')[17:-4]:
            hrefs.append(l.get('href'))

        if users[username].profile_picture == None:
            for i in profile:
                if i.get("src")[-10:] == "_Photo.PNG":
                    src = "https://wa-bsd405-psv.edupoint.com/" + i.get("src")
                    users[username].profile_picture = src

        for l in soupified.find_all(attrs= {'class' : 'student'}):
            name = l.find_all('img')[0].next_sibling
            school = l.find('h2').get_text()

        if users[username].dark_mode:
            bg_color = '#222'
            text_color = '#fff'
            header_color = '#000'
        else:
            bg_color = '#eee'
            text_color = '#000'
            header_color = '#fff'

        return render_template(path + "school_template.html", info = info_tables[0], contacts = info_tables[1], profile = users[username].profile_picture, name = name, school = school, hrefs = hrefs,   bg_color = bg_color, text_color = text_color, header_color = header_color)
    else:
        return redirect("https://grades.newportml.com/?login=expired")


@application.route("/class", methods = ['GET', 'POST'])
def class_info():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    try:
        session = None
        received_cookie = False
        token = ''

        # no uname/password because we're getting from the website, so check cookies
        username = request.cookies.get('username')
        token = request.cookies.get('token')

        print(username, token,  "token")

        if username not in users:
            return redirect("https://grades.newportml.com/?login=ummmm")
        else:
            # check token 
            if users[username].active_tokens[0] != token:
                return redirect("https://grades.newportml.com/?login=expired")
            else:
                session = users[username].session

                # if validated, set cookie flag to True
                received_cookie = True

        AGU = request.args['AGU']
        DGU = request.args['DGU']
        VDT = request.args['VDT']
        CID = request.args['CID']
        MK = request.args['MK']
        OY = request.args['OY']
        GP = request.args['GP']

        #session = auth("s-yann", pword)

        class_content = session.get(add_url_params("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx", [["AGU", AGU], ["DGU", DGU], ["VDT", VDT], ["CID", CID], ["MK", MK], ["OY", OY], ["GP", GP]])).text
        soupified = bs(class_content)

        tables = soupified.find_all("table", attrs = {"class" : "info_tbl"})
        info_tables = []        # summary, assignments, legend
        assignment_grades = []

        if len(tables) == 3:
            t_idx = 0
        else:
            t_idx = 1

        score_idx = 0
        for t in tables:

            temp_ = []
            for row in t.find_all("tr"):
                temp__ = []

                c = 0
                temp_score_idx = 0
                appended=False
                for element in row.find_all("td"):
                    temp__.append(element.get_text())

                    if element.get_text() == "Points":
                        score_idx = temp_score_idx
                    temp_score_idx += 1

                    g = element.get_text()
                    pt = g.split("/")
                    if len(pt) == 2 and t_idx == 1:

                        try:
                            points, total = pt

                            total = float(total) + 0.01
                            percentage = min(float(points) / float(total), 1)

                            # TODO: If dark mode is on, dim
                            # FIX: Nvm lol the dark mode coloring is better than normal coloring for all uses, switching to that as default

                            assignment_grades.append(percentage)
                            appended = True

                        except ValueError:
                            pass

                    c += 1

                if not appended and t_idx == 1:
                    assignment_grades.append("NULL")

                temp_.append(temp__)

            t_idx += 1
            info_tables.append(temp_)

        profile = soupified.find_all('img')

        for i in profile:
            if i.get("src")[-10:] == "_Photo.PNG":
                src = "https://wa-bsd405-psv.edupoint.com/" + i.get("src")

        for l in soupified.find_all(attrs= {'class' : 'student'}):
            name = l.find_all('img')[0].next_sibling
            school = l.find('h2').get_text()

        if users[username].dark_mode:
            bg_color = '#222'
            text_color = '#fff'
            header_color = '#000'
        else:
            bg_color = '#eee'
            text_color = '#000'
            header_color = '#fff'

        # There is an summary table, so we'll extract categories, weights, points and points possible
        if len(info_tables) == 3:
            summary = dictionarify(info_tables[0])
            assignments = dictionarify(info_tables[1][1:])

        else:
            assignments = dictionarify(info_tables[0][1:])

            summary = {
                "Weight" : ["100."],
                "Assignment Type" : ["assignment"],
            }
        
        dates = []
        for a in assignments['Date']:
            dates.append(a)

        grade = 0
        
        class_name = soupified.find_all("option", attrs = {'selected' : "selected"})[0].get_text()

        if len(info_tables) == 3:
            return render_template(path + "class_template.html", summary = info_tables[0], assignments = info_tables[1], assignment_grades = assignment_grades, profile = src, name = name, school = school,   bg_color = bg_color, text_color = text_color, header_color = header_color, dates = dates[::-1], js_summary = summary, js_assignments = assignments, three = "true", class_name = class_name)
        else:
            return render_template(path + "class_template.html", summary = [[]], assignments = info_tables[0], assignment_grades = assignment_grades, profile = src, name = name, school = school,   bg_color = bg_color, text_color = text_color, header_color = header_color, dates = dates[::-1], js_summary = summary, js_assignments = assignments, three = "false", class_name = class_name)

    except Exception as error:
        print(error)
        return redirect("https://grades.newportml.com/?login=session_expired")

    return class_content

@application.route("/profile", methods = ['GET', 'POST'])
def profile():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    session = None
    received_cookie = False
    token = ''

    # no uname/password because we're getting from the website, so check cookies
    username = request.cookies.get('username')
    token = request.cookies.get('token')

    print(username, token,  "token")

    if username not in users:
        return redirect("https://grades.newportml.com/?login=ummmm")
    else:
        # check token 
        if users[username].active_tokens[0] != token:
            return redirect("https://grades.newportml.com/?login=expired")
        else:
            session = users[username].session

            # if validated, set cookie flag to True
            received_cookie = True

    if users[username].dark_mode:
        bg_color = '#222'
        text_color = '#fff'
        header_color = '#000'
    else:
        bg_color = '#eee'
        text_color = '#000'
        header_color = '#fff'

    return render_template(path + "profile_template.html", profile = users[username].profile_picture, name = users[username].name, school = users[username].school, token = users[username].active_tokens[0], username = users[username].username, bg_color = bg_color, text_color = text_color, header_color = header_color)

@application.route("/profile-upload", methods = ['GET', 'POST'])
def upload_profile():
    username, token = request.form['username'], request.form['token']

    # First check if token is valid
    session = None

    if username in users:
        if token in users[username].active_tokens:
            session = users[username].session
        else:
            return "Token expired, please refresh"
    else:
        return "Invalid username"

    profile = request.files['profile']

    salt = generate_token(10)
    img = open("static/profiles/profile_" + username + '_' + salt + '.png', 'wb')
    img.write(profile.read())

    users[username].profile_picture = "static/profiles/profile_" + username + '_' + salt + '.png'
    print(users[username].profile_picture, username, users)
    return "uploaded"

@application.route("/profile-setting", methods = ['GET', 'POST'])
def profile_setting():
    mobile = request.args.get('mobile', default = False, type = bool)

    if (mobile):
        path = 'mobile/'
    else:
        path = ''

    username, token, change =  request.cookies.get('username'), request.cookies.get('token'), request.form['change']

    print(username, token, change)

    if username in users:
        if token in users[username].active_tokens:
            session = users[username].session
        else:
            return "Token expired, please refresh"
    else:
        return "Invalid username"

    if change == 'mode:night':
        users[username].dark_mode = True
    elif change == 'mode:day':
        users[username].dark_mode = False

    if users[username].dark_mode:
        bg_color = '#222'
        text_color = '#fff'
        header_color = '#000'
    else:
        bg_color = '#eee'
        text_color = '#000'
        header_color = '#fff'

    return render_template(path + "profile_template.html", profile = users[username].profile_picture, name = users[username].name, school = users[username].school, token = users[username].active_tokens[0], username = users[username].username, bg_color = bg_color, text_color = text_color, header_color = header_color)

# TODO: add a function that receives a logout request that generates a new token

def auth(username, password):
    session = login_pipeline(username, password)
    html = session.get("https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0").text

    if "Unknown error while accessing the web site. Please check back later as we address the problem" in html:
        return False

    # If user is not already in users dictionary, assign it
    if username not in users:
        users[username] = User(username, session = session, init_token = generate_token())
    
    else:
        users[username].session = session

    return session

def add_url_params(base, params):
    base += '?'
    for i in range (len(params)):
        base += params[i][0] + '=' + params[i][1]

        if (i != len(params) - 1):
            base += '&'

    return base

def dictionarify(a):
    # a is a two dimensional array, arranged in rows x columns
    print(a)
    categories = a[0]
    categories_ = {_ : [] for _ in categories}

    for r in a[1:]:
        for c in range(len(r)):
            categories_[a[0][c]].append(r[c])

    return categories_

if __name__=='__main__':
    application.debug = True
    application.run()
