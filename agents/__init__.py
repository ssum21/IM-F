"""
🎓 I'MF (아이엠에프) - AI Agent 모듈

Upstage API 기반 고교학점제 맞춤 설계 AI Agent 파이프라인
End-to-End 자동화: PDF 업로드 → 정보 추출 → 추천 생성 → 검증

=============================================================================
Agent 파이프라인 구조
=============================================================================

    [PDF 업로드]
         │
         ▼
    ┌────────────────┐
    │ DocumentAgent  │  ← Upstage Document Parse API
    │ PDF → 텍스트   │     OCR 및 구조화 텍스트 추출
    └────────────────┘
         │
         ▼
    ┌────────────────┐
    │ ExtractAgent   │  ← Upstage Solar Pro 3
    │ 텍스트 → JSON  │     구조화된 학생 정보 추출
    └────────────────┘
         │
         ▼
    ┌────────────────┐
    │ RecommendAgent │  ← Upstage Solar Pro 3 (Reasoning Mode)
    │ 맞춤 과목 추천 │     192학점 최적 설계
    └────────────────┘
         │
         ▼
    ┌────────────────┐
    │ VerifyAgent    │  ← Upstage Groundedness Check
    │ 추천 근거 검증 │     할루시네이션 방지
    └────────────────┘

=============================================================================
"""

from .document_agent import DocumentAgent, ParsedDocument
from .extract_agent import ExtractAgent, ExtractedInfo
from .recommend_agent import RecommendAgent, CourseRecommendation
from .verify_agent import VerifyAgent, VerificationResult

__all__ = [
    # Agent 클래스
    "DocumentAgent",
    "ExtractAgent",
    "RecommendAgent",
    "VerifyAgent",
    # 데이터 클래스
    "ParsedDocument",
    "ExtractedInfo",
    "CourseRecommendation",
    "VerificationResult"
]
