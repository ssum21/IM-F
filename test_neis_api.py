"""
NEIS API 테스트 스크립트

실제 API를 호출하여 학교 검색 및 시간표 조회를 테스트합니다.
"""

import os
from dotenv import load_dotenv
from utils.neis_api import NeisAPI

# .env 파일 로드
load_dotenv()


def test_school_search():
    """학교 검색 테스트"""
    print("=" * 60)
    print("1. 학교 기본정보 API 테스트")
    print("=" * 60)

    api = NeisAPI()

    # 테스트할 학교명들
    test_schools = ["서울과학고", "한국과학영재", "경기고"]

    for school_name in test_schools:
        print(f"\n검색어: '{school_name}'")
        print("-" * 60)

        schools = api.search_school(school_name)

        if schools:
            for idx, school in enumerate(schools, 1):
                print(f"{idx}. {school.name}")
                print(f"   - 코드: {school.code}")
                print(f"   - 교육청: {school.edu_office_name} ({school.edu_office_code})")
                print(f"   - 주소: {school.address}")
                print(f"   - 유형: {school.school_type}")
                if school.homepage:
                    print(f"   - 홈페이지: {school.homepage}")
        else:
            print("검색 결과 없음")


def test_timetable():
    """시간표 조회 테스트"""
    print("\n" + "=" * 60)
    print("2. 고등학교 시간표 API 테스트")
    print("=" * 60)

    api = NeisAPI()

    # 먼저 학교 검색
    schools = api.search_school("서울과학고")

    if not schools:
        print("테스트할 학교를 찾을 수 없습니다.")
        return

    school = schools[0]
    print(f"\n테스트 학교: {school.name}")
    print(f"교육청 코드: {school.edu_office_code}")
    print(f"학교 코드: {school.code}")
    print(f"학년도: {api.current_year}, 학기: {api.current_semester}")
    print("-" * 60)

    # 1학년 시간표 조회
    print("\n[1학년 시간표 조회]")
    timetable = api.get_timetable(
        edu_office_code=school.edu_office_code,
        school_code=school.code,
        grade="1"
    )

    if timetable:
        print(f"총 {len(timetable)}개 시간표 항목 조회됨")
        # 처음 10개만 출력
        for idx, item in enumerate(timetable[:10], 1):
            print(f"{idx}. [{item.grade}학년 {item.class_name}] "
                  f"{item.period}교시: {item.subject_name} ({item.date})")
    else:
        print("시간표 데이터가 없습니다.")


def test_subjects_extraction():
    """학교 개설 과목 추출 테스트"""
    print("\n" + "=" * 60)
    print("3. 학교 개설 과목 추출 테스트")
    print("=" * 60)

    api = NeisAPI()

    # 학교 검색
    schools = api.search_school("서울과학고")

    if not schools:
        print("테스트할 학교를 찾을 수 없습니다.")
        return

    school = schools[0]
    print(f"\n학교: {school.name}")
    print("-" * 60)

    # 학년별 과목 추출
    subjects_by_grade = api.get_school_subjects(
        edu_office_code=school.edu_office_code,
        school_code=school.code
    )

    for grade, subjects in subjects_by_grade.items():
        print(f"\n{grade}학년 개설 과목 ({len(subjects)}개):")
        for subject in subjects:
            print(f"  - {subject}")

    # 카테고리별 분류
    print("\n" + "-" * 60)
    print("카테고리별 과목 분류")
    print("-" * 60)

    categorized = api.get_subjects_categorized(
        edu_office_code=school.edu_office_code,
        school_code=school.code
    )

    for category, subjects in categorized.items():
        print(f"\n[{category}] ({len(subjects)}개)")
        for subject in subjects:
            print(f"  - {subject}")


def main():
    """메인 테스트 실행"""
    print("\n🏫 NEIS 교육정보 API 테스트 시작\n")

    # API 키 확인
    api_key = os.getenv("NEIS_API_KEY", "")
    if api_key and api_key != "SAMPLE":
        print(f"✅ API 키 설정됨: {api_key[:10]}...")
    else:
        print("⚠️  API 키 미설정 - SAMPLE 키 사용 (제한적)")

    try:
        # 1. 학교 검색 테스트
        test_school_search()

        # 2. 시간표 조회 테스트
        test_timetable()

        # 3. 과목 추출 테스트
        test_subjects_extraction()

        print("\n" + "=" * 60)
        print("✅ 테스트 완료")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
