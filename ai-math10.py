import streamlit as st
from google import genai
from google.genai import types
import os

# 1. API 키 설정 (Streamlit Secrets / 환경변수 / 사이드바 입력)
st.sidebar.title("🔑 설정")


def normalize_api_key(value):
    return value.strip() if isinstance(value, str) else ""


api_key = ""

# Streamlit Secrets에서 API 키 우선 읽기
try:
    api_key = normalize_api_key(st.secrets["api_keys"].get("GEMINI_API_KEY", ""))
except Exception:
    api_key = ""

# 환경변수 fallback
if not api_key:
    api_key = normalize_api_key(os.getenv("GEMINI_API_KEY", ""))

# API 키가 없으면 사이드바에서 직접 입력받기
if not api_key:
    api_key = normalize_api_key(
        st.sidebar.text_input(
            "Gemini API Key를 입력하세요",
            type="password",
            key="gemini_api_key"
        )
    )

# 2. 클라이언트 초기화 함수
def get_gemini_client(api_key):
    if not api_key:
        st.warning("왼쪽 사이드바에 Gemini API Key를 입력해주세요.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(
            "API 키가 올바르지 않습니다. Gemini AI Studio에서 복사한 키를 사용했는지, 앞뒤 공백이 없는지 확인해주세요."
        )
        st.caption(f"상세 오류: {e}")
        return None

# 3. 메인 화면 UI
st.title("📐 중고등 수학 문제 생성기 by Kevin")
st.write("학년과 단원을 선택하면 Gemini가 맞춤형 문제와 풀이를 만들어줍니다.")

# 사용자 선택 항목
school_level = st.selectbox("학교 급", ["중학교", "고등학교"])

if school_level == "중학교":
    grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
    topic = st.text_input("단원/주제 (예: 일차방정식, 피타고라스 정리)", "일차방정식")
else:
    grade = st.selectbox("학년", ["1학년(공통수학)", "2학년(수학I/II)", "3학년(선택과목)"])
    topic = st.text_input("단원/주제 (예: 지수함수, 미분계수, 확률과 통계)", "지수함수")

difficulty = st.select_slider("난이도", options=["하", "중", "상", "최상"])

# 문제 생성 버튼
if st.button("🚀 수학 문제 생성하기"):
    if not api_key:
        st.warning("왼쪽 사이드바에 Gemini API Key를 입력해주세요.")
    else:
        client = get_gemini_client(api_key)
        if client:
            with st.spinner("Gemini가 열심히 문제를 출제하고 있습니다..."):
                
                # Gemini에게 보낼 프롬프트 엔지니어링
                prompt = f"""
                너는 대한민국 중고등학교 수학 교사야. 
                다음 조건에 맞는 수학 문제 1개와 정답, 그리고 상세한 풀이 과정을 만들어줘.

                [조건]
                - 학교급 및 학년: {school_level} {grade}
                - 단원/주제: {topic}
                - 난이도: {difficulty}

                [출력 형식 가이드]
                - 수학 기호나 수식은 반드시 Streamlit에서 렌더링 가능한 LaTeX 형식(예: $x^2 + 2x = 0$)으로 감싸서 작성해줘.
                - 분리된 수식은 $$ 수식 $$ 형태를 사용해줘.
                - 구조는 크게 '### [문제]', '### [정답]', '### [상세 풀이]'로 나누어 가독성 있게 작성해줘.
                """

                try:
                    # Gemini 2.5 Flash 모델 사용 (빠르고 비용 효율적)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    # 결과 출력
                    st.success("문제 생성 완료!")
                    st.markdown("---")
                    content = response.text
                    st.markdown(content)

                    # 파일 형식 선택 및 저장
                    from datetime import datetime
                    from reportlab.lib.pagesizes import letter, A4
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib.units import inch
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                    from reportlab.lib.enums import TA_LEFT, TA_CENTER
                    import re
                    
                    st.markdown("### 📁 파일 저장하기")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        file_format = st.selectbox("파일 형식 선택", 
                            ["📊 PDF (권장)", "📄 Markdown (.md)", "📜 텍스트 (.txt)"])
                    
                    base_fname = f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    if "PDF" in file_format:
                        ext, mime = ".pdf", "application/pdf"
                        
                        # PDF 생성 함수
                        from io import BytesIO
                        pdf_buffer = BytesIO()
                        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        # 제목 스타일
                        title_style = ParagraphStyle(
                            'CustomTitle',
                            parent=styles['Heading1'],
                            fontSize=16,
                            textColor='#2c3e50',
                            spaceAfter=12,
                            alignment=TA_CENTER
                        )
                        
                        # 내용 스타일 (LaTeX 수식을 그대로 표시)
                        content_style = ParagraphStyle(
                            'CustomBody',
                            parent=styles['BodyText'],
                            fontSize=11,
                            leading=14,
                            spaceAfter=10,
                            alignment=TA_LEFT,
                            fontName='Helvetica'
                        )
                        
                        # 마크다운을 간단한 텍스트로 변환 (수식 보존)
                        lines = content.split('\n')
                        for line in lines:
                            if line.startswith('### '):
                                # 섹션 제목
                                title_text = line.replace('### ', '').strip()
                                story.append(Paragraph(f"<b>{title_text}</b>", title_style))
                                story.append(Spacer(1, 0.2*inch))
                            elif line.strip():
                                # 일반 텍스트 (수식 포함)
                                story.append(Paragraph(line.strip(), content_style))
                                story.append(Spacer(1, 0.1*inch))
                        
                        doc.build(story)
                        save_content = pdf_buffer.getvalue()
                        
                    elif "Markdown" in file_format:
                        ext, mime = ".md", "text/markdown"
                        save_content = content
                    else:
                        ext, mime = ".txt", "text/plain"
                        save_content = content
                    
                    filename = base_fname + ext
                    
                    # 다운로드 버튼 (브라우저)
                    st.download_button(
                        label=f"📥 {file_format} 다운로드", 
                        data=save_content, 
                        file_name=filename, 
                        mime=mime,
                        key="download_btn"
                    )
                    
                    # 서버 저장 섹션
                    col1, col2 = st.columns(2)
                    with col1:
                        custom_folder = st.text_input("저장 폴더 (기본값: 현재 디렉터리)", value=os.getcwd())
                    
                    if st.button("💾 서버에 저장", key="save_btn"):
                        save_dir = custom_folder if os.path.isdir(custom_folder) else os.getcwd()
                        save_path = os.path.join(save_dir, filename)
                        
                        try:
                            # 폴더가 없으면 생성
                            os.makedirs(save_dir, exist_ok=True)
                            
                            # PDF는 바이너리, 나머지는 텍스트 모드
                            if isinstance(save_content, bytes):
                                with open(save_path, "wb") as f:
                                    f.write(save_content)
                            else:
                                with open(save_path, "w", encoding="utf-8") as f:
                                    f.write(save_content)
                            
                            st.success(f"✅ 파일 저장 완료!")
                            st.info(f"📍 **저장 위치**: {save_path}")
                            
                            # 폴더 열기 버튼 (Windows)
                            if st.button("📂 폴더 열기"):
                                try:
                                    os.startfile(save_dir)  # Windows 전용
                                except Exception:
                                    st.warning("폴더를 열 수 없습니다. 수동으로 확인하세요.")
                        except Exception as e:
                            st.error(f"❌ 파일 저장 실패: {e}")

                except Exception as e:
                    st.error(f"문제 생성 중 오류가 발생했습니다: {e}")