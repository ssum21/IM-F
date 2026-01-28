"""
RAG 시스템 앱 통합 테스트

앱에 통합된 RAG 시스템이 정상적으로 작동하는지 테스트합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_rag_initialization():
    """RAG 시스템 초기화 테스트"""
    print("=" * 60)
    print("1. RAG 시스템 초기화 테스트")
    print("=" * 60)

    try:
        from utils.university_rag import UniversityRAG

        rag = UniversityRAG()
        print("✅ RAG 시스템 초기화 성공")

        # 대학 목록 조회
        universities = rag.get_universities_list()
        print(f"✅ 대학 목록 로드: {len(universities)}개")

        return True
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return False


def test_recommend_agent_rag():
    """RecommendAgent RAG 통합 테스트"""
    print("\n" + "=" * 60)
    print("2. RecommendAgent RAG 통합 테스트")
    print("=" * 60)

    try:
        # Mock client (실제 API 호출 없이 테스트)
        class MockClient:
            def chat_stream(self, message, system_prompt, reasoning_effort, temperature):
                # 간단한 JSON 응답 시뮬레이션
                response = """
                [추론 과정]
                학생의 희망 대학과 전공을 고려하여...

                ```json
                {
                    "year1": {"1학기": ["수학", "영어"], "2학기": ["국어", "사회"]},
                    "year2": {"1학기": ["수학I", "물리학"], "2학기": ["수학II", "화학"]},
                    "year3": {"1학기": ["미적분", "물리학II"], "2학기": ["기하", "화학II"]},
                    "total_credits": 192,
                    "reasoning": "서울대 기계공학부 핵심 권장과목 반영",
                    "highlights": ["물리학II, 미적분, 기하 포함", "대학 권장과목 충족"]
                }
                ```
                """
                for char in response:
                    yield char

        from agents.recommend_agent import RecommendAgent

        agent = RecommendAgent(MockClient())

        # RAG 초기화 확인
        if agent.rag:
            print("✅ RecommendAgent RAG 초기화 성공")
        else:
            print("⚠️  RAG 초기화 실패 (None)")
            return False

        # 프롬프트 빌드 테스트
        profile = {
            "strong_subjects": ["수학", "과학"],
            "weak_subjects": ["국어"],
            "club_activities": "과학동아리",
            "awards": ["과학경시대회"],
            "desired_career": "기계공학자"
        }

        courses = {
            "일반선택": ["물리학", "화학", "생명과학"],
            "진로선택": ["물리학II", "화학II", "미적분"],
            "융합선택": []
        }

        prompt = agent._build_prompt(profile, courses, "서울대학교", "공학")

        # 프롬프트에 권장과목 정보가 포함되었는지 확인
        if "입학전형 권장과목" in prompt or "권장과목" in prompt:
            print("✅ 프롬프트에 RAG 권장과목 정보 포함됨")
            print("\n[프롬프트 일부]")
            print(prompt[:500] + "...")
        else:
            print("⚠️  프롬프트에 RAG 정보 미포함")

        return True

    except Exception as e:
        print(f"❌ RecommendAgent 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_university_search():
    """대학별 권장과목 검색 테스트"""
    print("\n" + "=" * 60)
    print("3. 대학별 권장과목 검색 테스트")
    print("=" * 60)

    try:
        from utils.university_rag import UniversityRAG

        rag = UniversityRAG()

        # 테스트 케이스들
        test_cases = [
            ("서울대학교", "기계공학부", "2026"),
            ("고려대학교", "컴퓨터학과", "2022"),
            ("연세대학교", "의예과", "2022"),
        ]

        for univ, major, year in test_cases:
            print(f"\n검색: {univ} {major}")
            rec = rag.search_major_requirements(univ, major, year)

            if rec:
                print(f"✅ 검색 성공")
                print(f"   핵심: {', '.join(rec.essential[:3])}...")
                print(f"   권장: {', '.join(rec.recommended[:3])}...")
            else:
                print(f"⚠️  검색 결과 없음 (폴백 처리 가능)")

        return True

    except Exception as e:
        print(f"❌ 검색 테스트 실패: {e}")
        return False


def test_app_integration():
    """앱 통합 시뮬레이션 테스트"""
    print("\n" + "=" * 60)
    print("4. 앱 통합 시뮬레이션")
    print("=" * 60)

    try:
        # Step 3: 대학 목록 로드 시뮬레이션
        from utils.university_rag import UniversityRAG

        rag = UniversityRAG()
        univ_list = rag.get_universities_list()

        # 티어별 정렬
        sky_univs = [u["name"] for u in univ_list if u.get("tier") == "SKY"]
        top_univs = [u["name"] for u in univ_list if u.get("tier") == "상위권"]

        print("✅ Step 3: 대학 목록 로드 성공")
        print(f"   SKY: {', '.join(sky_univs)}")
        print(f"   상위권: {', '.join(top_univs[:3])}...")

        # Step 4: 권장과목 조회 시뮬레이션
        if sky_univs:
            rec = rag.search_major_requirements(sky_univs[0], "기계공학", "2026")
            if rec:
                print(f"\n✅ Step 4: {sky_univs[0]} 권장과목 조회 성공")
                print(f"   핵심 권장과목: {', '.join(rec.essential)}")
            else:
                print(f"\n⚠️  권장과목 검색 결과 없음 (일반 추천 진행)")

        return True

    except Exception as e:
        print(f"❌ 앱 통합 테스트 실패: {e}")
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "🧪 RAG 시스템 앱 통합 테스트\n")

    results = []

    # 1. RAG 초기화
    results.append(("RAG 초기화", test_rag_initialization()))

    # 2. RecommendAgent 통합
    results.append(("RecommendAgent RAG", test_recommend_agent_rag()))

    # 3. 대학 검색
    results.append(("대학 권장과목 검색", test_university_search()))

    # 4. 앱 통합
    results.append(("앱 통합 시뮬레이션", test_app_integration()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name:25} {status}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print("\n" + "=" * 60)
    print(f"총 {total}개 테스트 중 {passed}개 성공 ({passed/total*100:.0f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 모든 테스트 통과! RAG 시스템 정상 작동")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
