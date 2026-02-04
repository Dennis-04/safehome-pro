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
# [설정] 페이지 기본 설정 & 디자인 CSS
# --------------------------------------------------------------------------
st.set_page_config(page_title="입주 기록 (타임캡슐)", page_icon="📸", layout="wide")

st.markdown("""
<style>
    /* 전체 폰트 가독성 향상 */
    .stApp { font-family: 'Pretendard', sans-serif; }
    
    /* 헤더 스타일 */
    .header-box {
        padding: 20px;
        background-color: #f0f7ff;
        border-radius: 12px;
        margin-bottom: 25px;
        border-left: 5px solid #3182f6;
    }
    .header-title { font-size: 24px; font-weight: 700; color: #191f28; }
    .header-desc { font-size: 16px; color: #4e5968; margin-top: 5px; }
    
    /* 팁 박스 스타일 */
    .tip-box {
        background-color: #f2f4f6;
        padding: 15px;
        border-radius: 8px;
        font-size: 14px;
        color: #333d4b;
        margin-bottom: 20px;
    }
    
    /* 중요 버튼 강조 */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: bold;
        height: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [함수 1] 워터마크 처리
# --------------------------------------------------------------------------
def add_watermark(image_file, text):
    try:
        image = Image.open(image_file)
        # 이미지 회전 정보(EXIF) 처리 생략 (필요시 추가)
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # 폰트 크기 자동 조절 (이미지 높이의 4%)
        font_size = int(height * 0.04)
        try:
            # 윈도우/맥 기본 폰트 시도 (나눔고딕 등)
            font = ImageFont.truetype("NanumGothic.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # 워터마크 위치 (우하단 여백)
        text_width = font_size * len(text) * 0.6
        x = width - text_width - (width * 0.05)
        y = height - font_size - (height * 0.05)

        # 글자 테두리(검정) + 글자(흰색) -> 가독성 확보
        stroke_width = 2
        draw.text((x, y), text, font=font, fill="white", stroke_width=stroke_width, stroke_fill="black")
        
        return image
    except Exception as e:
        st.error(f"이미지 처리 중 오류: {e}")
        return None

# --------------------------------------------------------------------------
# [함수 2] PDF 생성
# --------------------------------------------------------------------------
def create_pdf(image_list):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(0)
        
        for img in image_list:
            pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                img_rgb = img.convert('RGB')
                img_rgb.save(tmp_file.name, "JPEG", quality=85)
                # A4(210mm) 기준 여백 고려 190mm 꽉 채우기
                pdf.image(tmp_file.name, x=10, y=10, w=190)
            os.unlink(tmp_file.name)
            
        return bytes(pdf.output())
    except Exception as e:
        st.error(f"PDF 생성 중 오류: {e}")
        return None

# --------------------------------------------------------------------------
# [함수 3] 이메일 전송 (제목 중복 수정됨)
# --------------------------------------------------------------------------
def send_email(to_email, pdf_bytes, filename):
    try:
        smtp_info = st.secrets["smtp"]
        my_email = smtp_info["EMAIL_ADDRESS"]
        my_password = smtp_info["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"[SafeHome] 입주 점검 리포트가 발급되었습니다 ({datetime.now().strftime('%Y-%m-%d')})"
        msg['From'] = my_email
        msg['To'] = to_email
        
        body = f"""
        안녕하세요, 고객님.
        당신의 소중한 보증금을 지키는 SafeHome입니다.
        
        요청하신 '입주 점검 리포트' 생성이 완료되어 첨부파일로 전달드립니다.
        첨부파일을 꼭 안전한 곳에 보관해주세요.
        
        감사합니다.
        SafeHome 드림
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
        st.error(f"메일 전송 실패: {e}")
        return False

# --------------------------------------------------------------------------
# [함수 4] 구글 시트 저장 (ID 방식 - 확실한 연결)
# --------------------------------------------------------------------------
def save_to_sheet(email, expiry_date):
    try:
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            st.error("❌ secrets.toml 설정 오류")
            return False

        credentials_info = st.secrets["connections"]["gsheets"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # [중요] 여기에 선생님의 구글 시트 ID를 넣어주세요!
        # 어제 복사했던 그 긴 ID가 코드에 들어가 있어야 합니다.
        # 만약 이 코드를 복붙하신다면, 아래 ID 부분만 본인 것으로 꼭! 다시 바꿔주세요.
        sheet_id = "1TZYPOaiI87gR_BRyTCZQedvPtmMzF7p-JdmIlKGeh_s" # <--- 여기에 실제 ID 입력 필수!!
        
        sheet = client.open_by_key(sheet_id).sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, email, str(expiry_date), "발송완료"])
        
        return True
    except Exception as e:
        st.warning(f"⚠️ 시트 ID를 확인해주세요. (오류: {e})")
        return False

