"""
📄 Document Agent - 문서 파싱 에이전트

생활기록부 PDF를 텍스트로 변환하는 에이전트
Upstage Document Parse API를 사용하여 OCR 및 구조화된 텍스트 추출

Classes:
    DocumentAgent: PDF 문서 파싱 에이전트
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ParsedDocument:
    """
    파싱된 문서 결과 데이터 클래스
    
    Attributes:
        text: 추출된 전체 텍스트
        pages: 페이지별 텍스트 목록
        tables: 추출된 테이블 목록
        metadata: 문서 메타데이터
        raw_response: API 원본 응답
    """
    text: str
    pages: List[str]
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    raw_response: Dict[str, Any]


class DocumentAgent:
    """
    생활기록부 PDF 문서 파싱 에이전트
    
    PDF 문서를 업로드받아 텍스트로 변환하고,
    테이블 및 구조화된 정보를 추출하는 역할 담당
    
    Attributes:
        client: Upstage API 클라이언트
    
    Example:
        >>> from utils.upstage_client import UpstageClient
        >>> client = UpstageClient()
        >>> agent = DocumentAgent(client)
        >>> result = agent.parse("./생기부.pdf")
        >>> print(result.text)
    """
    
    def __init__(self, client):
        """
        에이전트 초기화
        
        Args:
            client: UpstageClient 인스턴스
        """
        self.client = client
    
    def parse(self, file_path: str) -> ParsedDocument:
        """
        PDF 파일을 파싱하여 텍스트 추출
        
        Args:
            file_path: PDF 파일 경로
        
        Returns:
            ParsedDocument: 파싱된 문서 결과
        
        Raises:
            FileNotFoundError: 파일이 존재하지 않을 경우
            Exception: API 호출 실패 시
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # Document Parse API 호출
        response = self.client.parse_document(file_path)
        
        return self._process_response(response)
    
    def parse_bytes(self, file_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
        """
        바이트 데이터에서 문서 파싱 (Streamlit 업로드용)
        
        Args:
            file_bytes: PDF 파일 바이트 데이터
            filename: 파일명
        
        Returns:
            ParsedDocument: 파싱된 문서 결과
        """
        # Document Parse API 호출 (바이트 버전)
        response = self.client.parse_document_bytes(file_bytes, filename)
        
        return self._process_response(response)
    
    def _process_response(self, response: Dict[str, Any]) -> ParsedDocument:
        """
        API 응답을 ParsedDocument로 변환 (내부 헬퍼)
        다양한 Upstage API 응답 구조를 모두 지원
        
        Args:
            response: API 원본 응답
        
        Returns:
            ParsedDocument: 처리된 결과
        """
        text = ""
        pages = []
        tables = []
        
        # 1. content 필드가 있는 경우 (표준 응답)
        if "content" in response:
            content = response["content"]
            
            # text 필드에서 직접 추출
            if isinstance(content, dict):
                if "text" in content:
                    text = content["text"]
                elif "html" in content:
                    # HTML에서 텍스트 추출 (태그 제거)
                    import re
                    html_content = content["html"]
                    text = re.sub(r'<[^>]+>', ' ', html_content)
                    text = re.sub(r'\s+', ' ', text).strip()
                
                # 페이지별 텍스트
                if "pages" in content:
                    for page in content["pages"]:
                        if isinstance(page, dict) and "text" in page:
                            pages.append(page["text"])
                        elif isinstance(page, str):
                            pages.append(page)
                
                # 테이블 추출
                if "tables" in content:
                    tables = content["tables"]
            elif isinstance(content, str):
                text = content
        
        # 2. text 필드가 최상위에 있는 경우
        elif "text" in response:
            text = response["text"]
        
        # 3. html 필드가 최상위에 있는 경우
        elif "html" in response:
            import re
            text = re.sub(r'<[^>]+>', ' ', response["html"])
            text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. elements 기반 응답인 경우
        elif "elements" in response:
            text_parts = []
            for element in response["elements"]:
                # 다양한 element 구조 처리
                elem_text = ""
                if "content" in element:
                    content = element["content"]
                    if isinstance(content, dict) and "text" in content:
                        elem_text = content["text"]
                    elif isinstance(content, str):
                        elem_text = content
                elif "text" in element:
                    elem_text = element["text"]
                
                if elem_text:
                    text_parts.append(elem_text)
                
                # 테이블 요소 처리
                if element.get("category") == "table":
                    tables.append(element.get("content", {}))
            
            text = "\n".join(text_parts)
        
        # 5. raw 필드가 있는 경우 (클라이언트에서 전처리된 응답)
        elif "raw" in response and "content" in response:
            content = response["content"]
            if isinstance(content, dict) and "text" in content:
                text = content["text"]
        
        # 6. 그 외의 경우 - 전체 응답을 문자열로 변환
        if not text:
            text = str(response)
        
        # 메타데이터 추출
        metadata = {
            "page_count": len(pages) if pages else 1,
            "table_count": len(tables),
            "char_count": len(text)
        }
        
        return ParsedDocument(
            text=text,
            pages=pages if pages else [text],
            tables=tables,
            metadata=metadata,
            raw_response=response
        )
    
    def extract_sections(self, parsed_doc: ParsedDocument) -> Dict[str, str]:
        """
        파싱된 문서에서 생활기록부 섹션 추출
        
        생활기록부의 주요 섹션(인적사항, 학적사항, 출결상황, 
        수상경력, 창의적체험활동, 교과학습발달상황 등)을 식별
        
        Args:
            parsed_doc: 파싱된 문서
        
        Returns:
            dict: 섹션별 텍스트 {"섹션명": "내용"}
        """
        sections = {}
        current_section = "기타"
        current_content = []
        
        # 생활기록부 주요 섹션 키워드
        section_keywords = {
            "인적사항": ["인적사항", "학생정보", "기본정보"],
            "학적사항": ["학적사항", "학적"],
            "출결상황": ["출결상황", "출결", "출석"],
            "수상경력": ["수상경력", "수상", "상훈"],
            "자격증": ["자격증", "인증"],
            "창의적체험활동상황": ["창의적체험활동", "창체", "자율활동", "동아리활동", "봉사활동", "진로활동"],
            "교과학습발달상황": ["교과학습", "성적", "학업성취"],
            "독서활동상황": ["독서활동", "독서"],
            "행동특성및종합의견": ["행동특성", "종합의견", "담임", "특기사항"]
        }
        
        # 텍스트를 줄 단위로 분석
        lines = parsed_doc.text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 새 섹션 시작 확인
            section_found = False
            for section_name, keywords in section_keywords.items():
                for keyword in keywords:
                    if keyword in line:
                        # 이전 섹션 저장
                        if current_content:
                            sections[current_section] = "\n".join(current_content)
                        
                        current_section = section_name
                        current_content = [line]
                        section_found = True
                        break
                if section_found:
                    break
            
            if not section_found:
                current_content.append(line)
        
        # 마지막 섹션 저장
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def get_summary(self, parsed_doc: ParsedDocument) -> str:
        """
        파싱된 문서의 요약 정보 반환
        
        Args:
            parsed_doc: 파싱된 문서
        
        Returns:
            str: 문서 요약 정보
        """
        return f"""📄 문서 파싱 완료
- 페이지 수: {parsed_doc.metadata['page_count']}
- 테이블 수: {parsed_doc.metadata['table_count']}
- 총 문자 수: {parsed_doc.metadata['char_count']:,}자
- 추출된 텍스트 미리보기: {parsed_doc.text[:200]}..."""
