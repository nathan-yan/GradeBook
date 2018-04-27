import os

DB_CREDENTIAL = os.environ.get("gradebook_mongodb")

if not (DB_CREDENTIAL):
    raise Exception("ERROR: DB_CREDENTIAL environment variable not set, GradeBook will not be able to authenticate with the database.")

SERVER_NAME = os.environ.get("gradebook_server_name")

if not (SERVER_NAME):
    print("WARNING: Server name not set, default to GenericServer")
    SERVER_NAME = "GenericServer"

themes = {
    "night" : {
        "bg_color" : "#222",
        "text_color" : "#fff",
        "header_color" : "#000"
    },
    "day" : {
        "bg_color" : "#eee",
        "text_color" : "#000",
        "header_color" : "#fff"
    }
}
