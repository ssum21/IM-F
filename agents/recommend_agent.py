"""
🎯 Recommend Agent - 학점 설계 추천 에이전트

Upstage Solar Pro 3 Reasoning Mode를 활용한 맞춤형 과목 조합 추천
고교학점제 규정(192학점, 공통48+선택144)에 맞춘 최적 설계 제공

주요 기능:
    - 학생 프로필 기반 강점/진로 연계 과목 선정
    - 학교별 개설 과목 제약조건 반영
    - 대학별 권장 이수과목 데이터 참조
    - AI 추론 과정 실시간 스트리밍 시각화

Classes:
    CourseRecommendation: 추천 결과 데이터 클래스
    RecommendAgent: 추천 생성 에이전트
"""

import json
from typing import Dict, Any, List, Generator
from dataclasses import dataclass, field


# =============================================================================
# 추천 결과 데이터 클래스
# =============================================================================
@dataclass
class CourseRecommendation:
    """
    추천 과목 조합 결과 데이터 클래스

    Attributes:
        year1: 1학년 학기별 과목 (공통과목 중심)
        year2: 2학년 학기별 과목 (선택과목 시작)
        year3: 3학년 학기별 과목 (심화/진로 집중)
        total_credits: 총 설계 학점 (목표: 192학점)
        reasoning: 추천 근거 요약 텍스트
        highlights: 핵심 포인트 목록
        raw_response: LLM 원본 응답 (디버깅용)
    """
    year1: Dict[str, List[str]] = field(default_factory=dict)
    year2: Dict[str, List[str]] = field(default_factory=dict)
    year3: Dict[str, List[str]] = field(default_factory=dict)
    total_credits: int = 0
    reasoning: str = ""
    highlights: List[str] = field(default_factory=list)
    raw_response: str = ""


