"""
🎓 I'MF (아이엠에프) - F학점에서 Future로
고교학점제 맞춤 과목 설계 AI Agent 서비스

Upstage Solar Pro 3 기반 생활기록부 분석 및 최적 과목 추천 시스템
- Document Parse: PDF 문서 OCR 및 텍스트 추출
- Information Extract: 구조화된 학생 정보 추출
- Solar Pro 3: AI 기반 맞춤 과목 추천 (Reasoning Mode)
- Groundedness Check: 추천 근거 검증

제작: Upstage Ambassador 프로젝트
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# =============================================================================
# 페이지 설정 - Streamlit 앱 초기 구성
# 반드시 다른 Streamlit 명령보다 먼저 호출되어야 함
# =============================================================================
st.set_page_config(
    page_title="I'MF | UpStage 고교 학점 설계",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS 로더 클래스 - 스타일시트 관리
# =============================================================================
class StyleLoader:
    """
    커스텀 CSS 로드 및 관리 클래스

    Attributes:
        css_path: CSS 파일 경로
    """

    def __init__(self):
        """스타일 로더 초기화"""
        self.css_path = Path(__file__).parent / "static" / "style.css"

    def load(self) -> None:
        """CSS 파일을 읽어 페이지에 적용"""
        if os.getenv("IMF_DISABLE_CUSTOM_CSS"):
            return
        try:
            if self.css_path.exists():
                with open(self.css_path, "r", encoding="utf-8") as f:
                    css_content = f.read()
                    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <style>
                .stApp {
                    background: #0a0a0c !important;
                    color: #fafafa !important;
                }
                html, body {
                    background: #0a0a0c !important;
                    color: #fafafa !important;
                }
                </style>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <style>
            .stApp {
                background: #0a0a0c !important;
                color: #fafafa !important;
            }
            html, body {
                background: #0a0a0c !important;
                color: #fafafa !important;
            }
            </style>
            """, unsafe_allow_html=True)


