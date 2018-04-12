class AuthError(Exception):
    def __init__(self, message):
        super().__init__(message)

class UninitializedUserError(Exception):
    def __init__(self, message):
        super().__init__(message)