# =============================================================================
# 추천 에이전트 클래스
# =============================================================================
class RecommendAgent:
    """
    학점 설계 추천 에이전트

    Solar Pro 3의 Reasoning Mode를 활용하여
    학생 맞춤형 3개년 과목 조합을 추천

    Attributes:
        client: Upstage API 클라이언트
        subjects_data: 2022 개정 교육과정 과목 데이터
        univ_data: 대학별 권장 이수과목 데이터

    Example:
        >>> agent = RecommendAgent(client)
        >>> for chunk in agent.recommend(profile, courses, "서울대", "공학"):
        ...     print(chunk, end="")  # 실시간 추론 과정 출력
    """

    # 시스템 프롬프트 - RAG 정보 활용 강조
    SYSTEM_PROMPT = """당신은 한국 고교학점제 전문 상담사입니다.
학생의 프로필, 학교 개설 과목, 희망 진로를 바탕으로 3년간 최적의 과목 조합을 추천합니다.

[고교학점제 규칙]
- 총 192학점 (공통 48학점 + 선택 144학점)
- 학기당 25~34학점
- 교과영역별 균형 필요 (국어, 수학, 영어, 사회, 과학, 체육, 예술)

추천 시 고려사항:
1. **대학 입학전형 권장과목 최우선 반영** - 핵심 권장과목은 반드시 포함
2. 학생의 강점 과목을 심화
3. 희망 진로와 연계된 과목 선택
4. 학년별 난이도 순차 배치 (기본 → 일반선택 → 진로선택)
5. 과목 위계 준수 (예: 수학 → 수학I/II → 미적분I → 미적분II)

대학 권장과목 처리:
- 핵심 권장과목: 가능한 모두 포함 (학교 개설 여부 확인)
- 권장과목: 여유가 있으면 포함
- 학교 미개설 과목: highlights에 공동교육과정 이수 권장 명시

응답 형식:
- 아래의 JSON 객체만 출력하세요. 다른 텍스트(추론 과정/설명/마크다운)는 출력하지 마세요.

출력 예시(JSON만):
{
    "year1": {"1학기": ["과목1", "과목2"], "2학기": ["과목1"]},
    "year2": {"1학기": [], "2학기": []},
    "year3": {"1학기": [], "2학기": []},
    "total_credits": 192,
    "reasoning": "요약된 추천 이유",
    "highlights": ["핵심 포인트1", "핵심 포인트2", "공동교육과정 이수 권장: 과목명"]
}
"""

    def __init__(self, client):
        self.client = client
        self._load_data()
        self._init_rag()

    def _load_data(self):
        """과목 및 대학 데이터 로드"""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        try:
            with open(f"{base_path}/data/subjects_2022.json", "r", encoding="utf-8") as f:
                self.subjects_data = json.load(f)
        except:
            self.subjects_data = {}

        try:
            with open(f"{base_path}/data/university_requirements.json", "r", encoding="utf-8") as f:
                self.univ_data = json.load(f)
        except:
            self.univ_data = {}

    def _init_rag(self):
        """RAG 시스템 초기화"""
        try:
            from utils.university_rag import UniversityRAG
            self.rag = UniversityRAG()
        except Exception as e:
            print(f"RAG 시스템 초기화 실패: {e}")
            self.rag = None
    
    def recommend(
        self,
        student_profile: Dict[str, Any],
        school_courses: Dict[str, List[str]],
        target_university: str = "",
        target_major: str = ""
    ) -> Generator[str, None, CourseRecommendation]:
        """맞춤형 과목 조합 추천 (스트리밍)"""
        
        # 프롬프트 구성
        prompt = self._build_prompt(student_profile, school_courses, target_university, target_major)
        
        # Solar LLM 호출 (스트리밍)
        full_response = ""
        for chunk in self.client.chat_stream(
            message=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            reasoning_effort="low",
            temperature=0.3
        ):
            full_response += chunk
            yield chunk
        
        return self._parse_recommendation(full_response)
    
    def _build_prompt(
        self,
        profile: Dict[str, Any],
        courses: Dict[str, List[str]],
        univ: str,
        major: str
    ) -> str:
        """추천 요청 프롬프트 구성"""

        # 과목 리스트 전체 포함 (Truncation 제거)
        general_courses = courses.get('일반선택', [])
        career_courses = courses.get('진로선택', [])
        fusion_courses = courses.get('융합선택', [])

        prompt = f"""[학생 프로필]
- 강점 과목: {', '.join(profile.get('strong_subjects', []))}
- 보완 필요: {', '.join(profile.get('weak_subjects', []))}
- 동아리: {profile.get('club_activities', '정보 없음')}
- 수상: {', '.join(profile.get('awards', [])[:3])}
- 희망 진로: {profile.get('desired_career', major or '미정')}

[목표]
- 대학: {univ or '미정'}
- 계열/전공: {major or '미정'}

[학교 개설 과목]
- 일반선택: {', '.join(general_courses) if general_courses else '정보 없음'}
- 진로선택: {', '.join(career_courses) if career_courses else '정보 없음'}
- 융합선택: {', '.join(fusion_courses) if fusion_courses else '정보 없음'}
"""

        # RAG에서 대학별 권장과목 조회
        if self.rag and univ and univ != "선택 안함" and major and major != "선택 안함":
            try:
                # 전공별 권장과목 검색
                rec = self.rag.search_major_requirements(univ, major)

                if rec:
                    prompt += f"""
[{rec.university} {rec.major} 입학전형 권장과목]
※ 대학 입학전형에서 참고하는 권장과목입니다. 반드시 이수를 고려하세요.

"""
                    if rec.essential:
                        prompt += f"**핵심 권장과목 (필수적으로 이수):**\n"
                        prompt += f"  {', '.join(rec.essential)}\n\n"

                    if rec.recommended:
                        prompt += f"**권장과목 (가급적 이수):**\n"
                        prompt += f"  {', '.join(rec.recommended)}\n\n"

                    if rec.notes:
                        prompt += f"**참고사항:** {rec.notes}\n\n"

                # 학문 분야별 권장과목도 추가 (폴백)
                if not rec:
                    # 계열명으로 검색
                    field_mapping = {
                        "공학": "공학계열",
                        "자연과학": "자연계열",
                        "의예": "의약학계열",
                        "약학": "의약학계열"
                    }

                    if major in field_mapping:
                        field_info = self.rag.search_by_field(field_mapping[major])
                        if field_info:
                            prompt += f"""
[{major} 계열 일반 권장과목]
※ 주요 대학들의 공통 권장사항입니다.

"""
                            # 첫 번째 전공 분야의 정보 사용
                            first_major = next(iter(field_info.values())) if field_info else None
                            if first_major:
                                if "핵심수학" in first_major:
                                    prompt += f"**수학 핵심:** {', '.join(first_major['핵심수학'])}\n"
                                if "핵심과학" in first_major:
                                    prompt += f"**과학 핵심:** {', '.join(first_major['핵심과학'])}\n"
                                if "권장" in first_major:
                                    prompt += f"**추가 권장:** {', '.join(first_major['권장'])}\n"
                                prompt += "\n"

            except Exception as e:
                print(f"RAG 검색 오류: {e}")

        prompt += """
위 조건으로 3년간 192학점 과목 조합을 추천해주세요.
대학 권장과목을 최대한 반영하되, 학교 개설 과목 내에서 선택하세요.
반드시 [추론 과정]을 먼저 서술하고, JSON 데이터를 제공하세요."""

        return prompt
    
    def _parse_recommendation(self, response: str) -> CourseRecommendation:
        """LLM 응답 파싱"""
        try:
            # JSON 추출
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                start, end = response.find("{"), response.rfind("}") + 1
                json_str = response[start:end] if start >= 0 else response
            
            data = json.loads(json_str)
            
            return CourseRecommendation(
                year1=data.get("year1", {}),
                year2=data.get("year2", {}),
                year3=data.get("year3", {}),
                total_credits=data.get("total_credits", 192),
                reasoning=data.get("reasoning", ""),
                highlights=data.get("highlights", []),
                raw_response=response
            )
        except:
            return CourseRecommendation(raw_response=response, reasoning=response[:500])
    
    def get_summary(self, rec: CourseRecommendation) -> str:
        """추천 결과 요약"""
        lines = [f"📊 총 {rec.total_credits}학점 설계 완료", ""]
        
        for year, label in [(rec.year1, "1학년"), (rec.year2, "2학년"), (rec.year3, "3학년")]:
            if year:
                subjects = []
                for sem in year.values():
                    subjects.extend(sem if isinstance(sem, list) else [])
                if subjects:
                    lines.append(f"📚 {label}: {', '.join(subjects[:5])}...")
        
        if rec.highlights:
            lines.append(f"\n✨ 핵심: {' | '.join(rec.highlights[:3])}")
        
        return "\n".join(lines)
