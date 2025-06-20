# 역할별(Mock) API 응답 예시 및 프론트 연동 가이드

## 1. 역할별(Mock) 응답 예시

### (1) 관리자(admin)로 전체 유저 목록 조회
- **요청**
  - `GET /users/`
  - Header: `Authorization: Bearer <admin-access-token>`
- **Mock 응답**
```json
[
  {
    "id": 1,
    "email": "admin@prorder.com",
    "role": "admin",
    "nickname": "관리자",
    ...
  },
  {
    "id": 2,
    "email": "user1@prorder.com",
    "role": "user",
    "nickname": "유저1",
    ...
  }
]
```

### (2) 일반회원(user)로 전체 유저 목록 조회
- **요청**
  - `GET /users/`
  - Header: `Authorization: Bearer <user-access-token>`
- **Mock 응답**
```json
{
  "detail": "권한이 없습니다. (관리자만 접근 가능)"
}
```

### (3) 매니저(manager)로 관리자 전용 API 접근 시
- **요청**
  - `GET /dashboard/summary/`
  - Header: `Authorization: Bearer <manager-access-token>`
- **Mock 응답**
```json
{
  "detail": "권한이 없습니다. (관리자만 접근 가능)"
}
```

---

## 2. 프론트 연동 가이드

### (1) Swagger/OpenAPI 문서 활용
- `/swagger/` (Swagger UI)에서 모든 API 명세, 파라미터, 인가 정책, 예시 응답 확인 가능
- "Try it out"으로 실제 요청/응답 테스트 및 Mock 데이터 확인 가능
- OpenAPI 스펙(JSON): `/swagger.json`에서 추출 가능 (Postman 등에서 Import)

### (2) 역할별 인가 정책 확인
- 각 API의 Swagger 문서(operation_description)에 `role=admin` 등 인가 조건 명시
- 403 Forbidden 응답 시 detail 메시지로 인가 실패 사유 제공

### (3) 프론트 개발 체크리스트
- 요청 시 반드시 JWT 토큰 등 인증 헤더 포함
- 인가 실패(403) 응답 처리 및 사용자 안내
- Swagger 문서 기반 자동 코드 생성/Mock 서버 연동 가능 (Swagger Codegen, Postman 등 활용)

---

## 3. Postman Collection 예시
- `resources/postman_collection.json` 파일을 Postman에서 Import하면 roles별 Mock 응답 테스트 가능
- 변수(base_url, admin_token, user_token)로 환경별 손쉬운 테스트 지원

## 4. 프론트엔드 샘플 코드(React/JS)
- `resources/frontend_sample.js` 참고
- roles별 인증/인가, 403 응답 처리, Mock 응답 활용 예시 포함

```js
// 예시 코드 일부
import axios from 'axios';
...
```

---
> 추가 샘플, Mock, 연동 가이드가 필요하면 언제든 요청 바랍니다.
