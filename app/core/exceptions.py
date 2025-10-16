class APIException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(APIException):
    def __init__(self, message: str = "Document not found"):
        super().__init__(message, status_code=404)


