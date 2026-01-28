# 🚀 Streamlit Cloud 배포 가이드

Streamlit Cloud에 앱을 배포하는 가장 간단한 방법입니다. **완전 무료**이며 GitHub과 자동 연동됩니다!

---

## 📋 필요한 것

- ✅ GitHub 계정
- ✅ 이 레포지토리가 GitHub에 푸시되어 있을 것
- ✅ Upstage API 키
- ✅ (선택) 나이스 API 키

---

## 1️⃣ 코드를 GitHub에 푸시

```bash
# 아직 푸시하지 않았다면
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

---

## 2️⃣ Streamlit Cloud 가입 및 앱 배포

### 2.1 Streamlit Cloud 접속

1. https://streamlit.io/cloud 방문
2. **Sign up** 또는 **Sign in with GitHub** 클릭
3. GitHub 계정으로 로그인 및 권한 승인

### 2.2 새 앱 배포

1. **Streamlit Cloud 대시보드**에서 **"New app"** 버튼 클릭
2. 다음 정보 입력:

   **Repository 설정:**
   - Repository: `ssumuss/Oh_my_school_credit` (본인의 레포지토리 선택)
   - Branch: `main`
   - Main file path: `app.py`

   **App settings:**
   - App URL: 기본값 사용 또는 커스텀 (예: `oh-my-school-credit`)
     - 최종 URL: `https://oh-my-school-credit.streamlit.app`

3. **Advanced settings** 클릭 (중요!)

   **Python version:**
   - Python version: `3.11` (권장)

4. **Deploy!** 클릭

---

## 3️⃣ Secrets (환경 변수) 설정

앱 배포 후 API 키를 안전하게 설정합니다.

### 3.1 Secrets 추가

1. Streamlit Cloud 대시보드에서 배포한 앱 선택
2. 오른쪽 메뉴에서 **⚙️ Settings** 클릭
3. 좌측 메뉴에서 **Secrets** 클릭
4. 다음 내용을 **TOML 형식**으로 입력:

```toml
# Upstage API 키 (필수)
UPSTAGE_API_KEY = "up_xxxxxxxxxxxxxxxxxxxxx"

# 나이스 API 키 (선택사항)
NEIS_API_KEY = "your_neis_api_key_here"
```

5. **Save** 클릭

### 3.2 앱에서 Secrets 사용 방법

코드에서는 다음과 같이 접근합니다:

```python
import streamlit as st

# Streamlit Cloud에서 자동으로 로드됨
api_key = st.secrets["UPSTAGE_API_KEY"]
```

**로컬 개발 시:**
- `.streamlit/secrets.toml` 파일 생성 (`.gitignore`에 포함됨)
- 위와 동일한 형식으로 작성

---

## 4️⃣ 커스텀 도메인 연결 (선택사항)

Streamlit Cloud는 기본적으로 `your-app.streamlit.app` 도메인을 제공하지만, 커스텀 도메인도 연결 가능합니다.

### 4.1 도메인 설정

1. Streamlit Cloud 대시보드 → 앱 선택 → **Settings** → **General**
2. **Custom domain** 섹션에서 도메인 입력 (예: `iamf.site`)
3. DNS 설정 안내가 표시됨

### 4.2 DNS 레코드 추가

도메인 등록업체에서 **CNAME** 레코드 추가:

| Type  | Name              | Value                                    | TTL  |
|-------|-------------------|------------------------------------------|------|
| CNAME | @                 | `your-app.streamlit.app`                 | Auto |
| CNAME | www               | `your-app.streamlit.app`                 | Auto |

**Cloudflare 사용 시:**
- Proxy status: **DNS only** (회색 구름) 선택 필수
- Proxied 모드는 Streamlit Cloud와 호환되지 않음

### 4.3 SSL 인증서

Streamlit Cloud가 자동으로 Let's Encrypt SSL 인증서를 발급해줍니다. 별도 설정 불필요!

---

## 5️⃣ 자동 업데이트 설정

Streamlit Cloud는 GitHub과 자동 연동되어, 코드를 푸시하면 자동으로 재배포됩니다.