# =============================================================================
# 세션 상태 관리 클래스
# =============================================================================
class SessionManager:
    """
    Streamlit 세션 상태 관리 클래스

    세션 변수 초기화 및 관리를 담당
    모든 단계(Step)에서 필요한 데이터를 유지
    """

    # 세션 기본값 정의
    DEFAULTS: Dict[str, Any] = {
        "step": 1,                      # 현재 진행 단계 (1~5)
        "parsed_text": "",              # Document Parse로 추출한 텍스트
        "extracted_info": None,         # Information Extract 결과
        "selected_school": "",          # 선택한 학교명
        "selected_school_info": None,   # NEIS API 학교 상세정보
        "searched_schools": [],         # 학교 검색 결과 목록
        "auto_searched_school": False,  # PDF에서 추출한 학교 자동 검색 완료 여부
        "selected_courses": {},         # 학교 개설 과목
        "target_university": "",        # 목표 대학
        "target_major": "",             # 관심 계열/전공
        "recommendation": None,         # Solar Pro 3 추천 결과
        "verification": None,           # Groundedness Check 결과
        "client": None,                 # Upstage API 클라이언트
        "neis_api": None                # NEIS API 클라이언트
    }

    @classmethod
    def initialize(cls) -> None:
        """세션 상태 초기화 - 미설정 변수만 기본값으로 설정"""
        for key, value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @classmethod
    def reset(cls) -> None:
        """세션 상태 전체 초기화 - 처음부터 다시 시작"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    @staticmethod
    def get_client():
        """
        Upstage 클라이언트 지연 로딩

        Returns:
            UpstageClient: API 클라이언트 인스턴스 또는 None
        """
        if st.session_state.client is None:
            try:
                from utils.upstage_client import UpstageClient
                st.session_state.client = UpstageClient()
            except Exception as e:
                st.error(f"API 클라이언트 초기화 실패: {e}")
                return None
        return st.session_state.client


# =============================================================================
# 데이터 로더 클래스 - JSON 데이터 관리
# =============================================================================
class DataLoader:
    """
    JSON 데이터 파일 로드 클래스

    2022 개정 교육과정 과목 데이터, 대학별 권장과목 데이터 등 로드
    """

    BASE_PATH = Path(__file__).parent / "data"

    @classmethod
    def load_subjects(cls) -> Dict[str, Any]:
        """2022 개정 교육과정 과목 데이터 로드"""
        path = cls.BASE_PATH / "subjects_2022.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"categories": {}}

    @classmethod
    def load_school_courses(cls) -> Dict[str, Any]:
        """샘플 학교 개설 과목 데이터 로드 (폴백용)"""
        path = cls.BASE_PATH / "sample_school_courses.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"schools": {}}

    @classmethod
    def load_university_requirements(cls) -> Dict[str, Any]:
        """대학별 권장 이수과목 데이터 로드"""
        path = cls.BASE_PATH / "university_requirements.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"universities": {}}


# =============================================================================
# UI 컴포넌트 클래스 - 재사용 가능한 UI 요소
# =============================================================================
class UIComponents:
    """
    재사용 가능한 UI 컴포넌트 클래스

    공통적으로 사용되는 UI 요소들을 메서드로 제공
    """

    @staticmethod
    def render_hero() -> None:
        """히어로 섹션 렌더링 - 메인 타이틀"""
        st.markdown('<h1 class="main-header">I\'MF</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sub-header">f학점에서 future로 — ai 기반 고교학점제 맞춤 설계</p>',
            unsafe_allow_html=True
        )

    @staticmethod
    def render_step_indicator(current_step: int) -> None:
        """
        단계 표시기 렌더링

        Args:
            current_step: 현재 진행 단계 (1~5)
        """
        steps = [
            ("01", "생활기록부 업로드", "생기부 PDF 업로드"),
            ("02", "추출 정보 분석", "정보 추출 확인"),
            ("03", "학교 및 진로 설정", "학교 & 진로 설정"),
            ("04", "고교 학점 설계", "AI 학점 설계"),
            ("05", "대학 입시 검증", "추천 근거 검증")
        ]

        # 진행률 계산 (0%에서 시작, 완료 시 100%)
        progress = min((current_step - 1) / 4, 1.0) if current_step > 0 else 0.0

        # 사이드바에 단계 표시
        st.markdown("### 진행 단계")

        for idx, (num, short, desc) in enumerate(steps, 1):
            is_complete = idx < current_step
            is_current = idx == current_step

            # 상태에 따른 스타일 설정
            if is_complete:
                # 완료된 단계 - 민트색
                num_bg = "rgba(0, 212, 170, 0.2)"
                num_color = "#00d4aa"
                text_color = "#00d4aa"
                font_weight = "400"
            elif is_current:
                # 현재 단계 - 골드색
                num_bg = "rgba(212, 175, 55, 0.3)"
                num_color = "#ffd700"
                text_color = "#d4af37"
                font_weight = "600"
            else:
                # 미완료 단계 - 회색
                num_bg = "rgba(85, 85, 85, 0.15)"
                num_color = "#555555"
                text_color = "#555555"
                font_weight = "400"

            st.markdown(f'''
            <div style="display: flex; align-items: center; gap: 10px; padding: 6px 0; margin: 2px 0;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 28px;
                    width: 28px;
                    height: 28px;
                    background: {num_bg};
                    color: {num_color};
                    font-size: 0.75rem;
                    font-weight: 600;
                    border-radius: 50%;
                    font-family: 'JetBrains Mono', monospace;
                ">{num}</span>
                <span style="color: {text_color}; font-weight: {font_weight}; font-size: 0.9rem;">{short}</span>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")
        st.caption(f"진행률 {int(progress * 100)}%")
        st.progress(progress)

    @staticmethod
    def render_info_card(title: str, content: str, card_type: str = "highlight") -> None:
        """
        정보 카드 렌더링

        Args:
            title: 카드 제목
            content: 카드 내용 (HTML 지원)
            card_type: 카드 유형 (highlight, success, metric)
        """
        css_class = f"{card_type}-box"
        st.markdown(f"""
        <div class="{css_class}">
        <strong>{title}</strong><br>
        {content}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_thinking_box(content: str) -> None:
        """
        AI 추론 시각화 박스 렌더링

        Args:
            content: 추론 내용 텍스트
        """
        st.markdown(f"""
        <div class="thinking-box">
        {content}
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 사이드바 렌더러
# =============================================================================
class SidebarRenderer:
    """사이드바 UI 렌더링 클래스"""

    @staticmethod
    def render() -> None:
        """사이드바 전체 렌더링"""
        with st.sidebar:
            # I'MF 그라데이션 로고 영역
            st.markdown("""
            <div style="
                text-align: center; 
                padding: 1.5rem 1rem;
                margin-bottom: 1rem;
            ">
                <div style="
                    font-family: 'Bricolage Grotesque', sans-serif;
                    font-size: 4.5rem;
                    font-weight: 800;
                    letter-spacing: -0.03em;
                    background: linear-gradient(135deg, #d4af37 0%, #f4d03f 25%, #d4af37 50%, #00d4aa 100%);
                    background-size: 200% auto;
                    -webkit-background-clip: text;
                    background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: gradient-shift 4s ease infinite;
                ">I'MF</div>
                <div style="
                    font-size: 1.0rem;
                    color: rgba(255,255,255,0.5);
                    margin-top: 0.25rem;
                    letter-spacing: 0.1em;
                ">UpStage 고교 학점 설계</div>
            </div>
            """, unsafe_allow_html=True)

            # 단계 표시
            UIComponents.render_step_indicator(st.session_state.step)

            st.markdown("---")

            # 리셋 버튼
            if st.button("↺ 처음부터 다시", use_container_width=True):
                SessionManager.reset()
                st.rerun()

            # 푸터
            st.markdown("""
            <div style="margin-top: 2rem; text-align: center;">
                <p style="font-size: 0.7rem; color: #555;">
                    Powered by<br>
                    <strong style="color: #d4af37;">Upstage Solar Pro 3</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# Step 1: 생활기록부 업로드
# =============================================================================
class Step1Upload:
    """
    Step 1: 생활기록부 PDF 업로드 및 분석

    Document Parse API를 사용하여 PDF를 텍스트로 변환
    Extract Agent로 구조화된 정보 추출
    """

    @staticmethod
    def render() -> None:
        """Step 1 UI 렌더링"""
        st.markdown("### 📄 생활기록부 업로드")
        st.markdown("생활기록부 PDF를 업로드하면 AI가 자동으로 분석합니다.")

        col1, col2 = st.columns([2, 1])

        with col1:
            Step1Upload._render_uploader()

        with col2:
            Step1Upload._render_tips()

        st.markdown("---")
        Step1Upload._render_demo_mode()

    @staticmethod
    def _render_uploader() -> None:
        """파일 업로더 렌더링"""
        uploaded_file = st.file_uploader(
            "PDF 파일 선택",
            type=["pdf"],
            help="초등/중학/고등학교 생활기록부 PDF 파일"
        )

        if uploaded_file:
            st.success(f"✓ {uploaded_file.name}")

            if st.button("🔍 AI 분석 시작", type="primary", use_container_width=True):
                Step1Upload._process_upload(uploaded_file)

    @staticmethod
    def _render_tips() -> None:
        """업로드 팁 렌더링"""
        st.markdown("""
        **지원 형식**
        - PDF 파일 (스캔본 포함)
        - 여러 학년 통합 문서 가능

        **분석 항목**
        - 성적 및 강점 과목
        - 수상 경력
        - 동아리/진로 활동
        - 담임 종합 의견
        """)

    @staticmethod
    def _process_upload(uploaded_file) -> None:
        """
        업로드된 파일 처리

        Document Parse → Extract Agent 파이프라인 실행
        """
        with st.spinner("📖 문서를 분석하고 있습니다..."):
            try:
                client = SessionManager.get_client()
                if not client:
                    return

                from agents.document_agent import DocumentAgent
                from agents.extract_agent import ExtractAgent

                # Phase 1: Document Parse
                st.markdown('<div class="thinking-header">📄 Document Parse</div>', unsafe_allow_html=True)

                doc_agent = DocumentAgent(client)
                file_bytes = uploaded_file.read()
                parsed = doc_agent.parse_bytes(file_bytes, uploaded_file.name)
                st.session_state.parsed_text = parsed.text

                # Phase 2: Information Extract
                st.markdown('<div class="thinking-header">🔍 Information Extract</div>', unsafe_allow_html=True)

                extract_agent = ExtractAgent(client)
                thinking_placeholder = st.empty()
                thinking_content = ""

                gen = extract_agent.extract_from_text(parsed.text)

                while True:
                    try:
                        chunk = next(gen)
                        thinking_content += chunk
                        thinking_placeholder.markdown(f"""
                        <div class="thinking-box">{thinking_content}</div>
                        """, unsafe_allow_html=True)
                    except StopIteration as e:
                        st.session_state.extracted_info = e.value
                        st.session_state.auto_searched_school = False  # 새 추출시 자동검색 플래그 초기화
                        st.session_state.step = 2
                        st.rerun()
                        break

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

    @staticmethod
    def _render_demo_mode() -> None:
        """데모 모드 렌더링"""
        st.markdown("**🎮 데모 모드**")
        st.caption("API 키 없이 샘플 데이터로 서비스를 체험해보세요.")

        if st.button("샘플 데이터로 체험", use_container_width=True):
            from agents.extract_agent import ExtractedInfo

            st.session_state.extracted_info = ExtractedInfo(
                student_name="김미래",
                school_name="서울과학고등학교",  # 자동 검색 테스트용 학교명 추가
                school_type="고등학교",
                grade=1,
                strong_subjects=["수학", "과학", "정보"],
                weak_subjects=["국어"],
                awards=["과학탐구대회 금상", "수학경시대회 은상", "정보올림피아드 장려상"],
                club_activities="과학탐구반, 코딩동아리",
                career_activities="소프트웨어 개발 체험, AI 캠프 참가",
                desired_career="소프트웨어 개발자",
                teacher_comments="수학적 사고력이 뛰어나고 프로그래밍에 재능을 보임"
            )
            st.session_state.parsed_text = "[DEMO] 샘플 데이터 사용"
            st.session_state.auto_searched_school = False  # 자동검색 플래그 초기화
            st.session_state.step = 2
            st.rerun()


# =============================================================================
# Step 2: 추출 정보 확인
# =============================================================================
class Step2Review:
    """
    Step 2: 추출된 정보 확인 및 검토

    Information Extract 결과를 사용자에게 표시
    필요시 수정 가능
    """

    @staticmethod
    def render() -> None:
        """Step 2 UI 렌더링"""
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #FFFFFF; font-size: 1.3rem; margin-bottom: 0.5rem;">📊 추출 정보 확인</h3>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem;">생활기록부에서 분석된 정보를 확인하세요</p>
        </div>
        """, unsafe_allow_html=True)

        info = st.session_state.extracted_info
        if not info:
            st.warning("추출된 정보가 없습니다. Step 1을 완료하세요.")
            return

        # 기본 정보 카드
        Step2Review._render_profile_card(info)
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # 2열 레이아웃
        col1, col2 = st.columns(2)

        with col1:
            Step2Review._render_subjects_card(info)

        with col2:
            Step2Review._render_activities_card(info)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # 진로 정보
        Step2Review._render_career_card(info)

        st.markdown("---")
        Step2Review._render_navigation()

    @staticmethod
    def _render_profile_card(info) -> None:
        """프로필 카드 렌더링"""
        name = info.student_name or "미확인"
        school = info.school_type or "미확인"
        grade = info.grade or "미확인"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(28, 28, 32, 0.95) 100%);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.5rem;
        ">
            <div style="
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, var(--imf-gold) 0%, #c9a227 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
            ">👤</div>
            <div style="flex: 1;">
                <h4 style="color: #FFFFFF; margin: 0 0 0.5rem 0; font-size: 1.2rem;">{name}</h4>
                <div style="display: flex; gap: 1rem; color: rgba(255,255,255,0.7); font-size: 0.9rem;">
                    <span>🏫 {school}</span>
                    <span>📚 {grade}학년</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def _render_subjects_card(info) -> None:
        """과목 분석 카드 렌더링"""
        strong_html = ""
        if info.strong_subjects:
            tags = "".join([
                f'<span style="background:rgba(0,212,170,0.15); color:#00d4aa; padding:6px 12px; margin:3px; display:inline-block; border-radius:20px; font-size:0.85rem;">{s}</span>'
                for s in info.strong_subjects
            ])
            strong_html = f'<div style="margin-bottom:0.75rem;"><span style="color:rgba(255,255,255,0.6); font-size:0.8rem;">강점 과목</span><div style="margin-top:0.5rem;">{tags}</div></div>'
        
        weak_html = ""
        if info.weak_subjects:
            tags = "".join([
                f'<span style="background:rgba(255,107,107,0.15); color:#ff6b6b; padding:6px 12px; margin:3px; display:inline-block; border-radius:20px; font-size:0.85rem;">{s}</span>'
                for s in info.weak_subjects
            ])
            weak_html = f'<div><span style="color:rgba(255,255,255,0.6); font-size:0.8rem;">보완 필요</span><div style="margin-top:0.5rem;">{tags}</div></div>'
        
        st.markdown(f"""
        <div style="
            background: rgba(28, 28, 32, 0.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.25rem;
            height: 100%;
        ">
            <h5 style="color:#FFFFFF; margin:0 0 1rem 0; font-size:1rem; display:flex; align-items:center; gap:0.5rem;">
                📚 과목 분석
            </h5>
            {strong_html}
            {weak_html}
            {'' if strong_html or weak_html else '<p style="color:rgba(255,255,255,0.5);">과목 정보 없음</p>'}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def _render_activities_card(info) -> None:
        """활동 정보 카드 렌더링"""
        awards_html = ""
        if info.awards:
            items = "".join([f'<li style="margin-bottom:0.25rem;">{award}</li>' for award in info.awards[:4]])
            awards_html = f'<ul style="margin:0.5rem 0 0.75rem 1rem; padding:0; color:rgba(255,255,255,0.8); font-size:0.9rem;">{items}</ul>'
        
        club_html = ""
        if info.club_activities:
            club_html = f'<div style="margin-top:0.75rem;"><span style="color:rgba(255,255,255,0.6); font-size:0.8rem;">동아리</span><p style="margin:0.25rem 0 0 0; color:#FFFFFF;">{info.club_activities}</p></div>'
        
        st.markdown(f"""
        <div style="
            background: rgba(28, 28, 32, 0.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.25rem;
            height: 100%;
        ">
            <h5 style="color:#FFFFFF; margin:0 0 0.75rem 0; font-size:1rem; display:flex; align-items:center; gap:0.5rem;">
                🏆 수상 & 활동
            </h5>
            {awards_html if awards_html else '<p style="color:rgba(255,255,255,0.5); margin:0;">수상 정보 없음</p>'}
            {club_html}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def _render_career_card(info) -> None:
        """진로 정보 카드 렌더링"""
        career = info.desired_career if info.desired_career else "미확인"
        
        # 진로 카드 메인 부분
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(0, 212, 170, 0.08) 0%, rgba(28, 28, 32, 0.95) 100%);
            border: 1px solid rgba(0, 212, 170, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
        ">
            <h5 style="color:#FFFFFF; margin:0 0 0.75rem 0; font-size:1rem; display:flex; align-items:center; gap:0.5rem;">
                💼 희망 진로
            </h5>
            <div style="
                background: rgba(0, 212, 170, 0.1);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
            ">
                <span style="color:#00d4aa; font-size:1.2rem; font-weight:600;">{career}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 담임 의견 (있을 경우 별도로 렌더링)
        if info.teacher_comments:
            comment_text = info.teacher_comments
            if len(comment_text) > 150:
                comment_text = comment_text[:150] + "..."
            
            st.markdown(f"""
            <div style="
                background: rgba(28, 28, 32, 0.6);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 1rem;
                margin-top: 0.75rem;
            ">
                <span style="color:rgba(255,255,255,0.6); font-size:0.8rem;">📝 담임 의견</span>
                <p style="margin:0.5rem 0 0 0; color:rgba(255,255,255,0.85); font-size:0.9rem; line-height:1.6;">{comment_text}</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def _render_navigation() -> None:
        """네비게이션 버튼 렌더링"""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("← 이전", use_container_width=True):
                st.session_state.step = 1
                st.rerun()

        with col2:
            if st.button("다음 →", type="primary", use_container_width=True):
                st.session_state.step = 3
                st.rerun()


# =============================================================================
# Step 3: 학교/진로 설정
# =============================================================================
class Step3Settings:
    """
    Step 3: 학교 및 진로 설정

    NEIS API를 통한 학교 검색 및 개설 과목 조회
    목표 대학/전공 설정
    """

    @staticmethod
    def render() -> None:
        """Step 3 UI 렌더링"""
        st.markdown("### 🏫 학교 & 진로 설정")

        # NEIS API 초기화
        if st.session_state.neis_api is None:
            from utils.neis_api import NeisAPI
            st.session_state.neis_api = NeisAPI()

        col1, col2 = st.columns(2)

        with col1:
            Step3Settings._render_school_search()

        with col2:
            Step3Settings._render_career_settings()

        st.markdown("---")
        Step3Settings._render_navigation()

    @staticmethod
    def _render_school_search() -> None:
        """학교 검색 UI 렌더링"""
        st.markdown("**🔍 학교 검색**")

        neis = st.session_state.neis_api

        # 자동 검색: PDF에서 추출된 학교명이 있고 아직 선택 안된 경우
        info = st.session_state.extracted_info
        auto_searched_key = "auto_searched_school"

        if (info and info.school_name and
            not st.session_state.selected_school and
            not st.session_state.get(auto_searched_key)):

            with st.spinner(f"'{info.school_name}' 검색 중..."):
                results = neis.search_school(info.school_name)
                st.session_state.searched_schools = results
                st.session_state[auto_searched_key] = True

                # 첫 번째 결과 자동 선택
                if results and len(results) > 0:
                    Step3Settings._select_school(results[0], neis)
                    st.success(f"✅ '{results[0].name}' 자동 선택 완료")
                    st.rerun()

        search_query = st.text_input(
            "학교명 입력",
            placeholder="예: 서울과학고, 경기고..."
        )

        if st.button("검색", use_container_width=True) and search_query:
            with st.spinner("검색 중..."):
                results = neis.search_school(search_query)
                st.session_state.searched_schools = results

        # 검색 결과 표시
        if st.session_state.searched_schools:
            st.markdown(f"**검색 결과** ({len(st.session_state.searched_schools)}개)")

            for i, school in enumerate(st.session_state.searched_schools[:8]):
                label = f"{school.name}"
                if school.edu_office_name:
                    label += f" ({school.edu_office_name})"

                if st.button(label, key=f"school_{i}", use_container_width=True):
                    Step3Settings._select_school(school, neis)

        # 선택된 학교 정보
        if st.session_state.selected_school:
            Step3Settings._render_selected_school()

    @staticmethod
    def _select_school(school, neis) -> None:
        """
        학교 선택 처리

        Args:
            school: 선택된 학교 정보
            neis: NEIS API 클라이언트
        """
        st.session_state.selected_school = school.name
        st.session_state.selected_school_info = school

        # 개설 과목 조회
        with st.spinner(f"{school.name} 과목 조회 중..."):
            courses = neis.get_subjects_categorized(
                school.edu_office_code,
                school.code
            )

            if courses and any(courses.values()):
                st.session_state.selected_courses = courses
            else:
                # 폴백: 샘플 데이터 사용
                sample_data = DataLoader.load_school_courses()
                sample_schools = sample_data.get("schools", {})
                if sample_schools:
                    first_school = list(sample_schools.values())[0]
                    st.session_state.selected_courses = first_school.get("available_subjects", {})

        st.rerun()

    @staticmethod
    def _render_selected_school() -> None:
        """선택된 학교 정보 렌더링"""
        school_info = st.session_state.selected_school_info

        info_html = f"<strong>🏫 {st.session_state.selected_school}</strong>"
        if school_info:
            if school_info.edu_office_name:
                info_html += f"<br>📍 {school_info.edu_office_name}"
            if school_info.school_type:
                info_html += f" | {school_info.school_type}"

        UIComponents.render_info_card("", info_html)

        # 개설 과목 표시
        if st.session_state.selected_courses:
            with st.expander("📚 개설 과목 보기", expanded=False):
                for category, subjects in st.session_state.selected_courses.items():
                    if subjects:
                        subjects_preview = ", ".join(subjects[:8])
                        if len(subjects) > 8:
                            subjects_preview += f" 외 {len(subjects) - 8}개"
                        st.markdown(f"**{category}:** {subjects_preview}")

    @staticmethod
    def _render_career_settings() -> None:
        """진로 설정 UI 렌더링"""
        st.markdown("**🎯 목표 설정**")

        # RAG에서 대학 목록 가져오기
        try:
            from utils.university_rag import UniversityRAG
            rag = UniversityRAG()
            univ_list = rag.get_universities_list()

            # 티어별로 정렬
            sky_univs = [u["name"] for u in univ_list if u.get("tier") == "SKY"]
            top_univs = [u["name"] for u in univ_list if u.get("tier") == "상위권"]
            others = [u["name"] for u in univ_list if u.get("tier") not in ["SKY", "상위권"]]

            universities = ["선택 안함"] + sky_univs + top_univs + others + ["기타"]
        except Exception as e:
            # RAG 실패시 기본 목록 사용
            universities = [
                "선택 안함", "서울대학교", "연세대학교", "고려대학교",
                "KAIST", "POSTECH", "성균관대학교", "한양대학교",
                "경희대학교", "중앙대학교", "건국대학교", "동국대학교", "기타"
            ]

        st.session_state.target_university = st.selectbox(
            "목표 대학",
            universities
        )

        majors = [
            "선택 안함", "공학", "자연과학", "의예", "약학",
            "인문", "사회과학", "경영", "교육", "예술", "체육", "기타"
        ]
        st.session_state.target_major = st.selectbox(
            "관심 계열",
            majors
        )

        # 구체적 진로
        info = st.session_state.extracted_info
        default_career = info.desired_career if info else ""

        custom_career = st.text_input(
            "구체적 희망 직업 (선택)",
            value=default_career,
            placeholder="예: 소프트웨어 개발자, 의사..."
        )

        if custom_career and info:
            info.desired_career = custom_career

        # 선택 요약
        if st.session_state.target_university != "선택 안함" or st.session_state.target_major != "선택 안함":
            st.markdown("**📌 선택 요약**")
            summary_parts = []
            if st.session_state.target_university != "선택 안함":
                summary_parts.append(f"🎓 {st.session_state.target_university}")
            if st.session_state.target_major != "선택 안함":
                summary_parts.append(f"📚 {st.session_state.target_major}")
            if custom_career:
                summary_parts.append(f"💼 {custom_career}")
            st.caption(" | ".join(summary_parts))

    @staticmethod
    def _render_navigation() -> None:
        """네비게이션 버튼 렌더링"""
        col1, col2 = st.columns(2)

        # 진행 가능 조건 체크
        can_proceed = (
            st.session_state.selected_school and
            st.session_state.target_major != "선택 안함"
        )

        with col1:
            if st.button("← 이전", use_container_width=True):
                st.session_state.step = 2
                st.rerun()

        with col2:
            if st.button("🎯 AI 추천 받기 →", type="primary", use_container_width=True, disabled=not can_proceed):
                st.session_state.step = 4
                st.rerun()

            if not can_proceed:
                st.caption("학교 선택 및 관심 계열을 지정하세요")


# =============================================================================
# Step 4: AI 학점 설계
# =============================================================================
class Step4Recommend:
    """
    Step 4: AI 맞춤 학점 설계

    Solar Pro 3 Reasoning Mode를 사용하여
    학생 프로필 기반 맞춤 과목 조합 추천
    """

    @staticmethod
    def render() -> None:
        """Step 4 UI 렌더링"""
        st.markdown("### 🎓 AI 맞춤 학점 설계")

        if not st.session_state.recommendation:
            Step4Recommend._generate_recommendation()
        else:
            Step4Recommend._display_recommendation()

        st.markdown("---")
        Step4Recommend._render_navigation()

    @staticmethod
    def _generate_recommendation() -> None:
        """Solar Pro 3로 추천 생성"""
        st.markdown('<div class="thinking-header">🧠 Solar Pro 3 Reasoning</div>', unsafe_allow_html=True)

        thinking_placeholder = st.empty()
        thinking_content = ""

        try:
            client = SessionManager.get_client()
            if not client:
                return

            from agents.recommend_agent import RecommendAgent

            agent = RecommendAgent(client)

            # 학생 프로필 구성
            info = st.session_state.extracted_info
            profile = {
                "strong_subjects": info.strong_subjects if info else [],
                "weak_subjects": info.weak_subjects if info else [],
                "awards": info.awards if info else [],
                "club_activities": info.club_activities if info else "",
                "desired_career": info.desired_career if info else ""
            }

            # 추천 생성 (스트리밍)
            gen = agent.recommend(
                student_profile=profile,
                school_courses=st.session_state.selected_courses,
                target_university=st.session_state.target_university,
                target_major=st.session_state.target_major
            )

            # 스트리밍 루프
            while True:
                try:
                    chunk = next(gen)
                    thinking_content += chunk
                    thinking_placeholder.markdown(f"""
                    <div class="thinking-box">{thinking_content}</div>
                    """, unsafe_allow_html=True)
                except StopIteration as e:
                    st.session_state.recommendation = e.value
                    st.rerun()
                    break

        except Exception as e:
            st.error(f"추천 생성 중 오류: {e}")

    @staticmethod
    def _display_recommendation() -> None:
        """추천 결과 표시"""
        rec = st.session_state.recommendation

        # 총 학점 배너
        st.markdown(f"""
        <div class="success-box">
        <h2 style="margin:0; color:#00d4aa;">📊 총 {rec.total_credits}학점 설계 완료</h2>
        </div>
        """, unsafe_allow_html=True)

        # 학년별 과목
        years = [
            (rec.year1, "1학년", "공통과목 중심"),
            (rec.year2, "2학년", "선택과목 시작"),
            (rec.year3, "3학년", "심화/진로 집중")
        ]

        for year_data, year_name, year_desc in years:
            if year_data:
                with st.expander(f"📚 {year_name} — {year_desc}", expanded=True):
                    for semester, subjects in year_data.items():
                        if subjects and isinstance(subjects, list):
                            st.markdown(f"**{semester}**")

                            # 과목 칩 형태로 표시
                            chips_html = " ".join([
                                f'<span class="course-chip">{s}</span>'
                                for s in subjects
                            ])
                            st.markdown(chips_html, unsafe_allow_html=True)

        # 추천 근거
        if rec.reasoning:
            st.markdown("**💡 추천 근거**")
            st.info(rec.reasoning)

        # 핵심 포인트
        if rec.highlights:
            st.markdown("**✨ 핵심 포인트**")
            for hl in rec.highlights:
                st.markdown(f"• {hl}")

    @staticmethod
    def _render_navigation() -> None:
        """네비게이션 버튼 렌더링"""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("← 설정 수정", use_container_width=True):
                st.session_state.step = 3
                st.session_state.recommendation = None
                st.rerun()

        with col2:
            if st.button("✓ 검증하기 →", type="primary", use_container_width=True):
                st.session_state.step = 5
                st.rerun()


# =============================================================================
# Step 5: 검증 결과
# =============================================================================
class Step5Verify:
    """
    Step 5: 추천 검증

    Groundedness Check를 통해 추천의 근거 검증
    학생 프로필 대비 추천 적합성 평가
    """

    @staticmethod
    def render() -> None:
        """Step 5 UI 렌더링"""
        st.markdown("### ✓ 추천 검증 결과")

        if not st.session_state.verification:
            Step5Verify._run_verification()
        else:
            Step5Verify._display_verification()

        st.markdown("---")
        Step5Verify._render_completion()

    @staticmethod
    def _run_verification() -> None:
        """Groundedness Check 실행"""
        st.markdown('<div class="thinking-header">🔍 Groundedness Check</div>', unsafe_allow_html=True)

        thinking_placeholder = st.empty()
        thinking_content = ""

        try:
            client = SessionManager.get_client()
            if not client:
                return

            from agents.verify_agent import VerifyAgent

            agent = VerifyAgent(client)

            # 프로필 구성
            info = st.session_state.extracted_info
            profile = {
                "strong_subjects": info.strong_subjects if info else [],
                "weak_subjects": info.weak_subjects if info else [],
                "awards": info.awards if info else [],
                "club_activities": info.club_activities if info else "",
                "career_activities": info.career_activities if info else "",
                "desired_career": info.desired_career if info else "",
                "teacher_comments": info.teacher_comments if info else ""
            }

            rec = st.session_state.recommendation
            rec_text = rec.reasoning if rec else ""

            # 검증 실행 (스트리밍)
            gen = agent.verify(profile, rec_text)

            while True:
                try:
                    chunk = next(gen)
                    thinking_content += chunk
                    thinking_placeholder.markdown(f"""
                    <div class="thinking-box">{thinking_content}</div>
                    """, unsafe_allow_html=True)
                except StopIteration as e:
                    st.session_state.verification = e.value
                    st.rerun()
                    break

        except Exception as e:
            st.error(f"검증 중 오류: {e}")

    @staticmethod
    def _display_verification() -> None:
        """검증 결과 표시"""
        result = st.session_state.verification

        # 메트릭 카드
        col1, col2, col3 = st.columns(3)

        with col1:
            status = "✓ 검증 통과" if result.is_grounded else "⚠ 검토 필요"
            status_color = "#00d4aa" if result.is_grounded else "#ffc107"
            st.markdown(f"""
            <div class="metric-card">
            <h2 style="color: {status_color};">{status}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            score_pct = int(result.score * 100)
            st.metric("근거도 점수", f"{score_pct}%")

        with col3:
            evidence_count = len(result.evidence) if result.evidence else 0
            st.metric("발견 근거", f"{evidence_count}개")

        # 검증 상세
        st.markdown("**📝 검증 상세**")
        UIComponents.render_info_card("", result.explanation)

        # 근거 목록
        if result.evidence:
            st.markdown("**📌 발견된 근거**")
            for ev in result.evidence:
                st.markdown(f"• {ev}")

        # 개선 제안
        if result.suggestions:
            st.markdown("**💡 개선 제안**")
            for sug in result.suggestions:
                st.info(sug)

    @staticmethod
    def _render_completion() -> None:
        """완료 화면 렌더링"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
        <h2 style="color: #d4af37;">🎉 학점 설계 완료!</h2>
        <p style="color: #888;">F학점에서 Future로, I'MF와 함께!</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("← 추천 다시 보기", use_container_width=True):
                st.session_state.step = 4
                st.rerun()

        with col2:
            if st.button("↺ 새로운 분석 시작", type="primary", use_container_width=True):
                SessionManager.reset()
                st.rerun()


# =============================================================================
# 메인 애플리케이션
# =============================================================================
class IMFApp:
    """
    I'MF 메인 애플리케이션 클래스

    전체 앱 흐름 제어 및 라우팅 담당
    """

    # Step별 렌더러 매핑
    STEP_RENDERERS = {
        1: Step1Upload,
        2: Step2Review,
        3: Step3Settings,
        4: Step4Recommend,
        5: Step5Verify
    }

    def __init__(self):
        """앱 초기화"""
        # 세션 상태 초기화 (CSS 로드 전에 먼저 초기화)
        SessionManager.initialize()
        # CSS를 로드하여 배경색이 제대로 적용되도록 함
        StyleLoader().load()

    def run(self) -> None:
        """앱 실행"""
        try:
            # 히어로 섹션
            UIComponents.render_hero()

            # 사이드바
            SidebarRenderer.render()

            # 현재 단계 렌더링
            current_step = st.session_state.get('step', 1)
            renderer_class = self.STEP_RENDERERS.get(current_step, Step1Upload)
            renderer_class.render()

            # 푸터
            self._render_footer()
        except Exception as e:
            # 에러 발생 시 사용자에게 표시
            st.error(f"앱 실행 중 오류가 발생했습니다: {e}")
            st.exception(e)

    @staticmethod
    def _render_footer() -> None:
        """푸터 렌더링"""
        st.markdown("---")
        st.markdown("""
        <div class="footer-section">
        Powered by <a href="https://upstage.ai" target="_blank">Upstage Solar Pro 3</a> |
        2022 개정 교육과정 기반 |
        Upstage Ambassador Project
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 엔트리 포인트
# =============================================================================
# Streamlit은 파일이 로드될 때 자동으로 실행되므로
# if __name__ == "__main__" 블록 밖에서도 실행됨
# 하지만 명시적으로 실행 흐름을 제어하기 위해 여기에 배치
try:
    app = IMFApp()
    app.run()
except Exception as e:
    # 최상위 레벨 에러 처리
    st.error(f"앱 초기화 중 오류가 발생했습니다: {e}")
    st.exception(e)