"""
🏫 나이스 교육정보 API 통합 모듈

NEIS Open API를 활용한 학교 정보 및 시간표 조회
- 학교 기본정보 조회 (schoolInfo)
- 고등학교 시간표 조회 (hisTimetable)
- 학교별 개설 과목 자동 추출

API 문서: https://open.neis.go.kr
"""

import os
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SchoolInfo:
    """학교 정보 데이터 클래스"""
    code: str = ""                    # 행정표준코드
    name: str = ""                    # 학교명
    edu_office_code: str = ""         # 시도교육청코드
    edu_office_name: str = ""         # 시도교육청명
    address: str = ""                 # 주소
    school_type: str = ""             # 학교 유형 (일반고/특목고 등)
    homepage: str = ""                # 홈페이지


@dataclass
class TimetableSubject:
    """시간표 과목 정보"""
    subject_name: str = ""
    grade: str = ""
    class_name: str = ""
    period: str = ""
    date: str = ""


@dataclass
class NeisAPIResponse:
    """NEIS API 응답 데이터 클래스"""
    success: bool = False
    message: str = ""
    code: str = ""
    data: Any = None


class NeisAPI:
    """
    나이스 교육정보 API 클라이언트

    학교 검색 및 시간표 조회를 통해 개설 과목 정보를 추출

    Example:
        >>> api = NeisAPI()
        >>> schools = api.search_school("서울과학고")
        >>> subjects = api.get_school_subjects(schools[0].edu_office_code, schools[0].code)
    """

    BASE_URL = "https://open.neis.go.kr/hub"

    # 시도교육청 코드 매핑
    EDU_OFFICE_CODES = {
        "서울": "B10", "부산": "C10", "대구": "D10", "인천": "E10",
        "광주": "F10", "대전": "G10", "울산": "H10", "세종": "I10",
        "경기": "J10", "강원": "K10", "충북": "M10", "충남": "N10",
        "전북": "P10", "전남": "Q10", "경북": "R10", "경남": "S10", "제주": "T10"
    }

    # NEIS API 에러 코드 매핑
    ERROR_MESSAGES = {
        "300": "필수 값이 누락되어 있습니다.",
        "290": "인증키가 유효하지 않습니다.",
        "310": "해당하는 서비스를 찾을 수 없습니다.",
        "333": "요청위치 값의 타입이 유효하지 않습니다.",
        "336": "데이터요청은 한번에 최대 1,000건을 넘을 수 없습니다.",
        "337": "일별 트래픽 제한을 넘은 호출입니다.",
        "500": "서버 오류입니다.",
        "600": "데이터베이스 연결 오류입니다.",
        "601": "SQL 문장 오류 입니다.",
        "000": "정상 처리되었습니다.",
        "200": "해당하는 데이터가 없습니다."
    }

    def __init__(self, api_key: Optional[str] = None):
        """초기화 - API 키 설정"""
        self.api_key = api_key or os.getenv("NEIS_API_KEY", "")
        # API 키 없으면 샘플 키 사용 (제한적)
        if not self.api_key:
            self.api_key = "SAMPLE"

        # 현재 학년도 자동 설정 (3월 기준)
        now = datetime.now()
        self.current_year = now.year if now.month >= 3 else now.year - 1
        self.current_semester = "1" if 3 <= now.month <= 8 else "2"
    
    def _parse_api_response(self, response_data: Dict[str, Any], service_name: str) -> NeisAPIResponse:
        """
        NEIS API 응답 파싱 및 에러 처리

        Args:
            response_data: API 응답 JSON
            service_name: 서비스명 (schoolInfo, hisTimetable 등)

        Returns:
            NeisAPIResponse: 파싱된 응답 데이터
        """
        # RESULT 메시지 확인
        if "RESULT" in response_data:
            result = response_data["RESULT"]
            code = result.get("CODE", "")
            message = result.get("MESSAGE", "")

            # 에러 코드 처리
            if code != "INFO-000":
                error_msg = self.ERROR_MESSAGES.get(code.split("-")[-1], message)
                return NeisAPIResponse(
                    success=False,
                    message=error_msg,
                    code=code,
                    data=None
                )

        # 정상 데이터 처리
        if service_name in response_data:
            # [0]: head 정보, [1]: row 데이터
            if len(response_data[service_name]) > 1:
                rows = response_data[service_name][1].get("row", [])
                return NeisAPIResponse(
                    success=True,
                    message="정상 처리",
                    code="INFO-000",
                    data=rows
                )

        # 데이터가 없는 경우
        return NeisAPIResponse(
            success=False,
            message="해당하는 데이터가 없습니다.",
            code="INFO-200",
            data=None
        )

    def search_school(self, school_name: str, school_type: str = "고등학교") -> List[SchoolInfo]:
        """
        학교명으로 학교 검색

        Args:
            school_name: 검색할 학교명 (부분 일치)
            school_type: 학교 유형 필터 (고등학교/중학교 등)

        Returns:
            list[SchoolInfo]: 검색된 학교 목록
        """
        try:
            url = f"{self.BASE_URL}/schoolInfo"
            params = {
                "KEY": self.api_key,
                "Type": "json",
                "pIndex": 1,
                "pSize": 20,
                "SCHUL_NM": school_name
            }

            # 학교종류명 필터 추가 (선택사항)
            if school_type:
                params["SCHUL_KND_SC_NM"] = school_type

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # API 응답 파싱
            parsed = self._parse_api_response(data, "schoolInfo")

            if parsed.success and parsed.data:
                return [self._parse_school_info(row) for row in parsed.data]
            else:
                print(f"학교 검색 결과 없음: {parsed.message}")
                return self._get_sample_schools(school_name)

        except requests.RequestException as e:
            print(f"학교 검색 네트워크 오류: {e}")
            return self._get_sample_schools(school_name)
        except Exception as e:
            print(f"학교 검색 API 오류: {e}")
            return self._get_sample_schools(school_name)
    
    def _parse_school_info(self, row: Dict[str, Any]) -> SchoolInfo:
        """API 응답을 SchoolInfo로 변환"""
        return SchoolInfo(
            code=row.get("SD_SCHUL_CODE", ""),
            name=row.get("SCHUL_NM", ""),
            edu_office_code=row.get("ATPT_OFCDC_SC_CODE", ""),
            edu_office_name=row.get("ATPT_OFCDC_SC_NM", ""),
            address=row.get("ORG_RDNMA", ""),
            school_type=row.get("HS_SC_NM", row.get("SCHUL_KND_SC_NM", "")),
            homepage=row.get("HMPG_ADRES", "")
        )
    
    def get_timetable(
        self,
        edu_office_code: str,
        school_code: str,
        grade: Optional[str] = None,
        semester: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[TimetableSubject]:
        """
        고등학교 시간표 조회

        Args:
            edu_office_code: 시도교육청코드 (예: "B10")
            school_code: 행정표준코드
            grade: 학년 필터 (1/2/3)
            semester: 학기 (1/2)
            year: 학년도 (미지정시 현재 학년도)

        Returns:
            list[TimetableSubject]: 시간표 과목 목록
        """
        try:
            url = f"{self.BASE_URL}/hisTimetable"
            params = {
                "KEY": self.api_key,
                "Type": "json",
                "pIndex": 1,
                "pSize": 1000,
                "ATPT_OFCDC_SC_CODE": edu_office_code,
                "SD_SCHUL_CODE": school_code,
                "AY": str(year) if year else str(self.current_year)
            }

            # 선택적 파라미터 추가
            if grade:
                params["GRADE"] = str(grade)
            if semester:
                params["SEM"] = str(semester)
            else:
                # 학기 미지정시 현재 학기 사용
                params["SEM"] = self.current_semester

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # API 응답 파싱
            parsed = self._parse_api_response(data, "hisTimetable")

            if parsed.success and parsed.data:
                return [self._parse_timetable(row) for row in parsed.data]
            else:
                print(f"시간표 조회 결과: {parsed.message}")
                return []

        except requests.RequestException as e:
            print(f"시간표 조회 네트워크 오류: {e}")
            return []
        except Exception as e:
            print(f"시간표 조회 API 오류: {e}")
            return []
    
    def _parse_timetable(self, row: Dict[str, Any]) -> TimetableSubject:
        """시간표 응답 파싱"""
        return TimetableSubject(
            subject_name=row.get("ITRT_CNTNT", "").strip(),
            grade=row.get("GRADE", ""),
            class_name=row.get("CLASS_NM", ""),
            period=row.get("PERIO", ""),
            date=row.get("ALL_TI_YMD", "")
        )
    
    def get_school_subjects(
        self, 
        edu_office_code: str, 
        school_code: str
    ) -> Dict[str, List[str]]:
        """
        학교 개설 과목 추출 (시간표에서 과목 목록 추출)
        
        Args:
            edu_office_code: 시도교육청코드
            school_code: 학교코드
        
        Returns:
            dict: 학년별 개설 과목 {"1": [...], "2": [...], "3": [...]}
        """
        timetable = self.get_timetable(edu_office_code, school_code)
        
        if not timetable:
            return self._get_sample_subjects()
        
        # 학년별 과목 추출 (중복 제거)
        subjects_by_grade: Dict[str, set] = {"1": set(), "2": set(), "3": set()}
        
        for item in timetable:
            if item.subject_name and item.grade in subjects_by_grade:
                # 빈 과목이나 특수 항목 제외
                if item.subject_name not in ["", "-", "자습", "조회", "종례"]:
                    subjects_by_grade[item.grade].add(item.subject_name)
        
        return {
            grade: sorted(list(subjects)) 
            for grade, subjects in subjects_by_grade.items()
        }
    
    def get_subjects_categorized(
        self, 
        edu_office_code: str, 
        school_code: str
    ) -> Dict[str, List[str]]:
        """
        학교 개설 과목을 카테고리별로 분류
        
        Returns:
            dict: {"일반선택": [...], "진로선택": [...], "융합선택": [...]}
        """
        raw_subjects = self.get_school_subjects(edu_office_code, school_code)
        
        # 모든 학년 과목 합치기
        all_subjects = set()
        for subjects in raw_subjects.values():
            all_subjects.update(subjects)
        
        # 과목 카테고리 분류 (간단 휴리스틱)
        categorized = {
            "일반선택": [],
            "진로선택": [],
            "융합선택": []
        }
        
        # 진로선택 키워드
        advanced_keywords = ["II", "Ⅱ", "심화", "실험", "탐구", "과제", "프로그래밍", "인공지능"]
        # 융합선택 키워드  
        fusion_keywords = ["생활", "실용", "문화", "역사와", "스포츠", "감상", "미디어"]
        
        for subject in all_subjects:
            if any(kw in subject for kw in advanced_keywords):
                categorized["진로선택"].append(subject)
            elif any(kw in subject for kw in fusion_keywords):
                categorized["융합선택"].append(subject)
            else:
                categorized["일반선택"].append(subject)
        
        # 정렬
        for key in categorized:
            categorized[key] = sorted(categorized[key])
        
        return categorized
    
    def _get_sample_schools(self, query: str) -> List[SchoolInfo]:
        """샘플 학교 데이터 (API 사용 불가시 폴백)"""
        samples = [
            SchoolInfo("7010083", "서울과학고등학교", "B10", "서울특별시교육청", 
                      "서울특별시 종로구", "과학고", "http://sshs.sen.hs.kr"),
            SchoolInfo("7530174", "한국과학영재학교", "C10", "부산광역시교육청",
                      "부산광역시 해운대구", "과학영재학교", "http://www.ksa.hs.kr"),
            SchoolInfo("7010088", "서울고등학교", "B10", "서울특별시교육청",
                      "서울특별시 서초구", "일반고", ""),
            SchoolInfo("7010091", "경기고등학교", "B10", "서울특별시교육청",
                      "서울특별시 강남구", "일반고", ""),
            SchoolInfo("7010156", "한영외국어고등학교", "B10", "서울특별시교육청",
                      "서울특별시 강동구", "외국어고", ""),
        ]
        return [s for s in samples if query.lower() in s.name.lower()]
    
    def _get_sample_subjects(self) -> Dict[str, List[str]]:
        """샘플 과목 데이터"""
        return {
            "1": ["국어", "수학", "영어", "통합사회", "통합과학", "한국사"],
            "2": ["문학", "확률과통계", "미적분", "영어I", "물리학I", "화학I", "정보"],
            "3": ["화법과작문", "기하", "영어II", "물리학II", "생명과학II", "프로그래밍"]
        }
