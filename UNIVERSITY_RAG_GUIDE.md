# 🎓 대학 입학전형 권장과목 RAG 시스템

## 개요

이 시스템은 주요 대학들의 **입학전형 교과이수 권장과목** 정보를 구조화하여 AI가 학생에게 맞춤형 과목 추천을 할 수 있도록 지원합니다.

## 📁 파일 구조

```
Oh_my_school_credit/
├── data/
│   ├── university_requirements_rag.json    # 대학별 권장과목 데이터베이스
│   ├── universities_list.json              # 대학 목록 및 메타데이터
│   └── university_requirements_guide.md    # AI 참조용 상세 가이드
├── utils/
│   └── university_rag.py                    # RAG 유틸리티 클래스
└── univ_recruitment_guidelines/
    ├── 2026 서울대권장과목.pdf
    ├── 서울대_2028학년도 전공 연계 과목 선택 안내.pdf
    ├── 경희대,고려대성균관대연세대중앙대_.pdf
    └── ... (기타 PDF 파일들)
```

## 📊 데이터 구조

### 1. university_requirements_rag.json

전체 데이터베이스의 핵심 파일입니다.

**주요 섹션:**
- `metadata`: 데이터 버전, 출처, 커버리지 정보
- `universities`: 대학별 상세 권장과목 데이터
- `subject_categories`: 2022 개정 교육과정 과목 체계
- `major_field_mapping`: 전공 분야별 권장과목 매핑
- `evaluation_criteria`: 학생부종합전형 평가 기준
- `tips_and_guidance`: 과목 선택 전략 및 팁

**데이터 계층:**
```
universities
└── 서울대학교
    ├── 2026학년도
    │   ├── 인문계열
    │   └── 자연계열
    │       ├── 자연과학대학
    │       ├── 공과대학
    │       ├── 의과대학
    │       └── ...
    └── 2028학년도
        ├── 유형1_인문계열
        ├── 유형2_자연계열
        └── 유형3_예체능
```

### 2. universities_list.json

대학 목록 및 메타데이터입니다.

```json
{
  "universities": [
    {
      "id": "snu",
      "name": "서울대학교",
      "tier": "SKY",
      "region": "서울",
      "has_requirements": true,
      "years": ["2026", "2028"]
    }
  ],
  "tiers": {
    "SKY": ["서울대학교", "연세대학교", "고려대학교"]
  }
}
```

### 3. university_requirements_guide.md

AI가 참조할 수 있는 **자연어 형태의 상세 가이드**입니다.

**주요 내용:**
- 핵심 원칙 및 용어 정의
- 대학별 상세 권장과목
- 전공별 추천 이수 경로
- AI 추천시 주의사항
- 검색 키워드 (RAG용)
- AI 응답 예시

## 🔧 사용 방법

### Python 코드에서 사용

```python
from utils.university_rag import UniversityRAG

# RAG 시스템 초기화
rag = UniversityRAG()

# 1. 전공별 권장과목 검색
rec = rag.search_major_requirements(
    university="서울대학교",
    major="기계공학부",
    year="2026"
)

if rec:
    print(f"핵심 권장과목: {rec.essential}")
    print(f"권장과목: {rec.recommended}")

    # 포맷팅된 출력
    print(rag.format_recommendation(rec))

# 2. 학문 분야별 검색
field_info = rag.search_by_field("공학계열")
print(field_info["기계공학"])

# 3. 과목 위계 조회
hierarchy = rag.get_course_progression("수학")
print(hierarchy)

# 4. 평가 기준 조회
criteria = rag.get_evaluation_criteria()
print(criteria["학생부종합전형"])

# 5. 과목 선택 팁
tips = rag.get_tips_and_guidance()
print(tips["과목선택_전략"])
```

### AI Agent에서 활용

