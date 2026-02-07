import streamlit as st
import time  # <--- 이 줄이 빠져있어서 난 오류입니다. 추가해주세요!
from datetime import datetime
from openai import OpenAI # 나중에 프롬프트 강화 때 사용할 준비

# 1. 페이지 설정
st.set_page_config(page_title="SafeHome 3D - 솔루션", page_icon="🧸", layout="wide")

# 2. [디자인] R4X 로봇 배경
st.markdown("""
<style>
    .stApp { background: transparent !important; }
    header, footer { visibility: hidden !important; }
    #spline-bg { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; border: none; }
    .block-container { position: relative; z-index: 1; padding-top: 5vh; max-width: 800px; }

    /* 채팅 메시지 스타일 */
    .stChatMessage {
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        margin-bottom: 10px;
    }
    /* 유저 메시지 */
    div[data-testid="chatAvatarIcon-user"] { background-color: #38bdf8; }
    /* AI 메시지 */
    div[data-testid="chatAvatarIcon-assistant"] { background-color: #f43f5e; }
    
    h1 { text-shadow: 0 0 20px rgba(255,255,255,0.5); }
</style>
<iframe id="spline-bg" src='https://my.spline.design/r4xbot-x144J8ISm6Am5vnam9xXxwah/' frameborder='0'></iframe>
""", unsafe_allow_html=True)

# 3. 메인 UI
st.title("🤖 AI Concierge Link")
st.caption("거주 중 발생하는 법적 문제, 수리 요청 등 무엇이든 물어보세요.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "시스템 온라인. R4X 봇입니다. \n\n보일러 고장, 층간 소음, 월세 인상 요구 등 곤란한 일이 있으신가요?"}
    ]

# 대화 기록 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 입력창
if prompt := st.chat_input("질문을 입력하세요 (예: 보일러가 고장 났는데 집주인이 안 고쳐줘요)"):
    # 1. 유저 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. AI 응답 (나중에 로직 강화할 부분)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # [시뮬레이션] 나중에 실제 GPT 스트리밍으로 교체될 부분
        simulated_response = "확인했습니다. 민법 제623조에 따르면 임대인은 목적물을 사용, 수익하게 할 의무가 있으므로 보일러 수리는 원칙적으로 집주인의 의무입니다. \n\n집주인에게 보낼 문자 초안을 작성해 드릴까요?"
        
        # 타이핑 효과 연출
        for chunk in simulated_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})