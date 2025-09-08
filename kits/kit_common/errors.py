from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(self, code: int, type: str, message: str):
        self.code = code
        self.type = type
        self.message = message
        super().__init__(message)


def http_error_response(code: int, type: str, message: str):
    return JSONResponse(
        status_code=code,
        content={
            "detail": {
                "error": {
                    "code": code,
                    "type": type,
                    "message": message,
                }
            }
        },
    )

