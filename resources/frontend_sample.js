// 프론트엔드(React) 예시: roles별 인증/인가 및 Mock 응답 처리
import axios from "axios";

const API_BASE = "http://3.34.108.96:8000";

// JWT 토큰 예시 (실제 로그인 후 발급받은 토큰 사용)
const adminToken = "<admin-access-token>";
const userToken = "<user-access-token>";

// 전체 유저 목록 조회 (관리자)
async function fetchUsersAsAdmin() {
  try {
    const res = await axios.get(`${API_BASE}/users/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    console.log("관리자 응답:", res.data);
  } catch (err) {
    console.error("에러:", err.response?.data);
  }
}

// 전체 유저 목록 조회 (일반회원)
async function fetchUsersAsUser() {
  try {
    const res = await axios.get(`${API_BASE}/users/`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    console.log("일반회원 응답:", res.data);
  } catch (err) {
    // 403 등 인가 실패 시
    if (err.response?.status === 403) {
      alert("권한이 없습니다. (관리자만 접근 가능)");
    }
    console.error("에러:", err.response?.data);
  }
}

// 사용 예시
fetchUsersAsAdmin();
fetchUsersAsUser();
