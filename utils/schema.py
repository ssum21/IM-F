"""
📚 생활기록부 정보 추출 스키마

Upstage Information Extract API를 위한 데이터 모델 정의
Pydantic을 사용하여 타입 안전성과 데이터 검증 제공

Classes:
    - SubjectRecord: 개별 과목 성적 정보
    - AcademicRecord: 전체 학업 성적 정보
    - CreativeActivities: 창의적 체험활동 정보
    - Activities: 수상 및 활동 정보
    - CareerAspiration: 진로 희망 정보
    - StudentInfo: 학생 기본 정보
    - StudentRecord: 생활기록부 전체 구조
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SubjectRecord(BaseModel):
    """
    개별 과목 성적 정보
    
    Attributes:
        subject_name: 과목명
        achievement_level: 성취도 (A/B/C/D/E)
        raw_score: 원점수
        rank: 석차등급
    """
    subject_name: str = Field(description="과목명")
    achievement_level: Optional[str] = Field(default=None, description="성취도 (A/B/C/D/E)")
    raw_score: Optional[float] = Field(default=None, description="원점수")
    rank: Optional[str] = Field(default=None, description="석차등급")


class AcademicRecord(BaseModel):
    """
    전체 학업 성적 정보
    
    Attributes:
        subjects: 과목별 성적 목록
        strong_subjects: 강점 과목 목록
        weak_subjects: 약점 과목 목록
    """
    subjects: List[SubjectRecord] = Field(default_factory=list, description="과목별 성적 목록")
    strong_subjects: List[str] = Field(default_factory=list, description="강점 과목 목록")
    weak_subjects: List[str] = Field(default_factory=list, description="약점 과목 목록")


class CreativeActivities(BaseModel):
    """
    창의적 체험활동 정보 (자율/동아리/봉사/진로)
    
    Attributes:
        autonomous: 자율활동 내용
        club: 동아리활동 내용
        volunteer: 봉사활동 내용
        career: 진로활동 내용
    """
    autonomous: Optional[str] = Field(default=None, description="자율활동 내용")
    club: Optional[str] = Field(default=None, description="동아리활동 내용")
    volunteer: Optional[str] = Field(default=None, description="봉사활동 내용")
    career: Optional[str] = Field(default=None, description="진로활동 내용")


class Activities(BaseModel):
    """
    수상 및 활동 정보
    
    Attributes:
        awards: 수상 경력 목록
        creative_activities: 창의적 체험활동 정보
    """
    awards: List[str] = Field(default_factory=list, description="수상 경력 목록")
    creative_activities: CreativeActivities = Field(
        default_factory=CreativeActivities, 
        description="창의적 체험활동 정보"
    )


class CareerAspiration(BaseModel):
    """
    진로 희망 정보
    
    Attributes:
        desired_field: 희망 진로 분야
        reason: 진로 선택 이유
    """
    desired_field: Optional[str] = Field(default=None, description="희망 진로 분야")
    reason: Optional[str] = Field(default=None, description="진로 선택 이유")


class StudentInfo(BaseModel):
    """
    학생 기본 정보
    
    Attributes:
        name: 학생 이름
        school_type: 학교 유형 (초등학교/중학교/고등학교)
        grade: 학년
    """
    name: Optional[str] = Field(default=None, description="학생 이름")
    school_type: Optional[str] = Field(default=None, description="학교 유형")
    grade: Optional[int] = Field(default=None, description="학년")


class StudentRecord(BaseModel):
    """
    생활기록부 전체 구조
    
    생활기록부 PDF에서 추출한 모든 정보를 담는 최상위 모델
    
    Attributes:
        student_info: 학생 기본 정보
        academic_record: 학업 성적 정보
        activities: 수상 및 활동 정보
        career_aspiration: 진로 희망 정보
        teacher_comments: 담임 선생님 종합 의견
    """
    student_info: StudentInfo = Field(
        default_factory=StudentInfo, 
        description="학생 기본 정보"
    )
    academic_record: AcademicRecord = Field(
        default_factory=AcademicRecord, 
        description="학업 성적 정보"
    )
    activities: Activities = Field(
        default_factory=Activities, 
        description="수상 및 활동 정보"
    )
    career_aspiration: CareerAspiration = Field(
        default_factory=CareerAspiration, 
        description="진로 희망 정보"
    )
    teacher_comments: Optional[str] = Field(
        default=None, 
        description="담임 선생님 종합 의견"
    )
    
    def get_extraction_schema(self) -> dict:
        """
        Upstage Information Extract API용 JSON 스키마 반환
        
        Returns:
            dict: API 호출에 사용할 JSON 스키마
        """
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "student_record_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "student_info": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "학생 이름"},
                                "school_type": {"type": "string", "description": "학교 유형 (초등학교/중학교/고등학교)"},
                                "grade": {"type": "integer", "description": "학년"}
                            }
                        },
                        "academic_record": {
                            "type": "object",
                            "properties": {
                                "subjects": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "subject_name": {"type": "string", "description": "과목명"},
                                            "achievement_level": {"type": "string", "description": "성취도 (A/B/C/D/E)"},
                                            "raw_score": {"type": "number", "description": "원점수"},
                                            "rank": {"type": "string", "description": "석차등급"}
                                        }
                                    },
                                    "description": "과목별 성적 목록"
                                },
                                "strong_subjects": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "강점 과목 목록 (성취도 A 또는 상위권)"
                                },
                                "weak_subjects": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "약점 과목 목록 (성취도 D/E 또는 하위권)"
                                }
                            }
                        },
                        "activities": {
                            "type": "object",
                            "properties": {
                                "awards": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "수상 경력 목록"
                                },
                                "creative_activities": {
                                    "type": "object",
                                    "properties": {
                                        "autonomous": {"type": "string", "description": "자율활동 내용"},
                                        "club": {"type": "string", "description": "동아리활동 내용"},
                                        "volunteer": {"type": "string", "description": "봉사활동 내용"},
                                        "career": {"type": "string", "description": "진로활동 내용"}
                                    }
                                }
                            }
                        },
                        "career_aspiration": {
                            "type": "object",
                            "properties": {
                                "desired_field": {"type": "string", "description": "희망 진로 분야"},
                                "reason": {"type": "string", "description": "진로 선택 이유"}
                            }
                        },
                        "teacher_comments": {"type": "string", "description": "담임 선생님 종합 의견"}
                    }
                }
            }
        }


# Information Extract API 호출 시 사용할 간소화된 스키마 (직접 사용)
EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "student_record",
        "schema": {
            "type": "object",
            "properties": {
                "student_name": {"type": "string", "description": "학생 이름"},
                "school_type": {"type": "string", "description": "학교 유형 (초등학교/중학교/고등학교)"},
                "grade": {"type": "integer", "description": "학년"},
                "strong_subjects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "성적 우수 과목 목록"
                },
                "weak_subjects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "성적 부진 과목 목록"
                },
                "awards": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "수상 경력"
                },
                "club_activities": {"type": "string", "description": "동아리 활동 내용"},
                "career_activities": {"type": "string", "description": "진로 활동 내용"},
                "desired_career": {"type": "string", "description": "희망 진로"},
                "teacher_comments": {"type": "string", "description": "담임 종합 의견"}
            }
        }
    }
}
