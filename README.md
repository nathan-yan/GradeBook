# GradeBook

GradeBook is a Synergy StudentVUE interface that looks real fancy. Synergy, I'm sure we can all agree, is not the greatest, so GradeBook has sought to improve its interface and its experience. 

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

In addition, GradeBook uses MongoDB as its database to store persistent user metadata. Obviously, anyone who forks this repository either to contribute or modify for their own purposes will not have access to the primary GradeBook database, but anyone can create a free MongoDB either locally or in the cloud using [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/lp/general?jmp=search&utm_source=bing&utm_campaign=Americas-US-Atlas-Brand-Alpha&utm_keyword=mongodb%20atlas&utm_device=c&utm_network=o&utm_medium=cpc&utm_creative={creative}&utm_matchtype=e&_bt={creative}&_bk=mongodb%20atlas&_bm=e&_bn=o&msclkid=b81529904ecb1f7f05eb73404b09188f). 

If the MongoDB is hosted in the cloud, you'll need to copy your connection string to **gb/db.py**. Then set your DB credentials as an environment variable.

`export recordbook_mongodb=CREDENTIAL`

If you're using Windows, replace the "export" with "set"

## How to Run
GradeBook is a Flask web application programmed in Python. Once all dependencies are installed and the repository has been cloned, navigate into the repository and run the application by typing these lines into the console.

```
export FLASK_APP=application.py
export FLASK_DEBUG=1
flask run --host=A.B.C.D --port=PORT
```

Replace A.B.C.D with your IP address OR use 127.0.0.1 for localhost, and replace PORT with whatever port you want. Flask uses a default of 5000. 