### 자동 재배포 활성화

1. 앱 **Settings** → **Advanced settings**
2. **Auto-reboot** 옵션이 기본적으로 활성화되어 있음
3. `main` 브랜치에 푸시하면 자동으로 재배포

### 수동 재부팅

필요 시 수동으로 재부팅:
1. 앱 대시보드에서 **⋮** (메뉴) 클릭
2. **Reboot app** 선택

---

## 6️⃣ 모니터링 및 로그

### 앱 로그 확인

1. Streamlit Cloud 대시보드에서 앱 선택
2. 하단에 실시간 로그가 표시됨
3. 에러 발생 시 여기서 확인 가능

### 앱 사용량 확인

1. **Settings** → **Analytics**
2. 방문자 수, 리소스 사용량 등 확인

**무료 플랜 제한:**
- 공개 앱: 무제한
- 비공개 앱: 1개
- 리소스: 1GB RAM, 1 CPU 코어

---

## 7️⃣ 트러블슈팅

### "Module not found" 에러

**원인:** `requirements.txt`에 패키지가 누락됨

**해결:**
1. 로컬에서 `pip freeze > requirements.txt`
2. Git commit & push
3. Streamlit Cloud가 자동 재배포

### "Secrets not found" 에러

**원인:** Secrets가 설정되지 않음

**해결:**
1. 앱 Settings → Secrets
2. TOML 형식으로 API 키 추가
3. 저장 후 앱 자동 재시작

### 앱이 느리거나 멈춤

**원인:** 무료 플랜 리소스 제한 (1GB RAM)

**해결 방법:**
- 큰 파일은 `@st.cache_data` 데코레이터 사용하여 캐싱
- 불필요한 데이터 로드 최소화
- 필요 시 유료 플랜으로 업그레이드

### 배포 실패

**확인 사항:**
1. `requirements.txt` 파일 존재 여부
2. `app.py` 파일 경로 정확한지
3. Python 버전 호환성 (3.11 권장)
4. 로그에서 에러 메시지 확인

---

## 8️⃣ 비용 및 제한사항

### 무료 플랜 (Community Cloud)

✅ **포함 사항:**
- 무제한 공개 앱
- 1GB RAM per app
- GitHub 자동 연동
- SSL 인증서 자동 발급
- 커스텀 도메인 지원

❌ **제한 사항:**
- 비공개 앱 1개만 가능
- 리소스 제한 (RAM, CPU)
- 동시 접속자 수 제한 (일반적으로 문제 없음)

### 유료 플랜

필요 시 업그레이드:
- **Developer ($20/month):** 비공개 앱 3개, 더 많은 리소스
- **Team ($250/month):** 팀 협업, 더 많은 앱 및 리소스

---

## 9️⃣ 추가 최적화 팁

### 캐싱 사용

```python
import streamlit as st

@st.cache_data
def load_data():
    # 데이터 로딩 로직
    return data

@st.cache_resource
def load_model():
    # 모델 로딩 로직
    return model
```

### 비밀번호 보호 (선택사항)

Streamlit Cloud는 기본 인증 기능을 제공하지 않지만, 코드로 구현 가능:

```python
import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Main Streamlit app starts here
st.write("Main app content")
```

---

## 🎉 완료!

이제 앱이 다음 URL에서 접근 가능합니다:
- `https://oh-my-school-credit.streamlit.app` (기본 도메인)
- `https://iamf.site` (커스텀 도메인 설정 시)

### 다음 단계

1. ✅ 앱이 정상 작동하는지 확인
2. ✅ API 키가 올바르게 설정되었는지 테스트
3. ✅ 팀원들과 URL 공유
4. ✅ 사용자 피드백 수집 및 개선

---

## 📚 참고 자료

- [Streamlit Cloud 공식 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets 관리 가이드](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [커스텀 도메인 설정](https://docs.streamlit.io/streamlit-community-cloud/get-started/share-your-app#custom-subdomains)

---

**배포 완료 후 URL을 공유해보세요!** 🚀
