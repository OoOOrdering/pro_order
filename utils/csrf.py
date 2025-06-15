# utils/csrf.py
import hashlib
import hmac
import secrets
import time

from config.settings.settings import SECRET_KEY

# HMAC(Hash-based Message Authentication Code)**를 이용해 토큰의 위변조를 방지하는 구조


CSRF_TOKEN_EXPIRY_SECONDS = 60 * 60 * 3  # 3시간 유효기간


# 위조 방지용 사용자 정의 CSRF 토큰 생성
def generate_csrf_token():
    raw_token = secrets.token_hex(32)
    expiry_timestamp = int(time.time()) + CSRF_TOKEN_EXPIRY_SECONDS
    data_to_sign = f"{raw_token}.{expiry_timestamp}"
    signature = hmac.new(
        SECRET_KEY.encode(), data_to_sign.encode(), hashlib.sha256
    ).hexdigest()
    return f"{raw_token}.{expiry_timestamp}.{signature}"


# secrets.token_hex(32) : 32바이트 길이의 랜덤한 16진수 문자열 생성 (64자리)
# expiry_timestamp : UNIX 타임스탬프(만료시간)
# hmac.new() : SECRET_KEY를 이용해 서명(Signature) 생성
# return : 최종 토큰 형식: "랜덤값.서명" 형태로 반환


# 전달받은 CSRF 토큰이 유효한지 검증
def validate_csrf_token(token):
    try:
        raw_token, expiry_timestamp, signature = token.split(".")
        expected_data = f"{raw_token}.{expiry_timestamp}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(), expected_data.encode(), hashlib.sha256
        ).hexdigest()

        # 서명 검증
        if not hmac.compare_digest(signature, expected_signature):
            return False

        # 만료시간 검증
        if int(expiry_timestamp) < int(time.time()):
            return False

        return True
    except Exception:
        return False


# token.split('.')	토큰을 랜덤값과 서명으로 분리
# expected_signature	서버에서 다시 계산한 올바른 서명
# compare_digest	전달받은 서명과 계산된 서명이 일치하는지 안전하게 비교
# except	포맷 오류 등 예외 발생 시 False 반환

# CSRF 토큰의 위변조 방지 + 만료시간 검증을 안전하게 수행.
# 서버에 별도 저장소 없이 Stateless 방식으로 보안을 유지.
# 서명만큼은 절대 위조할 수 없기 때문에,
# 만료시간을 수정해도 소용 없음.
