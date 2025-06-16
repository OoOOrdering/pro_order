import logging
import secrets
import string

logger = logging.getLogger(__name__)


def generate_django_secret_key(length=50):
    """Django SECRET_KEY 생성.

    Args:
    ----
        length (int): 키 길이 (기본값: 50)

    Returns:
    -------
        str: 생성된 SECRET_KEY

    """
    chars = string.ascii_lowercase + string.digits + "!@$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for i in range(length))


def main():
    print("🔑 Django SECRET_KEY Generator")
    print("=" * 50)

    # SECRET_KEY 생성
    secret_key = generate_django_secret_key()

    print("✅ SECRET_KEY 생성 완료!")
    print(f"📋 SECRET_KEY: {secret_key}")
    print()
    print("📝 환경변수 파일(.env)에 추가할 내용:")
    print("-" * 50)
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print("-" * 50)

    # 클립보드 복사 시도 (macOS)
    try:
        import subprocess

        subprocess.run(["pbcopy"], input=f"DJANGO_SECRET_KEY={secret_key}", text=True, check=True)
        print("📋 클립보드에 복사되었습니다!")
    except Exception as e:
        print("💡 위 내용을 수동으로 복사해서 .env 파일에 붙여넣으세요.")
        logger.error(f"Failed to copy to clipboard: {e}", exc_info=True)


if __name__ == "__main__":
    main()
