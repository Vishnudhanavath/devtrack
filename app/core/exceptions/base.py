class AppException(Exception):
    """Base class for expected application errors."""
    ## here Exception is a built-in lass in python which is used to handle the errors and exceptions in the code.
#     Here, Exception is a built-in Python class.

# Python uses exceptions to signal that an error has occurred
# 
#  and allow the program to handle it.




    def __init__(
        self,
        message: str,
        status_code: int = 500,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ResourceConflictError(AppException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)








