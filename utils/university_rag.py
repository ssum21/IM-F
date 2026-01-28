"""
🎓 대학 입학전형 권장과목 RAG 유틸리티

대학별 모집단위 교과이수 권장과목 데이터를 조회하고
AI가 학생에게 맞춤형 과목 추천을 할 수 있도록 지원합니다.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SubjectRecommendation:
    """과목 추천 결과"""
    essential: List[str]  # 핵심 권장과목
    recommended: List[str]  # 권장과목
    category: str  # 학문 분야
    university: str  # 대학명
    major: str  # 모집단위/학과
    notes: str = ""  # 특이사항


class UniversityRAG:
    """
    대학 입학전형 권장과목 RAG 클래스

    JSON 데이터베이스를 로드하고 검색 기능을 제공합니다.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        초기화

        Args:
            data_dir: 데이터 디렉토리 경로 (기본값: 현재 파일 기준 ../data)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"

        self.data_dir = Path(data_dir)
        self.requirements = self._load_json("university_requirements_rag.json")
        self.universities = self._load_json("universities_list.json")

    def _load_json(self, filename: str) -> Dict:
        """JSON 파일 로드"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_universities_list(self) -> List[Dict]:
        """대학 목록 조회"""
        return self.universities.get("universities", [])

    def get_university_by_name(self, university_name: str) -> Optional[Dict]:
        """대학명으로 대학 정보 조회"""
        for univ in self.get_universities_list():
            if university_name in univ["name"]:
                return univ
        return None

    def search_major_requirements(
        self,
        university: str,
        major: str,
        year: str = "2026"
    ) -> Optional[SubjectRecommendation]:
        """
        전공별 권장과목 검색

        Args:
            university: 대학명 (예: "서울대학교")
            major: 전공/학과명 (예: "기계공학부")
            year: 학년도 (기본값: "2026")

        Returns:
            SubjectRecommendation 또는 None
        """
        # 서울대학교 2026학년도 예시
        if "서울대" in university and year == "2026":
            return self._search_snu_2026(major)
        elif "서울대" in university and year == "2028":
            return self._search_snu_2028(major)

        # 5개 대학 공동연구 (경희대/고려대/성균관대/연세대/중앙대)
        if any(u in university for u in ["경희대", "고려대", "성균관대", "연세대", "중앙대"]):
            return self._search_five_universities(major)

        return None

    def _search_snu_2026(self, major: str) -> Optional[SubjectRecommendation]:
        """서울대 2026학년도 검색"""
        data = self.requirements.get("universities", {}).get("서울대학교", {}).get("2026학년도", {})

        # 자연계열 검색
        natural = data.get("자연계열", {})
        for college, departments in natural.items():
            if isinstance(departments, dict):
                # 학과별 검색
                for dept_name, dept_info in departments.items():
                    if major in dept_name:
                        return SubjectRecommendation(
                            essential=dept_info.get("핵심권장과목", []),
                            recommended=dept_info.get("권장과목", []),
                            category="자연계열",
                            university="서울대학교",
                            major=dept_name,
                            notes=dept_info.get("비고", "")
                        )

        return None

    def _search_snu_2028(self, major: str) -> Optional[SubjectRecommendation]:
        """서울대 2028학년도 검색 (2022 개정 교육과정)"""
        data = self.requirements.get("universities", {}).get("서울대학교", {}).get("2028학년도", {})

        # 유형2 자연계열
        type2 = data.get("유형2_자연계열", {})

        # 공통 요구사항
        common = type2.get("공통요구사항", {})
        essential_math = common.get("수학", {}).get("핵심", [])
        essential_science_desc = common.get("과학", {}).get("진로선택", "")

        # 모집단위별 일반선택 우선이수 과목
        priority = type2.get("모집단위별_일반선택_우선이수", {})

        for category, info in priority.items():
            if major in str(info.get("모집단위", [])):
                subject = info.get("과목", "")
                return SubjectRecommendation(
                    essential=essential_math + [f"{subject} (일반선택 우선)"],
                    recommended=[essential_science_desc],
                    category="자연계열",
                    university="서울대학교 (2028)",
                    major=major,
                    notes="2022 개정 교육과정 기준"
                )

        # 기본 자연계열
        return SubjectRecommendation(
            essential=essential_math,
            recommended=[essential_science_desc],
            category="자연계열",
            university="서울대학교 (2028)",
            major=major,
            notes="2022 개정 교육과정 기준"
        )

    def _search_five_universities(self, major: str) -> Optional[SubjectRecommendation]:
        """5개 대학 공동연구 검색"""
        data = self.requirements.get("universities", {}).get("경희대_고려대_성균관대_연세대_중앙대", {})
        research = data.get("2022_공동연구", {}).get("학문분야", {})

        # 학문분야별 검색
        field_keywords = {
            "수학": ["수학과", "수학교육", "응용수학", "통계"],
            "컴퓨터": ["컴퓨터", "소프트웨어", "AI", "인공지능", "정보보안", "데이터"],
            "산업": ["산업공학", "산업경영"],
            "물리": ["물리학"],
            "기계": ["기계공학"],
            "전기전자": ["전기", "전자", "반도체"],
            "건설건축": ["건축", "건설", "토목", "도시"],
            "화학": ["화학과", "화학교육"],
            "재료_화공_고분자_에너지": ["재료", "화공", "고분자", "에너지", "신소재"],
            "생명과학_환경_생활과학_농림": ["생명과학", "생물", "환경", "식품", "농", "생활과학"],
            "천문_지구": ["천문", "지구", "우주"],
            "의학": ["의예", "의학", "한의"],
            "약학": ["약학", "약과학"],
            "간호_보건": ["간호", "보건"]
        }

        for field, keywords in field_keywords.items():
            if any(keyword in major for keyword in keywords):
                field_data = research.get(field, {})

                essential_subjects = []
                recommended_subjects = []

                # 핵심과목
                if "핵심과목" in field_data:
                    for category, subjects in field_data["핵심과목"].items():
                        essential_subjects.extend(subjects)

                # 권장과목
                if "권장과목" in field_data:
                    for category, subjects in field_data["권장과목"].items():
                        recommended_subjects.extend(subjects)

                return SubjectRecommendation(
                    essential=essential_subjects,
                    recommended=recommended_subjects,
                    category=field.replace("_", "/"),
                    university="5개 대학 공동 (경희대/고려대/성균관대/연세대/중앙대)",
                    major=major,
                    notes="2022 공동연구 기준"
                )

        return None

    def get_subject_categories(self, curriculum: str = "2022_개정_교육과정") -> Dict:
        """과목 카테고리 조회"""
        return self.requirements.get("subject_categories", {}).get(curriculum, {})

    def get_major_field_mapping(self) -> Dict:
        """전공 분야 매핑 조회"""
        return self.requirements.get("major_field_mapping", {})

    def search_by_field(self, field: str) -> Dict[str, Any]:
        """
        학문 분야별 권장과목 검색

        Args:
            field: 학문 분야 (예: "공학계열", "의약학계열")

        Returns:
            해당 분야의 전공별 권장과목 딕셔너리
        """
        mapping = self.get_major_field_mapping()
        return mapping.get(field, {})

    def get_course_progression(self, subject: str = "수학") -> Dict[str, str]:
        """
        과목 위계 조회

        Args:
            subject: 교과 (수학, 과학)

        Returns:
            과목 위계 딕셔너리
        """
        categories = self.requirements.get("subject_categories", {})
        hierarchy = categories.get("과목_위계", {})
        return hierarchy.get(subject, {})

    def get_evaluation_criteria(self) -> Dict:
        """평가 기준 조회"""
        return self.requirements.get("evaluation_criteria", {})

    def get_tips_and_guidance(self) -> Dict:
        """과목 선택 팁 및 가이드 조회"""
        return self.requirements.get("tips_and_guidance", {})

    def format_recommendation(self, rec: SubjectRecommendation) -> str:
        """
        추천 결과를 사람이 읽기 쉬운 형태로 포맷팅

        Args:
            rec: SubjectRecommendation 객체

        Returns:
            포맷팅된 문자열
        """
        result = f"## {rec.university} - {rec.major}\n\n"
        result += f"**학문 분야**: {rec.category}\n\n"

        if rec.essential:
            result += "### 핵심 권장과목 (필수적으로 이수)\n"
            for subject in rec.essential:
                result += f"- {subject}\n"
            result += "\n"

        if rec.recommended:
            result += "### 권장과목 (가급적 이수)\n"
            for subject in rec.recommended:
                result += f"- {subject}\n"
            result += "\n"

        if rec.notes:
            result += f"**참고사항**: {rec.notes}\n\n"

        return result


# 사용 예시
if __name__ == "__main__":
    rag = UniversityRAG()

    print("=" * 60)
    print("대학 입학전형 권장과목 RAG 시스템 테스트")
    print("=" * 60)

    # 1. 대학 목록 조회
    print("\n[1] 대학 목록")
    universities = rag.get_universities_list()
    for univ in universities[:3]:
        print(f"- {univ['name']} ({univ['tier']})")

    # 2. 전공별 검색 (서울대 기계공학부)
    print("\n[2] 서울대 기계공학부 권장과목")
    rec = rag.search_major_requirements("서울대학교", "기계공학부")
    if rec:
        print(rag.format_recommendation(rec))

    # 3. 5개 대학 공동연구 (컴퓨터공학)
    print("\n[3] 5개 대학 컴퓨터공학 권장과목")
    rec = rag.search_major_requirements("고려대학교", "컴퓨터학과")
    if rec:
        print(rag.format_recommendation(rec))

    # 4. 학문 분야별 검색
    print("\n[4] 공학계열 - 기계공학 분야")
    field_info = rag.search_by_field("공학계열")
    if "기계공학" in field_info:
        print(json.dumps(field_info["기계공학"], indent=2, ensure_ascii=False))

    # 5. 과목 위계
    print("\n[5] 수학 과목 위계")
    hierarchy = rag.get_course_progression("수학")
    for level, desc in hierarchy.items():
        print(f"- {level}: {desc}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
