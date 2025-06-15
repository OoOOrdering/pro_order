from rest_framework.exceptions import APIException


# 커스텀 에러 메시지
class CustomAPIException(APIException):
    def __init__(self, error_dict):
        self.status_code = error_dict.get("code", 400)
        self.detail = error_dict
