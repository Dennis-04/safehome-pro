import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --------------------------------------------------------------------------
# [설정] 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="SafeHome 관리자", page_icon="👮", layout="wide")

st.title("👮 SafeHome 관리자 모드")
st.caption("고객 데이터를 조회하고 리타겟팅(알림)을 수행합니다.")

# --------------------------------------------------------------------------
# [보안] 비밀번호 체크 (간단한 버전)
# --------------------------------------------------------------------------
# 실제 서비스에선 더 강력한 보안이 필요합니다.
password = st.text_input("관리자 암호를 입력하세요", type="password")
if password != "1234":  # 원하는 비밀번호로 바꾸세요
    st.warning("접근 권한이 없습니다.")
    st.stop()

# --------------------------------------------------------------------------
# [함수 1] 구글 시트 데이터 가져오기
# --------------------------------------------------------------------------
def load_data():
    try:
        credentials_info = st.secrets["connections"]["gsheets"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # [주의] 아까 그 시트 ID를 여기에 똑같이 넣어주세요!
        sheet_id = "1TZYPOaiI87gR_BRyTCZQedvPtmMzF7p-JdmIlKGeh_s" 
        
        sheet = client.open_by_key(sheet_id).sheet1
        data = sheet.get_all_records() # 딕셔너리 리스트로 가져옴
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------
# [함수 2] 리타겟팅 메일 발송
# --------------------------------------------------------------------------
def send_marketing_email(to_email):
    try:
        smtp_info = st.secrets["smtp"]
        my_email = smtp_info["EMAIL_ADDRESS"]
        my_password = smtp_info["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['Subject'] = "[SafeHome] 전세 만기가 2개월 남으셨나요?"
        msg['From'] = my_email
        msg['To'] = to_email
        
        body = f"""
        안녕하세요! SafeHome입니다.
        
        고객님께서 기록해주신 '전세 만기일'이 약 2개월 앞으로 다가왔습니다.
        이사 준비나 보증금 반환 준비는 잘 되고 계신가요?
        
        [SafeHome이 도와드릴 수 있는 것]
        1. 다음 집 등기부등본 무료 분석
        2. 보증금 미반환 시 대처 매뉴얼
        3. 이사 체크리스트 제공
        
        도움이 필요하시면 언제든 방문해주세요.
        👉 https://safehome-demo.streamlit.app (링크)
        
        감사합니다.
        SafeHome 팀 드림
        """
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(my_email, my_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"전송 실패: {e}")
        return False

# --------------------------------------------------------------------------
# [UI] 대시보드 구성
# --------------------------------------------------------------------------
if st.button("🔄 데이터 새로고침"):
    st.rerun()

df = load_data()

if not df.empty:
    st.subheader(f"총 가입자: {len(df)}명")
    
    # 1. 만기일 분석 (D-Day 계산)
    # 날짜 형식 변환 (문자열 -> 날짜객체)
    # 시트의 헤더 이름이 '만기일'인지 확인 필요 (어제 코드 기준 3번째 컬럼)
    # 데이터프레임 컬럼명을 확인해서 'Expiry' 관련 컬럼 찾기
    
    # 임시로 컬럼명 맞추기 (시트 헤더에 따라 다를 수 있음)
    # 어제 코드: sheet.append_row([timestamp, email, str(expiry_date), "발송완료"])
    # 시트 헤더(1행): 날짜, 이메일, 만기일, 비고 라고 가정
    
    # 만기일 컬럼 찾기
    date_col = None
    for col in df.columns:
        if "만기" in str(col) or "Expiry" in str(col):
            date_col = col
            break
            
    if date_col:
        # D-Day 계산
        today = datetime.now().date()
        df['만기일_변환'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
        
        # 남은 기간 계산
        df['남은기간'] = df['만기일_변환'].apply(lambda x: (x - today).days if pd.notnull(x) else 9999)
        
        # 2. 타겟팅 대상 추출 (만기 60일 전후인 사람)
        # 예: 0일 < 남은기간 <= 60일
        target_users = df[ (df['남은기간'] > 0) & (df['남은기간'] <= 60) ]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(df, use_container_width=True)
            
        with col2:
            st.error(f"🔥 긴급 타겟팅 대상: {len(target_users)}명")
            st.caption("만기가 2달 이내로 남은 고객입니다.")
            
            if not target_users.empty:
                for idx, row in target_users.iterrows():
                    with st.expander(f"📩 {row['이메일']} (D-{row['남은기간']})"):
                        if st.button("마케팅 메일 발송", key=f"btn_{idx}"):
                            is_sent = send_marketing_email(row['이메일'])
                            if is_sent:
                                st.toast(f"{row['이메일']} 발송 완료!", icon="✅")
            else:
                st.success("현재 만기 임박 고객이 없습니다.")
                
    else:
        st.warning("만기일 컬럼을 찾지 못했습니다. 시트 헤더를 확인해주세요.")
        st.dataframe(df)
else:
    st.info("데이터가 없거나 불러오지 못했습니다.")