import streamlit as st
from PIL import Image

# --------------------------------------------------------------------------
# [설정] 페이지 기본 설정 & 3D HUD 스타일 (CSS Magic)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="SafeHome 3D - Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------------------------------
# [스타일] CSS: 로봇 배경 + 글래스모피즘 HUD
# --------------------------------------------------------------------------
st.markdown("""
<style>
    /* 1. 전체 배경 및 폰트 */
    .stApp { 
        font-family: 'Pretendard', sans-serif; 
        background: transparent !important; 
    }
    
    /* Spline 3D 배경 (전체 화면 고정) */
    #spline-bg {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; border: none;
    }
    
    /* 컨텐츠 영역 (배경 위에 뜸) */
    .block-container {
        position: relative; z-index: 1; padding-top: 5vh; max-width: 1200px;
    }

    /* 2. 타이틀 스타일 (네온 효과) */
    .main-title {
        font-size: 60px;
        font-weight: 800;
        color: white;
        text-align: center;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.8);
        margin-bottom: 10px;
        letter-spacing: 2px;
    }
    .sub-title {
        font-size: 20px;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 50px;
        font-weight: 300;
    }

    /* 3. 기능 카드 (Glassmorphism) */
    .feature-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 280px; /* 높이 고정 */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 10px 40px rgba(56, 189, 248, 0.3);
        border-color: rgba(56, 189, 248, 0.5);
    }
    
    .card-icon { font-size: 50px; margin-bottom: 15px; }
    .card-title { font-size: 22px; font-weight: bold; color: white; margin-bottom: 10px; }
    .card-desc { font-size: 14px; color: #cbd5e1; line-height: 1.6; }

    /* 사이드바 스타일 보정 */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.9);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
</style>

<iframe id="spline-bg" src='https://my.spline.design/r4xbot-x144J8ISm6Am5vnam9xXxwah/' frameborder='0'></iframe>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [UI] 메인 컨텐츠
# --------------------------------------------------------------------------

# 1. 헤더 섹션
st.markdown('<div class="main-title">SAFEHOME AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">"당신의 보증금을 지키는 가장 강력한 인공지능 방어 시스템"</div>', unsafe_allow_html=True)

st.divider()

# 2. 3개 기능 카드 섹션 (HTML/CSS로 구현하여 시각적 통일감 부여)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">📄</div>
        <div class="card-title">계약서 AI 정밀 분석</div>
        <div class="card-desc">
            법률 전문 LLM이 독소 조항을 탐지하고<br>
            수정 제안을 제시합니다.<br>
            <span style="color:#38bdf8; font-size:12px;">(왼쪽 메뉴 '계약서 분석' 클릭)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">📸</div>
        <div class="card-title">입주 기록 타임캡슐</div>
        <div class="card-desc">
            로봇 스캐너가 방 상태를 기록하고<br>
            위변조 불가능한 리포트를 생성합니다.<br>
            <span style="color:#38bdf8; font-size:12px;">(왼쪽 메뉴 '입주 체크리스트' 클릭)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">🏠</div>
        <div class="card-title">거주 법률 솔루션</div>
        <div class="card-desc">
            누수, 소음, 수리 분쟁 발생 시<br>
            내용증명 작성 및 대응법을 안내합니다.<br>
            <span style="color:#38bdf8; font-size:12px;">(왼쪽 메뉴 '거주 솔루션' 클릭)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# 3. 하단 시스템 상태 메시지
st.info("💡 **System Status:** All Systems Operational. Ready for Input.")