# --------------------------------------------------------------------------
# [UI] 메인 화면 구성
# --------------------------------------------------------------------------
st.markdown("""
<div class="header-box">
    <div class="header-title">📸 입주 타임캡슐</div>
    <div class="header-desc">입주 날 방 상태를 기록해두세요. 2년 뒤 퇴거 시 든든한 증거가 됩니다.</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.info("💡 **사용 가이드:** 사진을 업로드하고 하단의 '캡슐 봉인하기' 버튼을 누르면 PDF 리포트가 생성됩니다.")

with col2:
    st.markdown("""
    <div class="tip-box">
        <b>✅ 필수 촬영 리스트</b><br>
        - 바닥 찍힘/변색<br>
        - 벽지 찢어짐/낙서<br>
        - 옵션 가구 파손
    </div>
    """, unsafe_allow_html=True)

# 탭 구성
tabs = st.tabs(["🛋️ 거실/방", "🍳 주방", "🚽 화장실", "🚪 현관/기타"])
uploaded_photos = {}

with tabs[0]:
    uploaded_photos['room'] = st.file_uploader("거실 및 방 사진", type=['jpg', 'png'], accept_multiple_files=True, key="u1")
with tabs[1]:
    uploaded_photos['kitchen'] = st.file_uploader("주방/싱크대 사진", type=['jpg', 'png'], accept_multiple_files=True, key="u2")
with tabs[2]:
    uploaded_photos['bath'] = st.file_uploader("화장실/욕실 사진", type=['jpg', 'png'], accept_multiple_files=True, key="u3")
with tabs[3]:
    uploaded_photos['etc'] = st.file_uploader("현관/기타 사진", type=['jpg', 'png'], accept_multiple_files=True, key="u4")

st.divider()

# --------------------------------------------------------------------------
# [Action] 실행 버튼
# --------------------------------------------------------------------------
if st.button("🔒 타임캡슐 봉인하기 (리포트 생성)", type="primary", use_container_width=True):
    # 파일 취합
    all_files = []
    for key in uploaded_photos:
        if uploaded_photos[key]:
            all_files.extend(uploaded_photos[key])
            
    if not all_files:
        st.warning("📸 사진을 최소 1장 이상 업로드해주세요.")
    else:
        # 워터마크 처리
        processed_images = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark_text = f"{timestamp} | SafeHome"
        
        progress_bar = st.progress(0)
        
        for idx, file in enumerate(all_files):
            img = add_watermark(file, watermark_text)
            if img: processed_images.append(img)
            progress_bar.progress((idx + 1) / len(all_files))
            
        st.success(f"✅ 총 {len(processed_images)}장의 증거 사진 처리 완료!")
        
        # PDF 생성
        with st.spinner("📄 PDF 문서를 만들고 있습니다..."):
            pdf_bytes = create_pdf(processed_images)
            
        if pdf_bytes:
            st.session_state['pdf_bytes'] = pdf_bytes
            st.session_state['file_name'] = f"SafeHome_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.session_state['pdf_ready'] = True
            st.rerun() # 화면 새로고침하여 다운로드 버튼 활성화
        else:
            st.error("PDF 생성 실패")

# --------------------------------------------------------------------------
# [Result] 결과 화면 (다운로드 & 이메일)
# --------------------------------------------------------------------------
if st.session_state.get('pdf_ready'):
    st.markdown("---")
    st.subheader("🎉 증거 자료가 준비되었습니다.")
    
    col_res1, col_res2 = st.columns(2)
    
    # 왼쪽: 다운로드
    with col_res1:
        st.markdown("#### 📥 PC에 저장하기")
        st.download_button(
            label="PDF 리포트 다운로드",
            data=st.session_state['pdf_bytes'],
            file_name=st.session_state['file_name'],
            mime="application/pdf",
            use_container_width=True
        )
    
    # 오른쪽: 이메일 전송 (DB 수집)
    with col_res2:
        st.markdown("#### 📧 이메일로 백업하기 (추천)")
        st.caption("2년 뒤 만기일에 맞춰 알림을 드립니다.")
        
        with st.form("email_db_form"):
            email_input = st.text_input("이메일 주소", placeholder="example@gmail.com")
            
            # 만기일 자동 계산 (2년 뒤)
            default_date = datetime.now().date().replace(year=datetime.now().year + 2)
            expiry_input = st.date_input("전세/보증금 만기일", value=default_date)
            
            submit_btn = st.form_submit_button("전송 및 알림 예약", type="primary", use_container_width=True)
            
            if submit_btn:
                if not email_input:
                    st.warning("이메일을 입력해주세요.")
                else:
                    with st.spinner("전송 중..."):
                        is_sent = send_email(email_input, st.session_state['pdf_bytes'], st.session_state['file_name'])
                        if is_sent:
                            save_to_sheet(email_input, expiry_input)
                            st.success("✅ 전송 완료! 만기일에 알림을 드릴게요.")
                            st.balloons()