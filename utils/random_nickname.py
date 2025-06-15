import random

from django.contrib.auth import get_user_model

adjectives = ["상큼한", "어두운", "행복한", "귀여운", "신비한"]
animals = ["호랑이", "팬더", "고양이", "늑대", "코끼리"]


def generate_random_nickname():
    return f"{random.choice(adjectives)}_{random.choice(animals)}"


def generate_unique_numbered_nickname():
    User = get_user_model()
    random_nickname = generate_random_nickname()
    latest_nick = (
        User.objects.filter(nickname__startswith=random_nickname + "#")
        .order_by("-nickname")
        .values_list("nickname", flat=True)
        .first()
    )

    if latest_nick:
        number = int(latest_nick.split("#")[1]) + 1
    else:
        number = 1

    # 새 닉네임 반환
    return f"{random_nickname}#{str(number).zfill(4)}"
