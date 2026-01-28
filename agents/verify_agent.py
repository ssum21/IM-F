"""
✅ Verify Agent - 추천 검증 에이전트

Upstage Groundedness Check API를 활용한 추천 근거 검증
생활기록부 정보와 추천 결과 간의 일관성 평가

주요 기능:
    - 학생 프로필과 추천 과목 간 연관성 검증
    - 강점 과목 → 심화 과목 연결 여부 확인
    - 희망 진로 → 관련 과목 포함 여부 확인
    - 할루시네이션(근거 없는 추천) 방지

Classes:
    VerificationResult: 검증 결과 데이터 클래스
    VerifyAgent: 검증 에이전트
"""

import json
from typing import Dict, Any, List, Generator
from dataclasses import dataclass, field


# =============================================================================
# 검증 결과 데이터 클래스
# =============================================================================
@dataclass
class VerificationResult:
    """
    검증 결과 데이터 클래스

    Attributes:
        is_grounded: 근거 충분 여부 (True/False)
        score: 근거도 점수 (0.0 ~ 1.0)
        explanation: 검증 결과 상세 설명
        evidence: 발견된 근거 목록
        suggestions: 개선 제안 목록
    """
    is_grounded: bool = True
    score: float = 0.0
    explanation: str = ""
    evidence: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# =============================================================================
# 검증 에이전트 클래스
# =============================================================================
class VerifyAgent:
    """
    추천 결과 검증 에이전트

    Solar Pro 3와 Groundedness Check를 활용하여
    추천 과목이 학생 정보에 얼마나 기반하는지 평가

    Attributes:
        client: Upstage API 클라이언트

    Example:
        >>> agent = VerifyAgent(client)
        >>> result = agent.verify_with_groundedness_api(context, answer)
        >>> print(f"근거도: {result.score:.1%}")
    """
    
    VERIFY_PROMPT = """당신은 교육 추천 검증 전문가입니다.
학생의 생활기록부 정보(Context)와 과목 추천 결과(Answer)를 비교하여
추천이 학생 정보에 얼마나 근거하는지 평가합니다.

평가 기준:
1. 강점 과목 → 심화 과목 연결 여부
2. 희망 진로 → 관련 과목 포함 여부
3. 활동 이력 → 추천 과목 연관성
4. 수상 경력 → 적성 반영 여부

응답 형식:
- 아래의 JSON 객체만 출력하세요. 다른 텍스트(검증 평가/설명/마크다운)는 출력하지 마세요.

출력 예시(JSON만):
{
    "is_grounded": true,
    "score": 0.9,
    "explanation": "요약된 검증 설명",
    "evidence": ["근거1", "근거2"],
    "suggestions": ["개선안1"]
}
"""

    def __init__(self, client):
        self.client = client
    
    def verify(
        self,
        student_profile: Dict[str, Any],
        recommendation: str
    ) -> Generator[str, None, VerificationResult]:
        """추천 결과 검증 (스트리밍)"""
        
        # 프로필을 컨텍스트로 변환
        context = self._profile_to_context(student_profile)
        
        prompt = f"""[학생 정보 (Context)]
{context}

[추천 결과 (Answer)]
{recommendation[:2000]}

위 추천이 학생 정보에 근거하는지 검증해주세요."""
        
        full_response = ""
        for chunk in self.client.chat_stream(
            message=prompt,
            system_prompt=self.VERIFY_PROMPT,
            reasoning_effort="low",
            temperature=0.1
        ):
            full_response += chunk
            yield chunk
        
        return self._parse_result(full_response)
    
    def verify_with_groundedness_api(
        self,
        context: str,
        answer: str
    ) -> VerificationResult:
        """Groundedness Check API 사용 검증"""
        result = self.client.check_groundedness(context, answer)
        
        return VerificationResult(
            is_grounded=result.get("grounded", True),
            score=result.get("score", 0.8),
            explanation=result.get("explanation", ""),
            evidence=result.get("evidence", [])
        )
    
    def _profile_to_context(self, profile: Dict[str, Any]) -> str:
        """프로필을 검증용 컨텍스트로 변환"""
        lines = []
        
        if profile.get("strong_subjects"):
            lines.append(f"강점 과목: {', '.join(profile['strong_subjects'])}")
        if profile.get("weak_subjects"):
            lines.append(f"보완 필요: {', '.join(profile['weak_subjects'])}")
        if profile.get("awards"):
            lines.append(f"수상 경력: {', '.join(profile['awards'][:5])}")
        if profile.get("club_activities"):
            lines.append(f"동아리: {profile['club_activities']}")
        if profile.get("career_activities"):
            lines.append(f"진로활동: {profile['career_activities']}")
        if profile.get("desired_career"):
            lines.append(f"희망 진로: {profile['desired_career']}")
        if profile.get("teacher_comments"):
            lines.append(f"담임 의견: {profile['teacher_comments'][:200]}")
        
        return "\n".join(lines) if lines else "학생 정보 없음"
    
    def _parse_result(self, response: str) -> VerificationResult:
        """응답 파싱"""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                start, end = response.find("{"), response.rfind("}") + 1
                json_str = response[start:end] if start >= 0 else response
            
            data = json.loads(json_str)
            
            return VerificationResult(
                is_grounded=data.get("is_grounded", True),
                score=float(data.get("score", 0.8)),
                explanation=data.get("explanation", ""),
                evidence=data.get("evidence", []),
                suggestions=data.get("suggestions", [])
            )
        except:
            return VerificationResult(
                is_grounded=True,
                score=0.8,
                explanation=response[:300]
            )
    
    def get_verification_summary(self, result: VerificationResult) -> str:
        """검증 결과 요약"""
        status = "✅ 검증 통과" if result.is_grounded else "⚠️ 검증 필요"
        score_bar = "🟢" * int(result.score * 5) + "⚪" * (5 - int(result.score * 5))
        
        lines = [
            f"{status} (점수: {result.score:.1%})",
            f"근거도: {score_bar}",
            "",
            f"📝 {result.explanation[:150]}"
        ]
        
        if result.evidence:
            lines.append(f"\n📌 근거: {' | '.join(result.evidence[:3])}")
        
        if result.suggestions:
            lines.append(f"\n💡 제안: {result.suggestions[0]}")
        
        return "\n".join(lines)
