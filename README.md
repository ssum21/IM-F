# 🎓 내 학점, 내 길 (Oh_My_School_Credit)

> 생활기록부 기반 고교학점제 맞춤 과목 설계 AI Agent 서비스

## 📋 프로젝트 소개

**내 학점, 내 길**은 학생의 생활기록부를 AI가 분석하여 고교학점제에 최적화된 과목 조합을 추천해주는 서비스입니다.

### 핵심 기능

| 단계 | 기능 | 사용 기술 |
|------|------|----------|
| 1️⃣ | 생기부 PDF 업로드 | Upstage Document Parse |
| 2️⃣ | 정보 자동 추출 | Upstage Information Extract + Solar LLM |
| 3️⃣ | 학교/진로 설정 | **NEIS 교육정보 API** + **대학 권장과목 RAG** |
| 4️⃣ | 맞춤 학점 설계 | Solar Pro3 LLM + **RAG 기반 맞춤 추천** |
| 5️⃣ | 추천 검증 | Groundedness Check |

### 🏫 NEIS API 통합
- **학교 기본정보 조회**: 실제 학교명으로 검색 및 상세정보 확인
- **시간표 조회**: 학교별 실제 개설 과목 자동 추출
- **과목 분류**: 일반선택/진로선택/융합선택 자동 카테고리화

### 🎓 대학 입학전형 RAG 시스템
- **8개 주요 대학**: 서울대, 연세대, 고려대, 성균관대, 경희대, 중앙대, 건국대, 동국대
- **100개 이상 모집단위**: 대학별 전공 권장과목 데이터베이스
- **14개 학문 분야**: 수학, 컴퓨터, 물리, 기계, 전기전자, 화학, 의학, 약학 등
- **AI 맞춤 추천**: 대학 입학전형 기준 자동 반영

---

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd Oh_my_school_credit
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 Upstage API 키 입력
```

### 3. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속

---

## 📁 프로젝트 구조

```
Oh_my_school_credit/
├── app.py                      # Streamlit 메인 앱
├── agents/
│   ├── document_agent.py       # PDF 파싱 에이전트
│   ├── extract_agent.py        # 정보 추출 에이전트
│   ├── recommend_agent.py      # 과목 추천 에이전트
│   └── verify_agent.py         # 검증 에이전트
├── data/
│   ├── subjects_2022.json                    # 2022 개정 교육과정 과목
│   ├── university_requirements_rag.json      # 대학별 권장과목 RAG DB
│   ├── university_requirements_guide.md      # AI 참조용 상세 가이드
│   ├── universities_list.json                # 대학 목록 및 메타데이터
│   └── sample_school_courses.json            # 샘플 학교 과목
├── utils/
│   ├── upstage_client.py       # Upstage API 클라이언트
│   ├── schema.py               # 데이터 스키마
│   ├── neis_api.py             # 나이스 API 연동
│   └── university_rag.py       # 대학 권장과목 RAG 유틸리티
├── univ_recruitment_guidelines/  # 대학 입학전형 가이드 원본
│   ├── 2026 서울대권장과목.pdf
│   ├── 서울대_2028학년도 전공 연계 과목 선택 안내.pdf
│   ├── 경희대,고려대성균관대연세대중앙대_.pdf
│   └── ... (기타 PDF 파일들)
├── static/
│   └── style.css               # 커스텀 스타일
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 API 키 설정

`.env` 파일에 다음 키를 설정하세요:

```env
# Upstage API 키 (필수)
UPSTAGE_API_KEY=your_upstage_api_key

# NEIS 교육정보 API 키 (선택사항 - 실제 학교 데이터 조회용)
NEIS_API_KEY=your_neis_api_key
```

### API 키 발급 방법

1. **Upstage API**: https://console.upstage.ai
   - 회원가입 후 API 키 발급
   - Document Parse, Information Extract, Solar LLM 사용

2. **NEIS API**: https://open.neis.go.kr
   - 회원가입 후 인증키 신청
   - 학교 기본정보 및 시간표 API 사용
   - 미설정시 샘플 데이터로 동작

---

## 💡 사용 방법

### 데모 모드
PDF 파일 없이도 샘플 데이터로 서비스를 체험할 수 있습니다.

### 실제 사용
1. **생기부 업로드**: PDF 파일을 드래그앤드롭
2. **정보 확인**: AI가 추출한 정보 검토
3. **학교/진로 설정**: 목표 학교와 진로 선택
4. **추천 확인**: 3년간 192학점 과목 조합 확인
5. **검증**: 추천 근거 확인

---

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **AI/LLM**: Upstage Solar Pro3
- **Document AI**: Upstage Document Parse, Information Extract
- **External API**: NEIS 교육정보 API (학교/시간표 조회)
- **Language**: Python 3.9+
- **Data**: 2022 개정 교육과정

---

## 📊 고교학점제 규칙

- **총 이수 학점**: 192학점
- **공통과목**: 48학점 (1학년)
- **선택과목**: 144학점 (2~3학년)
- **학기당**: 25~34학점

---

## 📝 라이선스

MIT License

---

## 📚 추가 문서

- [NEIS API 통합 가이드](./NEIS_API_GUIDE.md) - 학교 정보 및 시간표 API
- [대학 입학전형 RAG 가이드](./UNIVERSITY_RAG_GUIDE.md) - 대학별 권장과목 데이터베이스

## 🧪 테스트

NEIS API 동작 테스트:
```bash
python3 test_neis_api.py
```

대학 권장과목 RAG 시스템 테스트:
```bash
python3 utils/university_rag.py
```

## 🙏 감사

- [Upstage](https://upstage.ai) - Solar API 제공
- [나이스 교육정보 개방포털](https://open.neis.go.kr) - 학교정보 API 제공
- 2022 개정 교육과정 기반 과목 데이터