```python
from utils.university_rag import UniversityRAG

class RecommendAgent:
    def __init__(self):
        self.rag = UniversityRAG()

    def recommend_subjects(self, student_info: dict) -> str:
        """
        학생 정보 기반 과목 추천

        Args:
            student_info: {
                "target_university": "서울대학교",
                "target_major": "기계공학부",
                "current_grade": 2,
                "completed_subjects": ["수학I", "수학II", "물리학"]
            }
        """
        # 1. 권장과목 조회
        rec = self.rag.search_major_requirements(
            university=student_info["target_university"],
            major=student_info["target_major"]
        )

        if not rec:
            return "해당 전공의 권장과목 정보를 찾을 수 없습니다."

        # 2. 이미 이수한 과목 제외
        completed = set(student_info["completed_subjects"])
        remaining_essential = [s for s in rec.essential if s not in completed]
        remaining_recommended = [s for s in rec.recommended if s not in completed]

        # 3. 학년별 추천
        grade = student_info["current_grade"]

        response = f"## {rec.university} {rec.major} 권장과목\n\n"

        if remaining_essential:
            response += "### 앞으로 이수해야 할 핵심 과목\n"
            for subject in remaining_essential:
                response += f"- {subject}\n"

        if remaining_recommended:
            response += "\n### 추가 권장 과목\n"
            for subject in remaining_recommended:
                response += f"- {subject}\n"

        # 4. 과목 위계 고려한 조언
        hierarchy = self.rag.get_course_progression("수학")
        response += f"\n### 과목 이수 순서\n"
        response += f"수학 과목은 다음 순서로 이수하세요:\n"
        for level, desc in hierarchy.items():
            response += f"- {desc}\n"

        return response
```

## 🎯 RAG 검색 전략

### 키워드 기반 검색

**대학명:**
- `서울대`, `SKY`, `주요대학`
- `연세대`, `고려대`, `성균관대`, `경희대`, `중앙대`

**전공명:**
- `기계공학`, `전기전자`, `컴퓨터`
- `의예과`, `약학`, `간호`
- `물리학`, `화학`, `생명과학`

**과목명:**
- `미적분`, `기하`, `확률과통계`
- `물리학I`, `화학II`, `생명과학II`
- `역학과에너지`, `세포와물질대사`

### 시맨틱 검색 예시

```python
def semantic_search(query: str) -> list:
    """
    의미 기반 검색

    예시:
    - "의대 가려면 어떤 과목?" → 의학 분야 권장과목
    - "컴퓨터 전공 수학 과목" → 컴퓨터공학 수학 핵심과목
    - "기계공학 필수 과목" → 기계공학 핵심 권장과목
    """
    rag = UniversityRAG()

    # 키워드 추출
    if "의대" in query or "의학" in query:
        return rag.search_by_field("의약학계열")["의학"]
    elif "컴퓨터" in query:
        return rag.search_by_field("공학계열")["컴퓨터공학"]
    elif "기계" in query:
        return rag.search_by_field("공학계열")["기계공학"]

    # ... 추가 패턴 매칭
```

## 📖 데이터 활용 가이드

### 1. 학생 맞춤형 추천

```python
# 학생 상황 고려
if not school_offers_subject:
    advice = "학교에서 개설하지 않은 과목은 불이익이 없습니다."
    advice += "가능하다면 공동교육과정을 통해 이수하는 것을 권장합니다."
else:
    advice = "해당 과목은 희망 전공에 중요한 과목입니다."
    advice += "가급적 이수하시는 것을 추천드립니다."
```

### 2. 과목 위계 검증

```python
def validate_course_sequence(subjects: list) -> bool:
    """
    과목 이수 순서가 올바른지 검증

    예: 미적분II를 듣기 전에 미적분I을 들었는지 확인
    """
    rag = UniversityRAG()
    hierarchy = rag.get_course_progression("수학")

    # 위계 검증 로직
    if "미적분II" in subjects and "미적분I" not in subjects:
        return False

    return True
```

### 3. 전공 미정 학생 대응

