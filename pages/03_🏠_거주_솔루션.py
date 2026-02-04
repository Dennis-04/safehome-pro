import streamlit as st
from datetime import datetime
from openai import OpenAI
from fpdf import FPDF
import os

# --------------------------------------------------------------------------
# [설정] 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="거주 솔루션 (집주인 대응)", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    .big-font { font-size: 20px !important; font-weight: bold; }
    .warning-box { background-color: #fff4f4; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .success-box { background-color: #f0f7ff; padding: 15px; border-radius: 10px; border-left: 5px solid #3182f6; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 거주 중 문제 해결사")
st.caption("집주인에게 할 말이 있으신가요? AI가 상황에 맞는 '카톡 멘트'와 '법적 내용증명'을 작성해드립니다.")

# --------------------------------------------------------------------------
# [함수 1] GPT로 텍스트 생성 (카톡용 / 내용증명용)
# --------------------------------------------------------------------------
def generate_text(prompt_type, details):
    # Load API key from Streamlit secrets in a safe way
    api_key = st.secrets.get("openai", {}).get("api_key")
    if not api_key:
        st.error("OpenAI API key is not configured. Add it to your secrets.toml as:\n[openai]\napi_key = \"YOUR_KEY\"")
        st.stop()
    client = OpenAI(api_key=api_key)
    
    if prompt_type == "kakao":
        system_role = "당신은 예의 바르지만 할 말은 확실하게 하는 세입자입니다. 집주인에게 보낼 카카오톡 메시지를 작성하세요. 감정적이지 않고 사실 위주로 작성하세요."
    else:
        system_role = "당신은 20년 경력의 부동산 전문 변호사입니다. 세입자를 대리하여 집주인에게 보낼 '내용증명(Certification of Contents)' 본문을 작성하세요. 법적 용어(민법 임대차보호법 등)를 적절히 인용하여 강력하고 논리적으로 작성하세요. 서론/본론/결론 형식을 갖추세요."

    response = client.chat.completions.create(
        model="gpt-4o-mini", # 가성비 모델
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": f"상황: {details}"}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

# --------------------------------------------------------------------------
# [함수 2] PDF 내용증명 생성 (한글 폰트 필수)
# --------------------------------------------------------------------------
def create_legal_pdf(sender, receiver, address, title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 설정 (나눔고딕)
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('NanumGothic', '', font_path, uni=True)
        pdf.set_font('NanumGothic', '', 12)
    else:
        st.error("폰트 파일(NanumGothic.ttf)이 없습니다. 기본 폰트로 대체됩니다(한글 깨짐 주의).")
        pdf.set_font('Arial', '', 12)

    # 제목
    pdf.set_font_size(24)
    pdf.cell(0, 20, "내 용 증 명 서", 0, 1, 'C')
    pdf.ln(10)
    
    # 발신인/수신인 정보
    pdf.set_font_size(12)
    pdf.cell(0, 10, f"수 신 인: {receiver}", 0, 1)
    pdf.cell(0, 10, f"주 소: {address} (임대차 목적물)", 0, 1)
    pdf.ln(5)
    pdf.cell(0, 10, f"발 신 인: {sender}", 0, 1)
    pdf.ln(10)
    
    # 제목
    pdf.set_font_size(14)
    pdf.cell(0, 10, f"제 목: {title}", 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # 밑줄
    pdf.ln(10)
    
    # 본문
    pdf.set_font_size(11)
    pdf.multi_cell(0, 8, content)
    
    # 날짜 및 서명
    pdf.ln(20)
    pdf.cell(0, 10, datetime.now().strftime("%Y년 %m월 %d일"), 0, 1, 'C')
    pdf.cell(0, 10, f"발신인 {sender} (인)", 0, 1, 'C')
    
    return bytes(pdf.output())

# --------------------------------------------------------------------------
# [UI] 입력 폼
# --------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 상황 입력")
    issue_type = st.selectbox("어떤 문제가 있나요?", 
                             ["수리 요청 (누수/파손)", "보증금 반환 요청", "계약 갱신 거절 통보", "소음/생활 불편", "기타 직접 입력"])
    
    if issue_type == "기타 직접 입력":
        issue_detail = st.text_area("구체적인 상황을 적어주세요.", height=150)
    else:
        # 상황별 템플릿 질문
        if "수리" in issue_type:
            detail_q = "어디가 고장 났나요? 언제부터 그랬나요? (예: 안방 천장 누수, 3일 전부터)"
        elif "보증금" in issue_type:
            detail_q = "계약 만기일은 언제인가요? 얼마를 돌려받아야 하나요?"
        else:
            detail_q = "구체적인 내용을 적어주세요."
            
        issue_detail = st.text_area(detail_q, height=150)
    
    st.divider()
    
    st.subheader("2. 기본 정보 (내용증명용)")
    with st.expander("내용증명 작성 시에만 필요합니다 (클릭)", expanded=False):
        sender_name = st.text_input("내 이름 (발신인)")
        receiver_name = st.text_input("집주인 이름 (수신인)")
        address_info = st.text_input("현재 살고 있는 집 주소")

# --------------------------------------------------------------------------
# [Action] 생성 버튼
# --------------------------------------------------------------------------
with col2:
    st.subheader("3. AI 솔루션 생성")
    st.info("버튼을 누르면 AI가 두 가지 버전의 텍스트를 작성합니다.")
    
    if st.button("🚀 솔루션 생성하기", type="primary", use_container_width=True):
        if not issue_detail:
            st.warning("상황을 입력해주세요!")
        else:
            with st.spinner("변호사 AI가 문구를 작성 중입니다..."):
                # 1. 카톡용 멘트 생성
                kakao_msg = generate_text("kakao", f"{issue_type}, 상세내용: {issue_detail}")
                
                # 2. 내용증명 본문 생성
                legal_content = generate_text("legal", f"{issue_type}, 상세내용: {issue_detail}")
                
                # 결과 저장
                st.session_state['kakao_res'] = kakao_msg
                st.session_state['legal_res'] = legal_content
                st.session_state['generated'] = True

# --------------------------------------------------------------------------
# [Result] 결과 화면
# --------------------------------------------------------------------------
if st.session_state.get('generated'):
    st.divider()
    
    # 탭으로 구분해서 보여주기
    tab1, tab2 = st.tabs(["💬 정중한 카톡 (1단계)", "⚖️ 강력한 내용증명 (2단계)"])
    
    with tab1:
        st.markdown('<div class="success-box"><b>💡 Tip:</b> 먼저 이 메시지로 가볍게 대화를 시도해보세요.</div>', unsafe_allow_html=True)
        st.write("")
        st.text_area("복사해서 사용하세요", value=st.session_state['kakao_res'], height=200)
        
    with tab2:
        st.markdown('<div class="warning-box"><b>🚨 주의:</b> 말이 통하지 않을 때 최후의 수단으로 보내세요. 우체국에 가져가면 법적 효력이 발생합니다.</div>', unsafe_allow_html=True)
        st.write("")
        st.text_area("내용증명 본문 미리보기", value=st.session_state['legal_res'], height=300)
        
        # PDF 다운로드 버튼
        if sender_name and receiver_name and address_info:
            pdf_bytes = create_legal_pdf(sender_name, receiver_name, address_info, f"{issue_type} 관련의 건", st.session_state['legal_res'])
            
            st.download_button(
                label="📄 내용증명 PDF 다운로드 (제출용)",
                data=pdf_bytes,
                file_name="내용증명서.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("👈 왼쪽의 '기본 정보'를 모두 입력해야 PDF를 다운로드할 수 있습니다.")