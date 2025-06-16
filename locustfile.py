import random

from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)  # 각 작업 사이의 대기 시간 (초)

    # 호스트를 명시적으로 설정하지 않으면 Locust 웹 UI에서 입력해야 합니다.
    # host = "http://localhost:8000"

    def on_start(self):
        """Locust 테스트 시작 시 각 User가 한 번 호출하는 메서드."""
        self.client.headers = {"Content-Type": "application/json"}
        self.registered_users = []

    @task(10)  # 이 태스크는 다른 태스크보다 10배 더 자주 실행됩니다.
    def register_and_login(self):
        """사용자 등록 및 로그인 시나리오."""
        # 고유한 이메일 생성
        email = f"test_user_{random.randint(0, 1000000)}@example.com"
        nickname = f"testuser_{random.randint(0, 1000000)}"
        password = "StrongPass123!"

        # 회원가입
        signup_data = {
            "email": email,
            "password": password,
            "password_confirm": password,
            "nickname": nickname,
            "name": "Test User",
        }
        signup_response = self.client.post("/api/users/signup/", json=signup_data, name="/api/users/signup/")
        if signup_response.status_code == 201:
            self.registered_users.append({"email": email, "password": password})
            print(f"Registered user: {email}")
        elif signup_response.status_code == 400 and "email" in signup_response.json().get("data", {}):
            print(f"User already registered (expected for some tests): {email}")
        else:
            print(f"Signup failed for {email}: {signup_response.status_code} - {signup_response.text}")
            return

        # 로그인
        login_data = {"email": email, "password": password}
        login_response = self.client.post("/api/users/login/", json=login_data, name="/api/users/login/")

        if login_response.status_code == 200:
            access_token = login_response.json()["data"]["access_token"]
            csrf_token = login_response.json()["data"]["csrf_token"]
            self.client.headers.update({"Authorization": f"Bearer {access_token}", "X-CSRFToken": csrf_token})
            print(f"Logged in user: {email}")
        else:
            print(f"Login failed for {email}: {login_response.status_code} - {login_response.text}")

    @task(5)
    def view_profile(self):
        """프로필 조회 시나리오."""
        if hasattr(self.client, "headers") and "Authorization" in self.client.headers:
            self.client.get("/api/users/profile/", name="/api/users/profile/")
        else:
            print("Skipping profile view: not authenticated.")

    @task(2)
    def update_profile(self):
        """프로필 업데이트 시나리오."""
        if hasattr(self.client, "headers") and "Authorization" in self.client.headers:
            new_nickname = f"updateduser_{random.randint(0, 1000000)}"
            update_data = {"nickname": new_nickname}
            self.client.patch(
                "/api/users/profile/",
                json=update_data,
                name="/api/users/profile/update",
            )
        else:
            print("Skipping profile update: not authenticated.")
