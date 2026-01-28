# 🏫 NEIS 교육정보 API 통합 가이드

## 개요

나이스 교육개방정보 포털 API를 활용하여 학교 기본정보 및 시간표 조회 기능을 구현했습니다.

## 구현된 기능

### 1. 학교 기본정보 조회 API
- **엔드포인트**: `https://open.neis.go.kr/hub/schoolInfo`
- **기능**: 학교명으로 학교 검색 및 상세 정보 조회
- **반환 정보**:
  - 학교코드 (행정표준코드)
  - 시도교육청코드
  - 학교명, 주소, 홈페이지
  - 학교 유형 (일반고/특목고 등)

### 2. 고등학교 시간표 조회 API
- **엔드포인트**: `https://open.neis.go.kr/hub/hisTimetable`
- **기능**: 학교별 시간표 조회 및 개설 과목 추출
- **파라미터**:
  - 시도교육청코드 (필수)
  - 학교코드 (필수)
  - 학년도 (선택 - 기본값: 현재 학년도)
  - 학기 (선택 - 기본값: 현재 학기)
  - 학년 (선택)

### 3. 과목 추출 및 분류
- 시간표에서 학년별 개설 과목 자동 추출
- 과목 카테고리 자동 분류:
  - **일반선택**: 기본 교과목
  - **진로선택**: II, 심화, 실험, 프로그래밍 등
  - **융합선택**: 생활, 실용, 문화 관련 과목

## API 명세서 준수 사항

### 기본 인자
```python
{
    "KEY": "your_api_key",        # 인증키
    "Type": "json",                # 응답 형식
    "pIndex": 1,                   # 페이지 위치
    "pSize": 100                   # 페이지당 요청 개수 (최대 1000)
}
```

### 에러 처리
명세서의 모든 에러 코드를 처리합니다:
- `300`: 필수 값 누락
- `290`: 인증키 오류
- `333`: 타입 오류
- `336`: 요청 크기 초과
- `337`: 트래픽 제한
- `500/600/601`: 서버 오류
- `200`: 데이터 없음

## 코드 구조

### 파일 위치
- `utils/neis_api.py`: NEIS API 클라이언트 메인 코드
- `test_neis_api.py`: API 테스트 스크립트
- `.env`: API 키 저장

### 주요 클래스

#### NeisAPI
```python
from utils.neis_api import NeisAPI

# API 초기화 (자동으로 .env에서 키 로드)
api = NeisAPI()

# 학교 검색
schools = api.search_school("서울과학고")

# 시간표 조회
timetable = api.get_timetable(
    edu_office_code="B10",
    school_code="7010084",
    grade="1"
)

# 개설 과목 추출
subjects = api.get_school_subjects("B10", "7010084")

# 카테고리별 분류
categorized = api.get_subjects_categorized("B10", "7010084")
```

## 테스트 방법

### 1. API 키 설정
`.env` 파일에 NEIS API 키를 추가합니다:
```bash
NEIS_API_KEY=your_api_key_here
```

API 키 발급: https://open.neis.go.kr (회원가입 후 인증키 신청)

### 2. 테스트 실행
```bash
python3 test_neis_api.py
```

## 앱 통합

### Streamlit 앱에서 사용
`app.py`의 Step 3에서 NEIS API를 활용합니다:

```python
# NEIS API 초기화
from utils.neis_api import NeisAPI
neis = NeisAPI()

# 학교 검색
schools = neis.search_school(search_query)

# 선택한 학교의 과목 조회
courses = neis.get_subjects_categorized(
    school.edu_office_code,
    school.code
)
```

## 자동 설정 기능

### 1. 학년도 자동 설정
- 3월 이전: 전년도
- 3월 이후: 현재 연도
- 현재: 2025학년도

### 2. 학기 자동 설정
- 3~8월: 1학기
- 9~2월: 2학기
- 현재: 2학기 (1월)

## 에러 처리 및 폴백

### 네트워크 오류시
- 샘플 학교 데이터 반환
- 샘플 과목 데이터 반환

### API 키 없을 시
- "SAMPLE" 키 사용 (제한적)
- 폴백 데이터로 동작

## 시도교육청 코드

```python
EDU_OFFICE_CODES = {
    "서울": "B10", "부산": "C10", "대구": "D10", "인천": "E10",
    "광주": "F10", "대전": "G10", "울산": "H10", "세종": "I10",
    "경기": "J10", "강원": "K10", "충북": "M10", "충남": "N10",
    "전북": "P10", "전남": "Q10", "경북": "R10", "경남": "S10", "제주": "T10"
}
```

## 테스트 결과 예시

### 서울과학고등학교
- 교육청 코드: B10 (서울특별시교육청)
- 학교 코드: 7010084
- 개설 과목: 171개 (전 학년)
  - 1학년: 12개
  - 2학년: 101개
  - 3학년: 58개

### 과목 카테고리 분류
- 일반선택: 96개
- 진로선택: 67개 (II, 심화, 실험, 프로그래밍 등)
- 융합선택: 6개 (생활 관련)

## 개선 사항

### 명세서 반영 내용
1. ✅ 현재 학년도 자동 설정 (2025)
2. ✅ 현재 학기 자동 설정
3. ✅ 에러 코드 전체 매핑
4. ✅ API 응답 구조 검증
5. ✅ 네트워크 에러 처리 강화
6. ✅ 요청 파라미터 검증

### 추가 구현 기능
1. ✅ 과목 자동 카테고리 분류
2. ✅ 학년별 과목 추출
3. ✅ 중복 제거 및 정렬
4. ✅ 폴백 데이터 지원

## 참고 자료

- NEIS 오픈 API 포털: https://open.neis.go.kr
- 학교기본정보 명세서: `/Users/sumin/Downloads/학교기본정보_오픈API명세서.csv`
- 고등학교시간표 명세서: `/Users/sumin/Downloads/고등학교시간표_오픈API명세서 (1).csv`

---

**제작**: I'MF (아이엠에프) - 고교학점제 맞춤 과목 설계 AI Agent 서비스
