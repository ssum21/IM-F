# 🚀 배포 가이드

## 목차
1. [GitHub Actions 설정](#1-github-actions-설정)
2. [Synology NAS Container Manager 설정](#2-synology-nas-container-manager-설정)
3. [리버스 프록시 설정](#3-리버스-프록시-설정)
4. [DNS 설정](#4-dns-설정)
5. [SSL/TLS 인증서 설정](#5-ssltls-인증서-설정)

---

## 1. GitHub Actions 설정

### 1.1 Docker Hub Secrets 등록

GitHub Repository → Settings → Secrets and variables → Actions로 이동하여 다음 secrets를 추가합니다:

- `DOCKER_USERNAME`: `ssumuss`
- `DOCKER_PASSWORD`: Docker Hub 액세스 토큰

**Docker Hub 액세스 토큰 생성 방법:**
1. [Docker Hub](https://hub.docker.com)에 로그인
2. Account Settings → Security → New Access Token
3. 토큰 이름 입력 (예: github-actions) 후 생성
4. 생성된 토큰을 복사하여 GitHub Secrets에 저장

### 1.2 자동 빌드 확인

코드를 `main` 브랜치에 push하면 자동으로:
- Docker 이미지 빌드
- Docker Hub에 푸시
- 태그: `latest`, `main`, `<commit-sha>`

**릴리즈 버전 배포:**
```bash
git tag v1.0.0
git push origin v1.0.0
```
→ `ssumuss/oh-my-school-credit:v1.0.0` 이미지 생성

---

## 2. Synology NAS Container Manager 설정

### 2.1 Container Manager 설치

1. **Package Center** 열기
2. **Container Manager** 검색 및 설치
3. 설치 완료 후 실행

### 2.2 환경 변수 파일 준비

NAS의 적절한 위치(예: `/volume1/docker/oh-my-school-credit/`)에 `.env` 파일 생성:

```bash
UPSTAGE_API_KEY=your_actual_upstage_api_key
NEIS_API_KEY=your_actual_neis_api_key
```

**File Station에서 생성하는 방법:**
1. File Station 열기
2. `docker` 폴더 생성 (없으면)
3. `oh-my-school-credit` 폴더 생성
4. 텍스트 편집기로 `.env` 파일 생성

### 2.3 Docker Compose로 컨테이너 생성

#### 방법 1: File Station + Container Manager (권장)

1. **`docker-compose.yml` 파일을 NAS에 업로드**
   - File Station에서 `/volume1/docker/oh-my-school-credit/` 경로에 업로드

2. **Container Manager에서 프로젝트 생성**
   - Container Manager 열기
   - 좌측 메뉴: **Project** 클릭
   - **Create** 버튼 클릭
   - Project name: `oh-my-school-credit`
   - Path: `docker/oh-my-school-credit` 선택
   - Source: `docker-compose.yml` 선택
   - **Next** 클릭
   - 환경 변수 확인 후 **Done** 클릭

#### 방법 2: SSH로 설치 (고급 사용자)

```bash
# NAS에 SSH 접속
ssh admin@119.194.29.236

# 작업 디렉토리로 이동
cd /volume1/docker/oh-my-school-credit/

# Docker Compose 실행
sudo docker-compose up -d
```

### 2.4 컨테이너 확인

1. Container Manager → **Container** 메뉴
2. `oh-my-school-credit` 컨테이너가 실행 중인지 확인
3. **Details** 클릭하여 로그 확인
4. 브라우저에서 `http://119.194.29.236:8501` 접속 테스트

### 2.5 컨테이너 업데이트

새 버전이 Docker Hub에 푸시되면:

**자동 업데이트 (Container Manager GUI):**
1. Container 메뉴에서 컨테이너 선택
2. **Action** → **Update via compose file**
3. 또는 Project에서 프로젝트 선택 → **Action** → **Build**

**수동 업데이트 (SSH):**
```bash
cd /volume1/docker/oh-my-school-credit/
sudo docker-compose pull
sudo docker-compose up -d
```

---

## 3. 리버스 프록시 설정

Synology의 리버스 프록시를 사용하여 도메인을 컨테이너에 연결합니다.

### 3.1 Application Portal 설정

1. **Control Panel** → **Login Portal** → **Advanced** 탭
2. **Reverse Proxy** 섹션에서 **Create** 클릭

### 3.2 리버스 프록시 규칙 생성

**General 설정:**
- **Reverse Proxy Name**: `Oh My School Credit`
- **Source**:
  - Protocol: `HTTPS` (SSL 사용 시) 또는 `HTTP`
  - Hostname: `iamf.site`
  - Port: `443` (HTTPS) 또는 `80` (HTTP)
  - Enable HSTS: ✅ (HTTPS 사용 시)
- **Destination**:
  - Protocol: `HTTP`
  - Hostname: `localhost`
  - Port: `8501`

**Custom Header (Advanced 탭):**

WebSocket 지원을 위해 다음 헤더 추가:

```
Create → WebSocket
```

또는 Custom Header에 직접 추가:
- Header Name: `Upgrade`
- Value: `$http_upgrade`

- Header Name: `Connection`
- Value: `$connection_upgrade`

**Save** 클릭

---

## 4. DNS 설정

도메인 `iamf.site`를 NAS IP `119.194.29.236`에 연결합니다.

### 4.1 도메인 등록 업체에서 설정

도메인을 구매한 곳(예: GoDaddy, Namecheap, Cloudflare 등)에서 DNS 레코드 추가:

#### A 레코드 추가

| Type | Name              | Value          | TTL  |
|------|-------------------|----------------|------|
| A    | @                 | 119.194.29.236 | Auto |
| A    | www               | 119.194.29.236 | Auto |

또는 서브도메인 사용 시:

| Type | Name              | Value          | TTL  |
|------|-------------------|----------------|------|
| A    | school-credit     | 119.194.29.236 | Auto |

**예시 (Cloudflare):**
1. Cloudflare 대시보드 로그인
2. 도메인 선택
3. DNS 탭 → **Add record**
4. Type: `A`, Name: `@` 또는 `school-credit`, IPv4 address: `119.194.29.236`
5. Proxy status:
   - **Proxied** (오렌지 구름): Cloudflare CDN + DDoS 보호 (권장)
   - **DNS only** (회색 구름): 직접 연결
6. **Save** 클릭

### 4.2 DNS 전파 확인

DNS 설정 후 전파까지 최대 24-48시간 소요 (보통 몇 분 내 완료)

**확인 방법:**
```bash
# 터미널에서 확인
nslookup iamf.site
dig iamf.site

# 또는 온라인 도구 사용
# https://dnschecker.org/
```

---

## 5. SSL/TLS 인증서 설정

### 5.1 Let's Encrypt 인증서 발급 (Synology)

1. **Control Panel** → **Security** → **Certificate**
2. **Add** 버튼 클릭
3. **Add a new certificate** 선택 → **Next**
4. **Get a certificate from Let's Encrypt** 선택
5. 다음 정보 입력:
   - Domain name: `iamf.site` 또는 `school-credit.iamf.site`
   - Email: 본인 이메일
   - Subject Alternative Name: 추가 도메인 (선택사항)
6. **Apply** 클릭

**포트 포워딩 필요:**
- 라우터에서 외부 포트 80, 443을 NAS IP `119.194.29.236`로 포워딩
- Let's Encrypt는 포트 80으로 도메인 소유권 확인

### 5.2 인증서 할당

1. **Control Panel** → **Security** → **Certificate**
2. **Settings** 버튼 클릭
3. 서비스별 인증서 할당:
   - **System default**: Let's Encrypt 인증서 선택
   - **Reverse Proxy (iamf.site)**: 같은 인증서 선택
4. **OK** 클릭

### 5.3 Cloudflare SSL (대안)

Cloudflare를 사용하는 경우:

1. Cloudflare 대시보드 → **SSL/TLS** 탭
2. SSL 모드 선택:
   - **Flexible**: Cloudflare ↔ 방문자 간만 암호화 (빠르지만 덜 안전)
   - **Full**: NAS도 자체 서명 인증서 필요
   - **Full (strict)**: NAS에 유효한 인증서 필요 (권장)
3. **Always Use HTTPS** 활성화

---

## 6. 최종 확인

### 6.1 접속 테스트

브라우저에서 다음 URL 접속:
- `http://iamf.site` (자동으로 HTTPS 리다이렉트)
- `https://iamf.site`

### 6.2 방화벽 설정

**라우터 포트 포워딩:**
- 외부 포트 80 → NAS 119.194.29.236:80
- 외부 포트 443 → NAS 119.194.29.236:443

**Synology 방화벽 (선택사항):**
1. Control Panel → Security → Firewall
2. 규칙 추가하여 80, 443 포트 허용

### 6.3 모니터링

**Container Manager에서:**
- Container 로그 확인
- CPU/메모리 사용량 모니터링
- 재시작 정책 확인 (`unless-stopped`)

---

## 7. 트러블슈팅

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
sudo docker logs oh-my-school-credit

# 환경 변수 확인
sudo docker exec oh-my-school-credit env | grep UPSTAGE
```

### 502 Bad Gateway

- 컨테이너가 실행 중인지 확인
- 리버스 프록시 설정에서 포트 번호 확인
- WebSocket 헤더 추가 확인

### DNS 해석 안 됨

- DNS 전파 대기 (최대 48시간)
- 캐시 삭제: `ipconfig /flushdns` (Windows) 또는 `sudo dscacheutil -flushcache` (Mac)

### SSL 인증서 오류

- 도메인 소유권 확인 실패 시 포트 80 포워딩 확인
- Let's Encrypt Rate Limit: 주당 5회 재시도 제한

---

## 8. 유지보수

### 정기 업데이트

**월 1회 권장:**
```bash
# Docker 이미지 업데이트
cd /volume1/docker/oh-my-school-credit/
sudo docker-compose pull
sudo docker-compose up -d

# 사용하지 않는 이미지 정리
sudo docker image prune -a
```

### 백업

**중요 데이터:**
- `.env` 파일 (환경 변수)
- `/app/data` 볼륨 (업로드된 파일)
- `docker-compose.yml` 파일

**Synology Hyper Backup 사용:**
1. Hyper Backup 설치
2. Docker 폴더 백업 설정
3. 정기 백업 스케줄 설정

---

## 9. 참고 자료

- [Synology Container Manager 공식 문서](https://kb.synology.com/en-global/DSM/help/ContainerManager/docker_desc?version=7)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cloudflare DNS Documentation](https://developers.cloudflare.com/dns/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**배포 완료 후 이 가이드는 팀원들과 공유하거나 레포지토리에 보관하세요!** 🎉
