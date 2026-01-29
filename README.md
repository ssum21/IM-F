# I'MF

F학점에서 Future로 — AI 기반 고교학점제 맞춤 설계

## 개요

학생의 생활기록부 PDF를 분석하여 고교학점제에 최적화된 과목 조합을 추천하는 웹 애플리케이션입니다. [Upstage Solar API](https://upstage.ai)를 활용하여 문서 파싱부터 추천 근거 검증까지 전 과정을 자동화합니다.

**주요 기능**
- PDF 생활기록부 자동 분석 및 정보 추출
- [NEIS 교육정보 API](https://open.neis.go.kr) 연동으로 실제 학교별 개설 과목 조회
- 8개 주요 대학, 100개 이상 모집단위별 권장과목 RAG 시스템
- 3년간 192학점 과목 조합 AI 추천 (2022 개정 교육과정 기준)
- AI 추론 과정 실시간 스트리밍 및 추천 근거 검증

## Upstage AI 기능 활용

이 프로젝트는 Upstage의 4가지 핵심 API를 단계별로 활용합니다.

### 1. Document Parse API

생활기록부 PDF를 텍스트로 변환하는 OCR 엔진입니다. 스캔본 PDF도 정확하게 인식하여 텍스트, 테이블, 페이지별 구조를 추출합니다.

**구현 위치**: [`agents/document_agent.py`](agents/document_agent.py)

**특징**
- 바이트 스트림 직접 전송으로 Streamlit 파일 업로드 지원
- 다양한 API 응답 구조 처리 (content, text, html, elements 필드)
- 페이지별 텍스트 및 테이블 데이터 분리 추출
- 생활기록부 섹션 자동 분류 (인적사항, 수상경력, 교과학습발달상황 등)

### 2. Information Extract API

비구조화된 텍스트에서 JSON 스키마 기반으로 구조화된 정보를 추출합니다.

**구현 위치**: [`agents/extract_agent.py`](agents/extract_agent.py), [`utils/schema.py`](utils/schema.py)

**특징**
- [Pydantic](https://docs.pydantic.dev) 스키마 → JSON Schema 자동 변환
- 학생 이름, 학교 유형, 학년, 강점/약점 과목, 수상 경력, 동아리 활동, 진로 희망, 담임 의견 등 추출
- 타입 안전성 보장 (배열, 문자열, 정수 등 필드별 타입 검증)
- 실시간 스트리밍으로 추출 과정 시각화

### 3. Solar Pro 3 LLM (Reasoning Mode)

학생 프로필, 학교 개설 과목, 목표 대학/전공을 종합하여 맞춤형 과목 조합을 추천합니다.

**구현 위치**: [`agents/recommend_agent.py`](agents/recommend_agent.py)

**특징**
- Reasoning 모드 활성화로 논리적 사고 과정 노출
- 대학 입학전형 RAG 데이터베이스 활용 (권장과목 자동 반영)
- 학년별/학기별 과목 배치 (1학년 48학점 공통과목 + 2-3학년 144학점 선택과목)
- 총 학점 규칙 준수 (학기당 25-34학점)
- 추천 근거 및 핵심 포인트 설명 생성

**RAG 통합**
- [`utils/university_rag.py`](utils/university_rag.py)에서 대학/전공별 권장과목 검색
- [`data/university_requirements_rag.json`](data/university_requirements_rag.json)에 서울대, 연세대, 고려대, 성균관대, 경희대, 중앙대 등 주요 대학의 모집단위별 권장과목 저장
- AI 프롬프트에 권장과목 정보 자동 주입

### 4. Groundedness Check API

AI 추천 결과가 학생 프로필에 근거하고 있는지 검증합니다.

**구현 위치**: [`agents/verify_agent.py`](agents/verify_agent.py)

**특징**
- 추천 내용과 학생 생활기록부 간의 일치도 점수 산출
- 발견된 근거 목록 추출 (예: "수학 성적 우수", "정보올림피아드 수상")
- 개선 제안 생성 (추천에 부족한 부분 지적)
- 실시간 스트리밍으로 검증 과정 시각화

## 기술 스택

### 프레임워크 & API

**[Streamlit](https://streamlit.io)**
Python 기반 웹 애플리케이션 프레임워크. 파일 업로드, 멀티스텝 폼, 세션 상태 관리, 프로그레스 바 등 제공.

**[Upstage Solar API](https://console.upstage.ai)**
Document Parse, Information Extract, Solar Pro 3 LLM, Groundedness Check 통합 활용.

**[NEIS Open API](https://open.neis.go.kr)**
나이스 교육정보 개방 포털. 학교 기본정보 조회 및 시간표 API로 실제 개설 과목 데이터 수집. [`utils/neis_api.py`](utils/neis_api.py)에서 구현.

### 라이브러리

**[Pydantic](https://docs.pydantic.dev)**
데이터 검증 및 직렬화. JSON 스키마 자동 생성으로 Information Extract API 호출 시 타입 보장.

**[OpenAI Python SDK](https://github.com/openai/openai-python)**
Upstage API 호출. Solar LLM은 OpenAI 호환 인터페이스 제공.

**[Python-dotenv](https://github.com/theskumar/python-dotenv)**
환경 변수 관리. API 키 등 민감 정보를 `.env` 파일로 분리.

**[Requests](https://requests.readthedocs.io)**
HTTP 클라이언트. Document Parse 및 Groundedness Check REST API 호출.

### 디자인

**[Google Fonts](https://fonts.google.com)**
- [Bricolage Grotesque](https://fonts.google.com/specimen/Bricolage+Grotesque): 디스플레이 헤더
- [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono): 코드 및 모노스페이스 텍스트
- [Noto Sans KR](https://fonts.google.com/specimen/Noto+Sans+KR): 한글 본문

**커스텀 CSS**
[`static/style.css`](static/style.css)에 Brutalist-Editorial 디자인 시스템 구현. CSS 변수, 키프레임 애니메이션, 그라디언트 효과, 다크 테마 등 1,485줄.

## 프로젝트 구조

```
Oh_my_school_credit/
├── agents/
├── bootstrap/
├── data/
├── static/
├── univ_recruitment_guidelines/
├── utils/
├── .env.example
├── .gitignore
├── app.py
├── requirements.txt
└── README.md
```

### 주요 디렉토리

**[`agents/`](agents)**
AI 에이전트 모듈. `document_agent.py`는 PDF 파싱, `extract_agent.py`는 정보 추출, `recommend_agent.py`는 과목 추천, `verify_agent.py`는 검증 담당.

**[`data/`](data)**
JSON 데이터베이스. `subjects_2022.json`은 2022 개정 교육과정 과목 목록 (공통과목, 일반선택, 진로선택, 융합선택), `university_requirements_rag.json`은 대학별 권장과목 RAG 데이터베이스 (14개 학문 분야), `universities_list.json`은 대학 메타데이터 (티어, 위치, 설립 연도 등).

**[`static/`](static)**
정적 리소스. [`style.css`](static/style.css)에 다크 테마, 그라디언트 애니메이션, 커스텀 컴포넌트 스타일 정의.

**[`univ_recruitment_guidelines/`](univ_recruitment_guidelines)**
대학 입학전형 가이드 원본 PDF. 서울대, 연세대, 고려대 등 주요 대학의 모집단위별 권장과목 자료.

**[`utils/`](utils)**
유틸리티 모듈. `upstage_client.py`는 Upstage API 클라이언트, `neis_api.py`는 NEIS API 연동, `university_rag.py`는 대학 권장과목 검색, `schema.py`는 Pydantic 데이터 스키마.

### 루트 파일

**[`app.py`](app.py)**
메인 애플리케이션 (1,285줄). 5단계 워크플로우 구현:
1. Step 1: PDF 업로드 및 Document Parse
2. Step 2: 추출 정보 확인
3. Step 3: 학교/진로 설정 (NEIS API 검색)
4. Step 4: AI 맞춤 학점 설계 (Solar Pro 3 Reasoning)
5. Step 5: 추천 검증 (Groundedness Check)

클래스 기반 아키텍처로 각 단계별 렌더러(`Step1Upload`, `Step2Review`, `Step3Settings`, `Step4Recommend`, `Step5Verify`) 분리.

## 환경 설정

`.env` 파일 생성:

```env
UPSTAGE_API_KEY=your_upstage_api_key
NEIS_API_KEY=your_neis_api_key  # 선택사항
```

[Upstage Console](https://console.upstage.ai)에서 API 키 발급.
[NEIS 개방포털](https://open.neis.go.kr)에서 인증키 신청 (미설정 시 샘플 데이터 사용).

## 라이선스

GPL-3.0 license
