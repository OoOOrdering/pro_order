# API 정책/샘플/테스트/프론트 연동 종합 가이드

---

## 1. 주요 API별 정책 표 (실제 코드 기반)

| API 엔드포인트         | 필수 파라미터                | 선택 파라미터 | 권한(roles)      | 예상 응답/에러 예시                |
|------------------------|------------------------------|---------------|------------------|-------------------------------------|
| POST `/users/signup/`  | email, password, nickname    | -             | AllowAny         | 201: 가입 성공<br>400: 입력 오류, 닉네임 비속어/중복/10자 초과 |
| GET `/users/`          | -                            | page, search  | admin            | 200: 전체 유저 목록<br>403: 권한 없음 |
| POST `/faq/`           | title, content               | category      | admin            | 201: 등록 성공<br>403: 권한 없음<br>400: 비속어 포함 |
| GET `/faq/`            | -                            | page, search  | 인증(모두)        | 200: FAQ 목록<br>401: 인증 필요      |
| POST `/chat_room/`     | name, max_participants       | description, participant_ids | 인증(모두) | 201: 생성 성공<br>401: 인증 필요 |

---

## 2. Swagger 문서 operation_description 예시 (실제 정책 반영)

```python
@swagger_auto_schema(
    operation_summary="회원가입",
    operation_description="""
- **정책**
    - 닉네임: 10자 이하, 비속어/중복 불가
    - 이메일/비밀번호 필수, 이메일 인증 필요
- **권한**: 누구나(AllowAny)
- **예상 응답**
    - 201: 가입 성공
    - 400: 닉네임 비속어/중복/10자 초과, 이메일 중복 등
- **Mock**
    - { "detail": "닉네임에 비속어가 포함되어 있습니다." }
    - { "detail": "이미 사용 중인 이메일입니다." }
""",
    responses={201: ..., 400: "...", 403: "..."}
)
```

---

## 3. 입력 검증/권한 실패 Mock 응답 예시

```json
// 닉네임 비속어
{ "detail": "닉네임에 비속어가 포함되어 있습니다." }
// 닉네임 10자 초과
{ "detail": "닉네임은 10자 이하여야 합니다." }
// 권한 없음(403)
{ "detail": "권한이 없습니다. (관리자만 접근 가능)" }
// 인증 없음(401)
{ "detail": "인증 정보가 없습니다." }
```

---

## 4. 프론트엔드 샘플 코드 (React/JS, axios, 401/403 처리)

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000';
const adminToken = '<admin-access-token>';
const userToken = '<user-access-token>';

// 관리자 유저 목록 조회
async function fetchUsersAsAdmin() {
  try {
    const res = await axios.get(`${API_BASE}/users/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    console.log('관리자 응답:', res.data);
  } catch (err) {
    if (err.response?.status === 403) {
      alert('권한이 없습니다. (관리자만 접근 가능)');
    }
    if (err.response?.status === 401) {
      alert('로그인이 필요합니다.');
    }
    console.error('에러:', err.response?.data);
  }
}

// 회원가입 예시
async function signup(email, password, nickname) {
  try {
    const res = await axios.post(`${API_BASE}/users/signup/`, {
      email, password, password_confirm: password, nickname
    });
    alert('가입 성공!');
  } catch (err) {
    alert(err.response?.data?.detail || '가입 실패');
  }
}
```

---

## 5. Postman Collection/Mock

- `resources/postman_collection.json` 파일을 Postman에서 Import
- 환경변수(base_url, admin_token, user_token)로 역할별 Mock 응답/실제 API 테스트
- 각 요청에 "예상 응답"과 "실패 Mock" 예시 포함

---

## 6. pytest 테스트 코드 샘플 (실제 정책 기반)

```python
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_signup_nickname_profanity(api_client):
    url = reverse("user:signup")
    data = {
        "email": "test2@example.com",
        "password": "Qwer1234!",
        "password_confirm": "Qwer1234!",
        "nickname": "욕설",  # profanity_filter에 걸리는 단어
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "비속어" in response.data["detail"]

@pytest.mark.django_db
def test_user_list_admin_only(api_client, admin_user):
    url = reverse("user:user-list")
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_user_list_forbidden_for_normal_user(api_client, normal_user):
    url = reverse("user:user-list")
    api_client.force_authenticate(user=normal_user)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
```

---

## 7. 자동 코드 생성/Mock 서버 연동

- Swagger/OpenAPI 스펙(`/swagger.json`)을 Postman, Swagger Codegen 등에서 Import
- 프론트엔드에서 자동 타입/클라이언트 코드 생성, Mock 서버 연동 가능

---

> 본 파일은 실제 프로젝트 정책/구현/테스트/가이드에 맞춰 바로 활용할 수 있도록 작성되었습니다. 추가 샘플/정책/테스트/문서화가 필요하면 언제든 요청 바랍니다.
