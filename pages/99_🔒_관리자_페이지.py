import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(page_title="SafeHome 3D - 관리자", page_icon="⚙️", layout="wide")

# 2. [디자인] R4X 로봇 배경
st.markdown("""
<style>
    .stApp { background: transparent !important; }
    header, footer { visibility: hidden !important; }
    #spline-bg { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; border: none; }
    .block-container { position: relative; z-index: 1; padding-top: 5vh; max-width: 1100px; }

    /* 대시보드 카드 */
    .stat-box {
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 255, 127, 0.3); /* Green border */
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        color: white;
    }
    .big-number { font-size: 3rem; font-weight: 800; color: #00ff7f; text-shadow: 0 0 15px #00ff7f; }
    .label { font-size: 1rem; color: #aaa; text-transform: uppercase; }
</style>
<iframe id="spline-bg" src='https://my.spline.design/r4xbot-x144J8ISm6Am5vnam9xXxwah/' frameborder='0'></iframe>
""", unsafe_allow_html=True)

# 3. 메인 UI
st.title("⚙️ Admin Control Center")

# 로그인 시뮬레이션
if 'is_admin_logged_in' not in st.session_state:
    st.session_state['is_admin_logged_in'] = False

if not st.session_state['is_admin_logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='stat-box'>ACCESS REQUIRED</div>", unsafe_allow_html=True)
        password = st.text_input("ENTER ACCESS CODE", type="password")
        if st.button("LOGIN", use_container_width=True):
            if password == "safe2026": # 임시 비밀번호
                st.session_state['is_admin_logged_in'] = True
                st.rerun()
            else:
                st.error("ACCESS DENIED")
else:
    # 대시보드 화면
    st.success("✅ SYSTEM ONLINE: ADMINISTRATOR ACCESS GRANTED")
    
    # 1. 통계 지표
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Total Users</div>
            <div class="big-number">1,204</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Contracts Analyzed</div>
            <div class="big-number">856</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Risks Detected</div>
            <div class="big-number">342</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Revenue (KRW)</div>
            <div class="big-number">3.2M</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. 최근 로그 (테이블)
    st.subheader("📝 Recent Activity Logs")
    
    # 가짜 데이터 생성
    df = pd.DataFrame({
        "Timestamp": ["2026-02-07 10:01", "2026-02-07 09:45", "2026-02-07 09:12"],
        "User ID": ["User_8821", "User_9921", "User_1102"],
        "Action": ["Contract Analysis (PDF)", "Premium Upgrade", "Chatbot Query"],
        "Status": ["Success", "Success", "Pending"]
    })
    
    # 데이터프레임 스타일링 (투명하게)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    if st.button("LOGOUT"):
        st.session_state['is_admin_logged_in'] = False
        st.rerun()