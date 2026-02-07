import streamlit as st
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import tempfile
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------------
# [설정] 페이지 기본 설정 & 3D HUD 스타일 (CSS Magic)
# --------------------------------------------------------------------------
st.set_page_config(page_title="SafeHome 3D - Room Scan", page_icon="📸", layout="wide")

st.markdown("""
<style>
    /* 1. 배경 및 기본 폰트 설정 */
    .stApp { 
        font-family: 'Pretendard', sans-serif; 
        background: transparent !important; 
    }
    header, footer { visibility: hidden !important; }

    /* Spline 3D 배경 */
    #spline-bg {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; border: none;
    }

    /* 컨텐츠 영역 중앙 정렬 */
    .block-container {
        position: relative; z-index: 1; padding-top: 5vh; max-width: 1000px;
    }

    /* 2. Glassmorphism 카드 (HUD 스타일) */
    .glass-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(56, 189, 248, 0.3); /* Cyan border */
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }

    /* 3. 텍스트 스타일링 */
    h1, h2, h3 { color: white !important; text-shadow: 0 0 10px rgba(56, 189, 248, 0.8); }
    .header-desc { color: #94a3b8; font-size: 16px; margin-bottom: 20px; }
    
    /* 섹터 제목 (Scanning Areas) */
    .sector-title {
        font-size: 18px;
        font-weight: bold;
        color: #38bdf8; /* Sky Blue */
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.3);
        padding-bottom: 5px;
    }

    /* 4. 탭 스타일 커스텀 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0,0,0,0.5);
        padding: 10px 10px 0 10px;
        border-radius: 10px 10px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: bold;
    }

    /* 5. 버튼 스타일 (네온 효과) */
    div.stButton > button {
        background: rgba(56, 189, 248, 0.1) !important;
        border: 1px solid #38bdf8 !important;
        color: #38bdf8 !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        background: #38bdf8 !important;
        color: black !important;
        box-shadow: 0 0 20px #38bdf8 !important;
    }
    
    /* 팁 박스 (HUD Info) */
    .hud-info {
        border-left: 3px solid #facc15; /* Yellow */
        background: rgba(250, 204, 21, 0.1);
        padding: 15px;
        color: #e2e8f0;
        font-size: 14px;
        border-radius: 0 10px 10px 0;
    }
</style>

<iframe id="spline-bg" src='https://my.spline.design/r4xbot-x144J8ISm6Am5vnam9xXxwah/' frameborder='0'></iframe>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# [함수 1~4] 기존 로직 그대로 유지 (건드리지 않음)
# --------------------------------------------------------------------------
def add_watermark(image_file, text):
    try:
        image = Image.open(image_file)
        draw = ImageDraw.Draw(image)
        width, height = image.size
        font_size = int(height * 0.04)
        try:
            font = ImageFont.truetype("NanumGothic.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        text_width = font_size * len(text) * 0.6
        x = width - text_width - (width * 0.05)
        y = height - font_size - (height * 0.05)
        
        stroke_width = 2
        draw.text((x, y), text, font=font, fill="white", stroke_width=stroke_width, stroke_fill="black")
        return image
    except Exception as e:
        st.error(f"Image Error: {e}")
        return None

def create_pdf(image_list):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(0)
        for img in image_list:
            pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                img_rgb = img.convert('RGB')
                img_rgb.save(tmp_file.name, "JPEG", quality=85)
                pdf.image(tmp_file.name, x=10, y=10, w=190)
            os.unlink(tmp_file.name)
        return bytes(pdf.output())
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

def send_email(to_email, pdf_bytes, filename):
    try:
        smtp_info = st.secrets["smtp"]
        my_email = smtp_info["EMAIL_ADDRESS"]
        my_password = smtp_info["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"[SafeHome] R4X Protocol Report ({datetime.now().strftime('%Y-%m-%d')})"
        msg['From'] = my_email
        msg['To'] = to_email
        
        body = f"""
        System Notification: SafeHome R4X
        
        요청하신 '공간 기록 리포트(Time Capsule)' 생성이 완료되었습니다.
        첨부된 PDF 파일은 추후 분쟁 시 강력한 증거 자료로 활용됩니다.
        
        - Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - Status: Secured
        
        SafeHome AI Team
        """
        msg.attach(MIMEText(body, 'plain'))
        part = MIMEApplication(pdf_bytes, Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(my_email, my_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

def save_to_sheet(email, expiry_date):
    try:
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            st.error("❌ System Error: Secrets configuration missing")
            return False

        credentials_info = st.secrets["connections"]["gsheets"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # [중요] 파트너님의 구글 시트 ID를 여기에 다시 넣어주세요!
        sheet_id = "1TZYPOaiI87gR_BRyTCZQedvPtmMzF7p-JdmIlKGeh_s" # <--- 여기에 아까 쓰시던 ID를 입력하세요
        
        sheet = client.open_by_key(sheet_id).sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, email, str(expiry_date), "SECURED"])
        return True
    except Exception as e:
        st.warning(f"⚠️ Cloud Sync Error: {e}")
        return False

# --------------------------------------------------------------------------
# [UI] 메인 화면 구성 (R4X HUD Interface)
# --------------------------------------------------------------------------
st.markdown("""
<div class="glass-card" style="border-left: 5px solid #00f2ff;">
    <h1 style="margin:0; font-size:32px;">📸 R4X ROOM SCANNER</h1>
    <p class="header-desc" style="margin:5px 0 0 0;">
        "로봇과 함께 방의 상태를 스캔하여 타임캡슐에 저장합니다."
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="glass-card" style="padding:15px; background:rgba(0,0,0,0.5);">
        <span style="color:#38bdf8; font-weight:bold;">🟢 SYSTEM READY</span><br>
        모든 섹터의 사진을 업로드한 후 <b>[INITIATE PROTOCOL]</b> 버튼을 눌러주세요.
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="hud-info">
        <b>🎯 TARGET OBJECTS</b><br>
        • 바닥 찍힘/변색<br>
        • 벽지 찢어짐/낙서<br>
        • 옵션 가구 파손 흔적
    </div>
    """, unsafe_allow_html=True)

# 탭 구성 (System Modules)
tabs = st.tabs(["SECTOR A: 거실/방", "SECTOR B: 주방", "SECTOR C: 화장실", "SECTOR D: 기타"])
uploaded_photos = {}

# 각 탭 내부를 Glass Card로 감싸기
with tabs[0]:
    st.markdown('<div class="sector-title">📡 SCANNING LIVING AREA</div>', unsafe_allow_html=True)
    uploaded_photos['room'] = st.file_uploader("증거 사진 투입 (Drop Files)", type=['jpg', 'png'], accept_multiple_files=True, key="u1")

with tabs[1]:
    st.markdown('<div class="sector-title">📡 SCANNING KITCHEN AREA</div>', unsafe_allow_html=True)
    uploaded_photos['kitchen'] = st.file_uploader("증거 사진 투입 (Drop Files)", type=['jpg', 'png'], accept_multiple_files=True, key="u2")

with tabs[2]:
    st.markdown('<div class="sector-title">📡 SCANNING BATHROOM</div>', unsafe_allow_html=True)
    uploaded_photos['bath'] = st.file_uploader("증거 사진 투입 (Drop Files)", type=['jpg', 'png'], accept_multiple_files=True, key="u3")

with tabs[3]:
    st.markdown('<div class="sector-title">📡 SCANNING ENTRANCE/ETC</div>', unsafe_allow_html=True)
    uploaded_photos['etc'] = st.file_uploader("증거 사진 투입 (Drop Files)", type=['jpg', 'png'], accept_multiple_files=True, key="u4")

st.markdown("---")

# --------------------------------------------------------------------------
# [Action] 실행 버튼
# --------------------------------------------------------------------------
# 버튼 텍스트를 좀 더 시스템적으로 변경
if st.button("🔒 INITIATE PROTOCOL (타임캡슐 봉인)", type="primary", use_container_width=True):
    # 파일 취합
    all_files = []
    for key in uploaded_photos:
        if uploaded_photos[key]:
            all_files.extend(uploaded_photos[key])
            
    if not all_files:
        st.warning("⚠️ WARNING: NO VISUAL DATA DETECTED. (사진을 업로드하세요)")
    else:
        # 워터마크 처리
        processed_images = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark_text = f"{timestamp} | SafeHome R4X Secured"
        
        progress_text = "PROCESSING DATA..."
        my_bar = st.progress(0, text=progress_text)
        
        for idx, file in enumerate(all_files):
            img = add_watermark(file, watermark_text)
            if img: processed_images.append(img)
            my_bar.progress((idx + 1) / len(all_files), text=f"PROCESSING IMAGE {idx+1}/{len(all_files)}")
            
        st.success(f"✅ PROCESS COMPLETE: {len(processed_images)} IMAGES SECURED")
        
        # PDF 생성
        with st.spinner("GENERATING SECURE REPORT (PDF)..."):
            pdf_bytes = create_pdf(processed_images)
            
        if pdf_bytes:
            st.session_state['pdf_bytes'] = pdf_bytes
            st.session_state['file_name'] = f"SafeHome_R4X_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.session_state['pdf_ready'] = True
            st.rerun()
        else:
            st.error("❌ SYSTEM ERROR: PDF GENERATION FAILED")

# --------------------------------------------------------------------------
# [Result] 결과 화면 (HUD Style)
# --------------------------------------------------------------------------
if st.session_state.get('pdf_ready'):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card" style="border-color:#00ff7f; box-shadow:0 0 20px rgba(0,255,127,0.2);">
        <h3 style="color:#00ff7f !important; margin:0;">🎉 MISSION ACCOMPLISHED</h3>
        <p>증거 자료가 안전하게 생성되었습니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_res1, col_res2 = st.columns(2)
    
    # 왼쪽: 다운로드
    with col_res1:
        st.markdown("#### 📥 LOCAL DOWNLOAD")
        st.download_button(
            label="DOWNLOAD PDF REPORT",
            data=st.session_state['pdf_bytes'],
            file_name=st.session_state['file_name'],
            mime="application/pdf",
            use_container_width=True
        )
    
    # 오른쪽: 이메일 전송 (DB 수집)
    with col_res2:
        st.markdown("#### 📧 CLOUD BACKUP (EMAIL)")
        
        with st.form("email_db_form"):
            email_input = st.text_input("RECIPIENT EMAIL", placeholder="example@gmail.com")
            
            default_date = datetime.now().date().replace(year=datetime.now().year + 2)
            expiry_input = st.date_input("EXPIRATION DATE (만기일)", value=default_date)
            
            submit_btn = st.form_submit_button("SEND & REGISTER ALERT", type="primary", use_container_width=True)
            
            if submit_btn:
                if not email_input:
                    st.warning("INPUT REQUIRED: EMAIL ADDRESS")
                else:
                    with st.spinner("SENDING DATA..."):
                        is_sent = send_email(email_input, st.session_state['pdf_bytes'], st.session_state['file_name'])
                        if is_sent:
                            save_to_sheet(email_input, expiry_input)
                            st.success("✅ TRANSMISSION COMPLETE. SYSTEM STANDBY.")
                            st.balloons()