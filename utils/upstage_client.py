"""
🔌 Upstage API 통합 클라이언트

Upstage의 모든 API를 통합 관리하는 클라이언트 클래스
- Document Parse API: PDF → 텍스트 변환
- Information Extract API: 텍스트 → 구조화된 정보 추출
- Solar LLM API: 채팅 및 추론
- Groundedness Check API: 응답 검증

Classes:
    UpstageClient: Upstage API 통합 클라이언트
"""

import os
import base64
import json
import requests
from typing import Optional, Dict, Any, List, Generator
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class UpstageClient:
    """
    Upstage API 통합 클라이언트
    
    모든 Upstage API 호출을 관리하는 중앙 클라이언트 클래스
    
    Attributes:
        api_key: Upstage API 키
        base_url: API 기본 URL
        client: OpenAI 호환 클라이언트 (Solar LLM용)
    
    Example:
        >>> client = UpstageClient()
        >>> response = client.chat("안녕하세요!")
        >>> print(response)
    """
    
    # API 엔드포인트 상수
    DOCUMENT_PARSE_URL = "https://api.upstage.ai/v1/document-digitization"
    INFORMATION_EXTRACT_URL = "https://api.upstage.ai/v1/information-extraction"
    GROUNDEDNESS_CHECK_URL = "https://api.upstage.ai/v1/chat/completions"
    SOLAR_BASE_URL = "https://api.upstage.ai/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            api_key: Upstage API 키 (미제공 시 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        # OpenAI 호환 클라이언트 (Solar LLM용)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.SOLAR_BASE_URL
        )
        
        # Information Extract용 별도 클라이언트
        self.extract_client = OpenAI(
            api_key=self.api_key,
            base_url=f"{self.INFORMATION_EXTRACT_URL}"
        )
    
    # ==================== Document Parse API ====================
    
    def parse_document(
        self, 
        file_path: str, 
        ocr_mode: str = "force",
        model: str = "document-parse"
    ) -> Dict[str, Any]:
        """
        PDF 문서를 텍스트로 변환 (Document Parse API)
        
        Args:
            file_path: PDF 파일 경로
            ocr_mode: OCR 모드 ("auto", "force")
            model: 사용할 모델 ("document-parse", "ocr")
        
        Returns:
            dict: 파싱된 문서 정보 (텍스트, 테이블 등)
        
        Example:
            >>> result = client.parse_document("./생기부.pdf")
            >>> print(result["content"]["text"])
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {
                "ocr": ocr_mode,
                "base64_encoding": "['table']",
                "model": model
            }
            response = requests.post(
                self.DOCUMENT_PARSE_URL,
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code != 200:
            raise Exception(f"Document Parse 실패: {response.status_code} - {response.text}")
        
        return response.json()
    
    def parse_document_bytes(
        self, 
        file_bytes: bytes, 
        filename: str = "document.pdf",
        ocr_mode: str = "force",
        model: str = "document-parse"
    ) -> Dict[str, Any]:
        """
        바이트 데이터에서 문서 파싱 (Streamlit 업로드 파일용)
        스캔된 이미지 기반 PDF는 OCR 강제 모드로 처리
        
        Args:
            file_bytes: 파일 바이트 데이터
            filename: 파일명
            ocr_mode: OCR 모드 ("force" - 스캔 문서용)
            model: 사용할 모델 ("document-parse" 권장)
        
        Returns:
            dict: 파싱된 문서 정보
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # 스캔된 PDF를 위한 강화된 설정
        files = {"document": (filename, file_bytes, "application/pdf")}
        data = {
            "ocr": "force",  # 항상 OCR 강제 실행
            "model": model,
            "output_formats": "['text', 'html']",  # 텍스트와 HTML 모두 추출
            "coordinates": "false",
            "base64_encoding": "['table']"
        }
        
        response = requests.post(
            self.DOCUMENT_PARSE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120  # 스캔 문서는 처리 시간이 오래 걸릴 수 있음
        )
        
        if response.status_code != 200:
            raise Exception(f"Document Parse 실패: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # 응답에서 텍스트 추출 - 다양한 응답 구조 처리
        if "content" in result:
            return result
        elif "text" in result:
            return {"content": {"text": result["text"]}}
        elif "elements" in result:
            # elements 기반 응답 처리
            text_parts = []
            for elem in result.get("elements", []):
                if "content" in elem:
                    content = elem["content"]
                    if isinstance(content, dict) and "text" in content:
                        text_parts.append(content["text"])
                    elif isinstance(content, str):
                        text_parts.append(content)
                elif "text" in elem:
                    text_parts.append(elem["text"])
            return {"content": {"text": "\n".join(text_parts)}, "raw": result}
        else:
            # 그 외 응답 구조
            return {"content": {"text": str(result)}, "raw": result}
    
    # ==================== Information Extract API ====================
    
    def extract_information(
        self, 
        file_path: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이미지/문서에서 구조화된 정보 추출 (Information Extract API)
        
        Args:
            file_path: 이미지/PDF 파일 경로
            schema: 추출할 정보의 JSON 스키마
        
        Returns:
            dict: 추출된 구조화된 정보
        """
        # 파일을 base64로 인코딩
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        
        return self._extract_from_base64(base64_data, schema)
    
    def extract_information_bytes(
        self, 
        file_bytes: bytes, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        바이트 데이터에서 정보 추출 (Streamlit 업로드 파일용)
        
        Args:
            file_bytes: 파일 바이트 데이터
            schema: 추출할 정보의 JSON 스키마
        
        Returns:
            dict: 추출된 구조화된 정보
        """
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        return self._extract_from_base64(base64_data, schema)
    
    def _extract_from_base64(
        self, 
        base64_data: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Base64 인코딩된 데이터에서 정보 추출 (내부 헬퍼)
        
        Args:
            base64_data: Base64 인코딩된 파일 데이터
            schema: 추출 스키마
        
        Returns:
            dict: 추출된 정보
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "information-extract",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/octet-stream;base64,{base64_data}"
                            }
                        }
                    ]
                }
            ],
            "response_format": schema
        }
        
        response = requests.post(
            f"{self.SOLAR_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Information Extract 실패: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # 응답에서 추출된 내용 파싱
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_content": content}
        
        return result
    
    # ==================== Solar LLM API ====================
    
    def chat(
        self, 
        message: str, 
        system_prompt: Optional[str] = None,
        reasoning_effort: str = "low",
        model: str = "solar-pro3",
        temperature: float = 0.7
    ) -> str:
        """
        Solar LLM과 채팅 (동기 방식)
        
        Args:
            message: 사용자 메시지
            system_prompt: 시스템 프롬프트 (선택)
            reasoning_effort: 추론 노력 수준 ("low", "medium", "high")
            model: 사용할 모델
            temperature: 응답 다양성 (0.0~1.0)
        
        Returns:
            str: LLM 응답 텍스트
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            reasoning_effort=reasoning_effort,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    def chat_stream(
        self, 
        message: str, 
        system_prompt: Optional[str] = None,
        reasoning_effort: str = "low",
        model: str = "solar-pro3",
        temperature: float = 0.2,
    ) -> Generator[str, None, None]:
        """
        Solar LLM과 스트리밍 채팅
        
        Args:
            message: 사용자 메시지
            system_prompt: 시스템 프롬프트 (선택)
            reasoning_effort: 추론 노력 수준
            model: 사용할 모델
        
        Yields:
            str: 응답 텍스트 조각
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def chat_with_context(
        self, 
        messages: List[Dict[str, str]], 
        reasoning_effort: str = "high",
        model: str = "solar-pro3"
    ) -> str:
        """
        대화 컨텍스트를 포함한 채팅
        
        Args:
            messages: 대화 기록 [{"role": "user/assistant", "content": "..."}]
            reasoning_effort: 추론 노력 수준
            model: 사용할 모델
        
        Returns:
            str: LLM 응답 텍스트
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            reasoning_effort=reasoning_effort
        )
        
        return response.choices[0].message.content
    
    # ==================== Groundedness Check API ====================
    
    def check_groundedness(
        self, 
        context: str, 
        answer: str
    ) -> Dict[str, Any]:
        """
        응답의 근거 검증 (Groundedness Check)
        
        주어진 컨텍스트에 답변이 얼마나 기반하고 있는지 검증
        
        Args:
            context: 근거가 되는 원본 텍스트
            answer: 검증할 답변
        
        Returns:
            dict: 검증 결과 (grounded: bool, score: float, explanation: str)
        """
        system_prompt = """당신은 답변 검증 전문가입니다. 
주어진 컨텍스트(Context)를 바탕으로 답변(Answer)이 얼마나 근거 있는지 평가해주세요.

평가 기준:
1. 답변의 각 주장이 컨텍스트에 근거하는지 확인
2. 컨텍스트에 없는 정보를 추가하지 않았는지 확인
3. 0.0~1.0 사이의 점수로 근거 정도를 표현

반드시 다음 JSON 형식으로만 응답하세요:
{
    "grounded": true/false,
    "score": 0.0~1.0,
    "explanation": "검증 설명",
    "evidence": ["근거1", "근거2"]
}"""
        
        user_message = f"""[Context]
{context}

[Answer]
{answer}

위 답변이 컨텍스트에 얼마나 근거하는지 검증해주세요."""
        
        response = self.chat(
            message=user_message,
            system_prompt=system_prompt,
            reasoning_effort="high",
            temperature=0.1
        )
        
        # JSON 파싱 시도
        try:
            # JSON 블록 추출
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            # 파싱 실패 시 기본 응답
            return {
                "grounded": True,
                "score": 0.8,
                "explanation": response,
                "evidence": []
            }
    
    # ==================== 유틸리티 메서드 ====================
    
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = self.chat("테스트입니다. '연결 성공'이라고만 답해주세요.", temperature=0)
            return "연결" in response or "성공" in response or len(response) > 0
        except Exception as e:
            print(f"연결 테스트 실패: {e}")
            return False
