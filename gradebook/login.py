from requests import session
from bs4 import BeautifulSoup as bs

def get_value(field):
    s = field.split('=')
    if len(s) <= 1:
        return ''
    else:
        return '='.join(s[1:]).replace('"', '')

def get_input_params(split):
    params = []

    for s in split[1:-1]:
        content = s.split(' ')
        type_ = get_value(content[1])
        name = get_value(content[2])
        id_ = get_value(content[3])
        value = get_value(content[4])

        params.append([type_, name, id_, value])
    
    return params

def complete_form(givens, needed):
    form = {}

    for g in givens:
        name = g[2]
        value = g[3]

        form[name] = value
    
    for n in needed:
        form[n[0]] = n[1]

    return form

def login_pipeline(username, password):
    s = session()

    login_page = s.get('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True').text
    
    # get all form parameters
    split = login_page.split("<input")
    p = get_input_params(split)

    # complete the form with username and password 
    payload = (complete_form(p, [['username' , username], ['password', password]]))

    # post the payload to the login url
    returned = s.post('https://wa-bsd405-psv.edupoint.com/Login_Student_PXP.aspx?regenerateSessionId=True', data=payload)
    
    # now that the login cookies have been stored in the session, we'll return it so we can do whatever we want
    return s
    
    """
        response = s.get('https://wa-bsd405-psv.edupoint.com/PXP_Gradebook.aspx?AGU=0')
        print(returned.headers)
        #print(response.text)
        #print(c.get("https://wa-bsd405-psv.edupoint.com/cookies").text)
        f = open("save.html", 'w')
        f_ = open("save2.html", 'w')
        f.write(response.text)
        f_.write(returned.text)
        f_.close()
        f.close()
    """
