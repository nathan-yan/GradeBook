# GradeBook

GradeBook is a Synergy StudentVUE interface that looks real fancy. Synergy, I'm sure we can all agree is not the greatest, so GradeBook has sought to improve its interface and its experience.

Gradebook is an application that is currently run on AWS Elastic Beanstalk. We use HTTPS and HSTS to ensure that all information between the user's computer and Synergy's servers is encrypted. 

## Dependencies
1. **Flask** == 0.10.1
2. **itsdangerous** == 0.24
3. **Jinja2** == 2.7.3
4. **MarkupSafe** == 0.23
5. **Werkzeug** == 0.10.1
6. **boto** >= 2.4
7. **requests** >= 2.18
8. **numpy** >= 1.1
9. **beautifulsoup4** >= 4.3.0
10. **pycrypto** >= 2.6.1
11. **pymongo** == 3.6.0


## How to Run
GradeBook is a Flask web application programmed in Python. Once all dependencies are installed and the repository has been cloned, navigate into the repository and run the application by typing these lines into the console.

### Linux
```
export FLASK_APP=application.py
export FLASK_DEBUG=1
flask run --host=A.B.C.D --port=PORT
```

### Windows
```
set FLASK_APP=application.py
set FLASK_DEBUG=1
flask run --host=A.B.C.D --port=PORT
```

Replace A.B.C.D with your IP address OR use 127.0.0.1 for localhost, and replace PORT with whatever port you want. Flask uses a default of 5000. 
