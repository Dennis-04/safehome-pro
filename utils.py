import streamlit as st
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 구글 시트 저장 함수 (공통 사용)
def save_to_google_sheets(data_json):
    try:
        # Streamlit Secrets에서 구글 인증 정보 로드
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 'safehome_db' 시트 열기
        sheet = client.open("safehome_db").sheet1 
        
        # 저장할 데이터 행 구성
        row = [
            str(datetime.datetime.now()), # 시간
            data_json.get("district", "Unknown"), # 구/동
            data_json.get("deposit", 0), # 보증금
            data_json.get("rent", 0), # 월세
            data_json.get("risk_score", 0), # 위험도
            ", ".join(data_json.get("toxic_clauses", [])), # 독소조항 목록
            data_json.get("plan_type", "Basic") # 요금제
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"DB 저장 실패: {e}") 
        return False