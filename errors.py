class ApiError(Exception):
    status = 400
    code = "BAD_REQUEST"

    def __init__(self, message, code=None, field=None, details=None, status=None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.details = details or {}
        if code:
            self.code = code
        if status:
            self.status = status

    def to_dict(self):
        body = {"error": self.message, "code": self.code}
        if self.field:
            body["field"] = self.field
        if self.details:
            body["details"] = self.details
        return body


class ValidationError(ApiError):
    status = 400
    code = "INVALID_INPUT"


class SolverError(ApiError):
    status = 500
    code = "SOLVER_ERROR"
