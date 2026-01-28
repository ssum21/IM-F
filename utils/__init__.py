"""
🎓 내 학점, 내 길 - 유틸리티 모듈

공통 유틸리티 및 API 클라이언트 모듈

Modules:
    - upstage_client: Upstage API 통합 클라이언트
    - schema: 생활기록부 정보 추출 스키마
    - neis_api: 나이스 교육정보 API 연동
"""

from .upstage_client import UpstageClient
from .schema import StudentRecord, AcademicRecord, Activities, CareerAspiration

__all__ = [
    "UpstageClient",
    "StudentRecord",
    "AcademicRecord", 
    "Activities",
    "CareerAspiration"
]
