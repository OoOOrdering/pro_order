from rest_framework.response import Response


def success_response(data=None, message="성공", code=200):
    return Response(
        {
            "code": code,
            "message": message,
            "data": data,
        },
        status=code,
    )


def error_response(message="오류", code=400, data=None):
    return Response(
        {
            "code": code,
            "message": message,
            "data": data,
        },
        status=code,
    )
