import streamlit as st
from datetime import datetime
from openai import OpenAI
from fpdf import FPDF
import os
import time

# --------------------------------------------------------------------------
# [설정] 페이지 설정 & 커스텀 스타일(CSS)
# --------------------------------------------------------------------------
st.set_page_config(page_title="거주 솔루션 (집주인 대응)", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    /* 전체 폰트 및 배경 설정 */
    .main { background-color: #FAFAFA; }
    
    /* 제목 스타일 */
    h1 { color: #1E3A8A; font-family: 'Helvetica', sans-serif; font-weight: 800; }
    h3 { color: #333333; }
    
    /* 커스텀 박스 스타일 */
    .info-box { 
        background-color: #EBF8FF; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 6px solid #2B6CB0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .warning-box { 
        background-color: #FFF5F5; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 6px solid #C53030;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #F0FFF4;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #2F855A;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [Header] 제목 및 소개
# --------------------------------------------------------------------------
st.title("⚖️ 거주 법률 솔루션 AI")
st.markdown("""
<div class="info-box">
    <b>👨‍⚖️ AI 변호사가 도와드립니다.</b><br>
    집주인과의 갈등, 감정적으로 대응하지 마세요.<br>
    상황만 입력하면 <b>'정중한 카톡'</b>부터 법적 효력이 있는 <b>'강력한 내용증명'</b>까지 원스톱으로 작성해 드립니다.
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [Logic] 기능 함수들
# --------------------------------------------------------------------------
def generate_text(prompt_type, details):
    api_key = st.secrets.get("openai", {}).get("api_key")
    if not api_key:
        st.error("🚨 OpenAI API 키가 설정되지 않았습니다.")
        st.stop()
    client = OpenAI(api_key=api_key)
    
    if prompt_type == "kakao":
        system_role = "당신은 예의 바르지만 논리적인 세입자입니다. 집주인에게 보낼 카카오톡 메시지를 작성하세요. 감정적이지 않고, 요청사항을 명확하게 전달하세요. (이모티콘을 적절히 1~2개 사용)"
    else:
        system_role = "당신은 20년 경력의 부동산 전문 변호사입니다. 세입자를 대리하여 집주인에게 보낼 '내용증명(Certification of Contents)' 본문을 작성하세요. 민법 및 임대차보호법 조항을 언급하며 논리적이고 단호하게 작성하세요. 서론-본론-결론 형식을 갖추세요."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": f"상황: {details}"}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def create_legal_pdf(sender, receiver, address, title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 경로 탐색
    current_file_path = os.path.abspath(__file__)
    pages_dir = os.path.dirname(current_file_path)
    root_dir = os.path.dirname(pages_dir)
    font_path = os.path.join(root_dir, "NanumGothic.ttf")

    if os.path.exists(font_path):
        pdf.add_font('NanumGothic', '', font_path, uni=True)
        pdf.set_font('NanumGothic', '', 12)
    else:
        font_path_backup = os.path.join(pages_dir, "NanumGothic.ttf")
        if os.path.exists(font_path_backup):
            pdf.add_font('NanumGothic', '', font_path_backup, uni=True)
            pdf.set_font('NanumGothic', '', 12)
        else:
            st.error("폰트 파일을 찾을 수 없습니다.")
            return None

    # 문서 작성
    pdf.set_font_size(22)
    pdf.cell(0, 20, "내 용 증 명 서", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font_size(11)
    pdf.cell(0, 8, f"수 신 인: {receiver}", 0, 1)
    pdf.cell(0, 8, f"주 소: {address}", 0, 1)
    pdf.ln(2)
    pdf.cell(0, 8, f"발 신 인: {sender}", 0, 1)
    pdf.ln(10)
    
    pdf.set_font_size(14)
    pdf.cell(0, 10, f"제 목: {title}", 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font_size(11)
    pdf.multi_cell(0, 7, content)
    
    pdf.ln(20)
    pdf.cell(0, 10, datetime.now().strftime("%Y년 %m월 %d일"), 0, 1, 'C')
    pdf.cell(0, 10, f"발신인: {sender} (인)", 0, 1, 'C')
    
    return bytes(pdf.output())

# --------------------------------------------------------------------------
# [UI] 입력 섹션 (2단 레이아웃)
# --------------------------------------------------------------------------
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("📝 1. 상황 정보 입력")
    
    with st.container(border=True):
        issue_type = st.selectbox(
            "발생한 문제 유형", 
            ["수리 요청 (누수/파손)", "보증금 반환 요청", "계약 갱신 거절 통보", "층간소음/생활 불편", "기타"]
        )
        
        detail_placeholder = "구체적인 상황을 입력해주세요. (예: 안방 천장에서 물이 새서 벽지가 젖었습니다. 3일 전에 집주인에게 알렸으나 답이 없습니다.)"
        issue_detail = st.text_area("상세 내용", height=150, placeholder=detail_placeholder)
        
    st.write("") # 여백
    st.subheader("👤 2. 내용증명 정보 (선택)")
    with st.expander("PDF 생성 시 필요한 정보 입력하기"):
        st.info("카톡 멘트만 필요하다면 입력하지 않으셔도 됩니다.")
        sender_name = st.text_input("내 이름 (임차인)")
        receiver_name = st.text_input("집주인 이름 (임대인)")
        address_info = st.text_input("부동산 주소")

with col2:
    st.subheader("💡 3. 솔루션 생성")
    
    if st.button("🚀 AI 변호사에게 의뢰하기 (클릭)", type="primary", use_container_width=True):
        if not issue_detail:
            st.toast("⚠️ 내용을 입력해주세요!", icon="🚨")
        else:
            with st.status("🔍 AI가 법률 검토를 진행 중입니다...", expanded=True) as status:
                time.sleep(1)
                st.write("📝 상황을 분석하고 있습니다...")
                kakao_msg = generate_text("kakao", f"{issue_type}, {issue_detail}")
                
                time.sleep(1)
                st.write("⚖️ 판례 및 법률 조항을 검색 중입니다...")
                legal_content = generate_text("legal", f"{issue_type}, {issue_detail}")
                
                status.update(label="✅ 솔루션 생성이 완료되었습니다!", state="complete", expanded=False)
                
                st.session_state['kakao_res'] = kakao_msg
                st.session_state['legal_res'] = legal_content
                st.session_state['generated'] = True

    # 결과 표시 영역
    if st.session_state.get('generated'):
        st.divider()
        
        tab1, tab2 = st.tabs(["💬 부드러운 카톡 해결", "⚔️ 강경한 내용증명 발송"])
        
        with tab1:
            st.markdown('<div class="success-box"><b>Tip:</b> 감정을 배제하고 사실만 전달하는 것이 핵심입니다. 아래 내용을 복사해서 사용하세요.</div>', unsafe_allow_html=True)
            st.text_area("카톡 초안", value=st.session_state['kakao_res'], height=250)
            
        with tab2:
            st.markdown('<div class="warning-box"><b>주의:</b> 이 문서는 법적 효력을 갖기 위한 전 단계입니다. 상대방이 계속 무대응일 때 사용하세요.</div>', unsafe_allow_html=True)
            st.text_area("내용증명 초안", value=st.session_state['legal_res'], height=350)
            
            # PDF 다운로드
            if sender_name and receiver_name and address_info:
                pdf_bytes = create_legal_pdf(sender_name, receiver_name, address_info, f"{issue_type} 관련의 건", st.session_state['legal_res'])
                if pdf_bytes:
                    st.download_button(
                        label="📄 정식 내용증명 PDF 다운로드",
                        data=pdf_bytes,
                        file_name="내용증명서_최종.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            else:
                st.warning("👉 PDF를 다운로드하려면 왼쪽의 [내용증명 정보]를 모두 입력해주세요.")