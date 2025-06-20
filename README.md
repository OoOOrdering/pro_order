# ORDER
# trigger

---

## 프로젝트 개요
ORDER는 Django/DRF 기반의 실시간 주문·게시글·FAQ·채팅 등 다양한 사용자 참여형 서비스 백엔드입니다.
회원가입, 역할 기반 권한, 입력 정책(닉네임/비속어/길이 제한), 실시간 채팅, 알림, 로그, Throttle, API 문서화, Mock/테스트, 프론트 연동 가이드 등 실제 서비스 수준의 일관성·정합성·보안 정책을 갖춘 통합 백엔드 프로젝트입니다.

## 주요 기능
- 회원가입/로그인/이메일 인증/프로필 관리(닉네임만 필수, 10자 제한, 비속어 필터)
- 역할 기반 권한(관리자/매니저/일반회원) 및 API 인가 정책
- 게시글/리뷰/FAQ/채팅/알림/좋아요/작업 등 CRUD 및 실시간 기능
- DRF Pagination, Throttle, 로그, 예외/응답 일관화
- Swagger(OpenAPI) 기반 API 문서 자동화 및 Mock/테스트/샘플 코드 제공
- Postman Collection, 프론트엔드 연동 가이드, 샘플 JS 코드 제공
- 전체 테스트 코드 및 정책 일관성 자동 검증(pytest)

## 기술 스택
- Python 3.12, Django 5, Django REST Framework, SimpleJWT, Celery, Channels, Redis, PostgreSQL/SQLite
- drf-yasg(Swagger), pytest, Faker, cloudinary, S3, dotenv 등

## API 문서/가이드
- `/swagger/` (Swagger UI, 모든 API/권한/예시/Mock 확인)
- `/swagger.json` (OpenAPI 스펙, Postman 등에서 Import 가능)
- `resources/api_mock_and_front_guide.md` (Mock 응답, 역할별 인가, 프론트 연동 가이드)
- `resources/postman_collection.json` (Postman 테스트용)
- `resources/frontend_sample.js` (React/JS 인증/인가/Mock 샘플)

## 테스트/정책
- pytest 기반 전체 테스트 코드 제공(회원가입, 입력 검증, 권한, CRUD, 예외 등)
- 모든 정책/코드/테스트 일관성 자동 검증(테스트 100% 통과)
- 비속어/닉네임/권한/Throttle 등 정책은 코드와 테스트에 모두 반영

## 프론트 연동 체크리스트
- 모든 요청에 JWT 토큰 등 인증 헤더 필수
- 401/403 등 인가 실패 응답 처리 및 사용자 안내
- Swagger 문서 기반 자동 코드 생성/Mock 서버 연동 가능

---

상세 Mock/테스트/샘플/연동 가이드는 `resources/` 폴더 및 Swagger 문서 참고.
