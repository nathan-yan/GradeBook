class User:
    def __init__(self, username, session = None, init_token = None):
        if init_token == None:
            self.active_tokens = ["sometokenloma"]
        else:
            self.active_tokens = [init_token]
            
        self.session = session

        self.username = username
        self.profile_picture = None

        self.name = ""
        self.school = ""
    
        self.dark_mode = False

        self.first = "true"