```python
def recommend_for_undecided(interests: list) -> dict:
    """
    진로 미정 학생을 위한 폭넓은 추천

    Args:
        interests: ["자연과학", "공학"] 등 관심 분야
    """
    rag = UniversityRAG()

    # 공통 과목 추천
    common = {
        "수학": ["수학I", "수학II", "미적분I"],
        "과학": ["물리학", "화학", "생명과학"]
    }

    return common
```

## 🔍 검색 최적화

### 인덱싱 전략

1. **대학명 인덱스**: 빠른 대학 검색
2. **전공명 인덱스**: 학과/모집단위 매칭
3. **과목명 인덱스**: 과목 기반 역검색
4. **학문분야 인덱스**: 카테고리별 검색

### 캐싱 전략

```python
from functools import lru_cache

class UniversityRAG:
    @lru_cache(maxsize=128)
    def search_major_requirements(self, university, major, year):
        # 자주 검색되는 결과 캐싱
        ...
```

## 📝 데이터 업데이트 방법

### 1. 새 대학 추가

`data/university_requirements_rag.json`에 추가:

```json
{
  "universities": {
    "새대학교": {
      "2026학년도": {
        "자연계열": {
          "컴퓨터공학과": {
            "핵심권장과목": ["수학I", "수학II", "미적분"],
            "권장과목": ["확률과 통계"]
          }
        }
      }
    }
  }
}
```

### 2. 새 학년도 추가

기존 대학 아래에 새 학년도 섹션 추가:

```json
{
  "서울대학교": {
    "2030학년도": {
      ...
    }
  }
}
```

### 3. 가이드 문서 업데이트

`data/university_requirements_guide.md` 수정 후, AI가 참조할 수 있도록 RAG 시스템 재로드

## 🧪 테스트

```bash
# RAG 시스템 테스트
python3 utils/university_rag.py

# 예상 출력:
# ============================================================
# 대학 입학전형 권장과목 RAG 시스템 테스트
# ============================================================
#
# [1] 대학 목록
# - 서울대학교 (SKY)
# - 연세대학교 (SKY)
# ...
```

## 💡 활용 사례

### 사례 1: 진로 탐색 단계 (1학년)

```python
# 학생이 관심 분야만 정한 상태
interests = ["공학", "과학"]

# 폭넓은 기초 과목 추천
tips = rag.get_tips_and_guidance()
grade1_rec = tips["과목선택_전략"]["1학년"]
# → 공통과목 충실히, 기초를 탄탄히
```

### 사례 2: 전공 확정 단계 (2학년)

```python
# 서울대 기계공학부 희망
rec = rag.search_major_requirements("서울대학교", "기계공학부")

# 핵심: 물리학Ⅱ, 미적분, 기하
# 권장: 확률과 통계
# → 2학년: 물리학, 미적분I 이수
# → 3학년: 물리학Ⅱ, 미적분II, 기하 계획
```

### 사례 3: 복수 지망 (SKY 공대)

```python
# 서울대/연세대/고려대 모두 고려
snu_rec = rag.search_major_requirements("서울대", "전기정보공학부")
five_rec = rag.search_major_requirements("고려대", "전기전자공학부")

# 공통 핵심과목 추출
common = set(snu_rec.essential) & set(five_rec.essential)
# → 미적분, 기하, 물리학Ⅱ 우선 이수
```

## 🚀 향후 개선 방향

1. **벡터 임베딩**: 시맨틱 검색 정확도 향상
2. **그래프 DB**: 과목 간 선수관계 모델링
3. **실시간 업데이트**: 대학 홈페이지 크롤링
4. **학습 추천**: 학습 경로 최적화 알고리즘
5. **다국어 지원**: 영문 전공명 매칭

## 📚 참고 자료

- [서울대학교 입학본부](https://admission.snu.ac.kr)
- [NEIS 교육정보 개방포털](https://open.neis.go.kr)
- [2022 개정 교육과정 총론](https://www.moe.go.kr)
- 경희대/고려대/성균관대/연세대/중앙대 공동연구 보고서 (2022)

---

**제작**: I'MF (아이엠에프) - 고교학점제 맞춤 과목 설계 AI Agent 서비스
**업데이트**: 2026-01-28
