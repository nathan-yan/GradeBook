import os 

for f in ['login.py', 'application.py', 'user.py', 'templates/class_template.html', 'templates/community.html', 'templates/grade_template.html', 'templates/index.html', 'templates/issue.html', 'templates/issues.html', 'templates/profile_template.html', 'templates/school_template.html', 'templates/forbidden.html', 'templates/record.html', 'templates/docs.html', 'templates/api.html', 'templates/mobile/index.html', 'templates/mobile/grade_template.html', 'templates/mobile/profile_template.html', 'templates/mobile/class_template.html', 'templates/mobile/school_template.html']:
    c = open(f, 'r')
    contents = c.read() 
    c.close()

    c = open(f, 'w')
    #contents = contents.replace("http://grades.newportml.com", "http://127.0.0.1:5000").replace("https://grades.newportml.com", "http://127.0.0.1:5000")
    
    contents = contents.replace("http://127.0.0.1:5000", "https://grades.newportml.com")
    
    c.write(contents)
    c.close()