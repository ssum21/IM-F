"""
📊 Extract Agent - 정보 추출 에이전트

Solar Pro 3를 활용한 생활기록부 텍스트 구조화 정보 추출
Document Parse 결과를 분석하여 학생 프로필 생성

주요 추출 항목:
    - 학생 기본 정보 (이름, 학교, 학년)
    - 강점/약점 과목 분석
    - 수상 경력 및 활동 이력
    - 희망 진로 및 담임 종합 의견

Classes:
    ExtractedInfo: 추출된 학생 정보 데이터 클래스
    ExtractAgent: 정보 추출 에이전트
"""

import json
from typing import Dict, Any, List, Generator
from dataclasses import dataclass, field


# =============================================================================
# 추출 결과 데이터 클래스
# =============================================================================
@dataclass
class ExtractedInfo:
    """
    추출된 학생 정보 데이터 클래스

    생활기록부에서 추출한 구조화된 학생 프로필 정보

    Attributes:
        student_name: 학생 이름
        school_name: 학교명 (예: 서울과학고등학교)
        school_type: 학교 유형 (초등학교/중학교/고등학교)
        grade: 현재 학년
        strong_subjects: 강점 과목 목록 (성적 우수)
        weak_subjects: 보완 필요 과목 목록
        awards: 수상 경력 목록
        club_activities: 동아리 활동 내용
        career_activities: 진로 활동 내용
        desired_career: 희망 진로/직업
        teacher_comments: 담임 선생님 종합 의견
        raw_data: LLM 응답 원본 데이터 (디버깅용)
    """
    student_name: str = ""
    school_name: str = ""
    school_type: str = ""
    grade: int = 0
    strong_subjects: List[str] = field(default_factory=list)
    weak_subjects: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    club_activities: str = ""
    career_activities: str = ""
    desired_career: str = ""
    teacher_comments: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 추출 에이전트 클래스
# =============================================================================
class ExtractAgent:
    """
    생활기록부 정보 추출 에이전트

    Solar Pro 3를 사용하여 생활기록부 텍스트에서
    구조화된 학생 정보를 JSON 형태로 추출

    Attributes:
        client: Upstage API 클라이언트
        EXTRACTION_PROMPT: 정보 추출용 시스템 프롬프트

    Example:
        >>> agent = ExtractAgent(client)
        >>> for chunk in agent.extract_from_text(text):
        ...     print(chunk, end="")  # 실시간 추출 과정 출력
    """
    
    EXTRACTION_PROMPT = """당신은 한국 학교 생활기록부 분석 전문가입니다.
주어진 텍스트에서 다음 정보를 JSON 형식으로 추출하세요:

{
    "student_name": "이름",
    "school_name": "학교명 (예: 서울과학고등학교)",
    "school_type": "초등학교/중학교/고등학교",
    "grade": 학년(숫자),
    "strong_subjects": ["강점과목1", "강점과목2"],
    "weak_subjects": ["약점과목1"],
    "awards": ["수상1", "수상2"],
    "club_activities": "동아리 활동",
    "career_activities": "진로 활동",
    "desired_career": "희망 진로",
    "teacher_comments": "담임 의견 요약"
}

주의사항:
- school_name은 생활기록부 상단에 표시된 학교명을 정확히 추출하세요
- "OO고등학교", "OO중학교" 형태로 추출하세요"""
    
    def __init__(self, client):
        """에이전트 초기화"""
        self.client = client
    
    def extract_from_text(self, text: str) -> Generator[str, None, ExtractedInfo]:
        """텍스트에서 생활기록부 정보 추출 (스트리밍)"""
        user_message = f"다음 생활기록부에서 정보를 추출하세요:\n\n{text[:6000]}"
        
        full_response = ""
        for chunk in self.client.chat_stream(
            message=user_message,
            system_prompt=self.EXTRACTION_PROMPT,
            reasoning_effort="low",
            temperature=0.1
        ):
            full_response += chunk
            yield chunk
        
        return self._parse_response(full_response)
    
    def _parse_response(self, response: str) -> ExtractedInfo:
        """LLM 응답을 ExtractedInfo로 변환"""
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
            
            return ExtractedInfo(
                student_name=data.get("student_name", ""),
                school_name=data.get("school_name", ""),
                school_type=data.get("school_type", ""),
                grade=int(data.get("grade", 0)) if data.get("grade") else 0,
                strong_subjects=data.get("strong_subjects", []),
                weak_subjects=data.get("weak_subjects", []),
                awards=data.get("awards", []),
                club_activities=data.get("club_activities", ""),
                career_activities=data.get("career_activities", ""),
                desired_career=data.get("desired_career", ""),
                teacher_comments=data.get("teacher_comments", ""),
                raw_data=data
            )
        except (json.JSONDecodeError, ValueError) as e:
            return ExtractedInfo(raw_data={"error": str(e)})
    
    def get_profile_summary(self, info: ExtractedInfo) -> str:
        """추출된 정보의 프로필 요약 생성"""
        parts = []
        if info.student_name:
            parts.append(f"👤 학생: {info.student_name}")
        if info.school_name:
            parts.append(f"🏫 학교: {info.school_name}")
        elif info.school_type:
            parts.append(f"🏫 {info.school_type} {info.grade}학년")
        if info.grade and not info.school_name:
            parts.append(f"📖 {info.grade}학년")
        if info.strong_subjects:
            parts.append(f"💪 강점: {', '.join(info.strong_subjects)}")
        if info.weak_subjects:
            parts.append(f"📚 보완: {', '.join(info.weak_subjects)}")
        if info.awards:
            parts.append(f"🏆 수상: {', '.join(info.awards[:3])}")
        if info.desired_career:
            parts.append(f"💼 희망: {info.desired_career}")
        return "\n".join(parts) if parts else "추출된 정보 없음"
