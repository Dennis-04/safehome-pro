import streamlit as st
from openai import OpenAI
import base64
import os
import streamlit.components.v1 as components
import sqlite3
import json
from datetime import datetime

# --------------------------------------------------------------------------
# [설정] 페이지 기본 세팅 및 CSS
# --------------------------------------------------------------------------
st.set_page_config(page_title="세이프홈 Pro", page_icon="🏠", layout="centered")

st.markdown("""
<style>
    .stApp { font-family: 'Pretendard', sans-serif; }
    .guide-box {
        background-color: #1e1e1e; color: #e0e0e0; padding: 20px;
        border-radius: 12px; border: 1px solid #333; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .checklist-box {
        background-color: #263238; padding: 20px; border-radius: 10px;
        border-left: 5px solid #00e676; margin-top: 30px;
    }
    .refund-box {
        background-color: #3e2723; padding: 15px; border-radius: 8px;
        border: 1px solid #ffab91; margin-top: 20px; font-size: 14px;
    }
    .discount-box {
        background-color: #e3f2fd; border: 1px solid #2196f3; color: #0d47a1;
        padding: 10px; border-radius: 8px; margin-bottom: 10px; font-weight: bold;
    }
    .highlight-green { color: #00e676; font-weight: bold; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton>button:active { transform: scale(0.98); }
    div[data-testid="stToast"] { font-weight: bold; background-color: #00e676 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [보안] Secrets 키 가져오기
# --------------------------------------------------------------------------
api_key = os.environ.get("OPENAI_API_KEY")
toss_client_key = os.environ.get("TOSS_CLIENT_KEY", "test_ck_DnyRpQWGrNzkLXLyLYegrKwv1M9E")

# --------------------------------------------------------------------------
# [데이터베이스] SQLite 초기화 (서버 없이 파일로 저장)
# --------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('safehome_data.db')
    c = conn.cursor()
    # 테이블이 없으면 생성 (확장성을 위한 JSON 컬럼 포함)
    c.execute('''
        CREATE TABLE IF NOT EXISTS contract_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            quality_grade TEXT,
            risk_score INTEGER,
            anonymized_content TEXT,
            region_info TEXT,
            is_consented INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# 앱 실행 시 DB 초기화 (한 번만 실행됨)
init_db()

# --------------------------------------------------------------------------
# [UI] 사이드바 & 헤더
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_code = st.text_input("관리자 패스워드", type="password")
    is_admin = (admin_code == "safe2026")
    
    if is_admin:
        st.success("✅ 관리자 모드: 결제 패스")
        # 관리자용: 데이터 다운로드 기능 (나중에 엑셀로 변환 가능)
        if st.button("📂 수집된 데이터 보기"):
            conn = sqlite3.connect('safehome_data.db')
            data = conn.execute("SELECT * FROM contract_data ORDER BY id DESC LIMIT 5").fetchall()
            st.write(data)
            conn.close()

st.title("🏠 세이프홈 Pro")
st.markdown("### 대학생을 위한 **전세사기 방어 솔루션**")

st.markdown("""
<div class="guide-box">
    <h4 style="margin-top:0; color:white;">⚡ 3초 만에 내 보증금 지키기</h4>
    <p>1. 계약서 <span class="highlight-green">[특약사항]</span> 촬영<br>
    2. <b>AI 정밀 분석</b> 받고 독소조항 찾기<br>
    3. <b>법적 효력</b> 있는 문자 메시지 초안 받기</p>
</div>
""", unsafe_allow_html=True)

# [기능 1] 샘플 리포트
with st.expander("👀 분석 결과가 어떻게 나오나요? (예시 보기)"):
    st.info("실제 분석 시 아래와 같이 독소조항을 콕 집어 알려드립니다.")
    st.markdown("""
    > **🤖 AI 변호사 분석 결과**
    > **[위험] 특약 제 3조:** *"퇴실 시 청소비 30만 원을 정액으로 공제한다."*
    > 💡 **수정 제안:** "퇴실 시 청소비는 실비를 기준으로 영수증 증빙 후 정산한다"로 변경 요청하세요.
    """)

# [기능 2] 파일 업로드
tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 앨범에서 선택"])
uploaded_file = None

with tab1:
    camera_image = st.camera_input("계약서를 평평한 곳에 두고 찍어주세요")
    if camera_image: uploaded_file = camera_image
with tab2:
    file_image = st.file_uploader("계약서 사진 업로드", type=['jpg', 'png', 'jpeg'])
    if file_image: uploaded_file = file_image

# --------------------------------------------------------------------------
# [로직] 결제 및 분석
# --------------------------------------------------------------------------
query_params = st.query_params
is_paid_success = ("payment" in query_params and query_params["payment"] == "success")
final_paid_status = is_paid_success or is_admin

if final_paid_status and "welcome_msg" not in st.session_state:
    st.toast("🎉 결제 확인 완료! 분석을 시작하세요.", icon="✅")
    st.session_state["welcome_msg"] = True

if uploaded_file is not None:
    st.image(uploaded_file, caption='업로드된 계약서', use_container_width=True)

    # ----------------------------------------------------------------------
    # [수정된 부분 1] 데이터 수집 동의 & 할인 결제 로직
    # ----------------------------------------------------------------------
    if not final_paid_status:
        st.write("---")
        
        # 데이터 기여 체크박스
        st.markdown("#### 💰 할인 혜택 받기")
        is_consented = st.checkbox(
            "청년 주거 안전 생태계 조성을 위한 데이터 기여 동의 (200원 즉시 할인)", 
            value=True,
            help="개인정보(이름, 번호 등)는 즉시 삭제되며, 비식별 처리된 통계 데이터만 수집됩니다."
        )

        final_amount = 790 if is_consented else 990
        
        if is_consented:
            st.markdown(f"""<div class="discount-box">✅ 데이터 기여 덕분에 200원 할인! (990원 → 790원)</div>""", unsafe_allow_html=True)

        st.warning(f"🔒 아래 버튼을 누르면 {final_amount}원이 결제됩니다.")
       
        # 토스페이먼츠 결제 버튼 (자바스크립트에 Python 변수 주입)
        html_code = f"""
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <div style="text-align: center; margin-top: 20px;">
            <button id="payment-button" style="background-color: #3182f6; color: white; padding: 16px 24px; border: none; border-radius: 12px; font-size: 17px; font-weight: bold; cursor: pointer; width: 100%;">
                🛡️ {final_amount}원으로 보증금 지키기
            </button>
        </div>
        <script>
            var clientKey = '{toss_client_key}'
            var tossPayments = TossPayments(clientKey)
            var button = document.getElementById('payment-button')
            var currentUrl = window.location.href.split('?')[0];
            button.addEventListener('click', function () {{
                tossPayments.requestPayment('카드', {{
                    amount: {final_amount},
                    orderId: 'ORDER_' + new Date().getTime(),
                    orderName: '전세사기 방어 리포트',
                    customerName: '세이프홈 회원',
                    successUrl: currentUrl + '?payment=success&consented={str(is_consented).lower()}',
                    failUrl: currentUrl + '?payment=fail',
                }})
            }})
        </script>
        """
        components.html(html_code, height=150)

    # ----------------------------------------------------------------------
    # [수정된 부분 2] GPT-4o mini 교체 및 데이터 자동 수집/저장
    # ----------------------------------------------------------------------
    else:
        # URL 파라미터에서 동의 여부 가져오기 (결제 후 리다이렉트 시 유지)
        consented_param = query_params.get("consented", "false")
        is_user_consented = True if consented_param == "true" else False
        
        st.write("---")
        tone = st.radio("문자 말투 선택", ["👼 부드럽게", "⚖️ 단호하게"], index=0, horizontal=True)
       
        if st.button("🚀 AI 정밀 분석 시작 (Click)"):
            if not api_key:
                st.error("🚨 API Key 설정 오류. (Secrets를 확인하세요)")
            else:
                client = OpenAI(api_key=api_key)
                with st.spinner("AI가 계약서를 분석하고 데이터베이스를 생성 중입니다..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                       
                        # [핵심] JSON 포맷을 강제하는 프롬프트 (데이터 자산화 + 사용자 리포트 동시 생성)
                        system_prompt = f"""
                        당신은 '전세사기 예방 전문가'이자 '데이터 분석가'입니다.
                        주어진 계약서 이미지를 분석하여 반드시 아래 JSON 형식으로만 응답하세요.
                        
                        {{
                            "analysis_report": "사용자에게 보여줄 분석 결과. 독소조항, 필수 누락, 신탁 등기 여부를 포함하고 {tone} 말투로 작성된 문자 초안을 포함.",
                            "anonymized_data": "개인정보(이름, 주민번호, 전화번호, 주소 상세)를 완벽히 제거(마스킹)한 계약서 전문 텍스트.",
                            "risk_score": 0~100 사이의 위험도 점수 (정수),
                            "quality_grade": "Platinum(선명함/특이조항있음), Gold(보통), Silver(흐릿함) 중 하나 선택"
                        }}
                        """
                       
                        # 모델을 gpt-4o-mini로 변경 (비용 절감)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini", 
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": [
                                    {"type": "text", "text": "계약서를 분석하고 JSON으로 출력해."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]}
                            ],
                            response_format={"type": "json_object"}, # JSON 강제 모드
                            max_tokens=2500
                        )
                        
                        # 결과 파싱
                        result_json = json.loads(response.choices[0].message.content)
                        
                        # 1. 사용자에게 리포트 보여주기
                        st.success("분석 완료!")
                        st.markdown(result_json["analysis_report"])
                        
                        st.markdown("""
                        <div class="checklist-box">
                            <h4 style="color:#00e676;">🛑 필수 체크</h4>
                            <ul style="color:white;">
                                <li>✅ 입금 계좌주 = 집주인 이름 일치 확인</li>
                                <li>✅ 신분증 진위 확인 (ARS 1382)</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 2. (백그라운드) DB에 데이터 저장
                        # 동의한 사용자이거나 관리자 테스트일 경우에만 저장
                        if is_user_consented or is_admin:
                            conn = sqlite3.connect('safehome_data.db')
                            c = conn.cursor()
                            c.execute("INSERT INTO contract_data (timestamp, quality_grade, risk_score, anonymized_content, region_info, is_consented) VALUES (?, ?, ?, ?, ?, ?)",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                       result_json["quality_grade"], 
                                       result_json["risk_score"], 
                                       result_json["anonymized_data"], 
                                       "Seoul_Mapo", # 추후 GPS 기능 연동 시 변경 가능
                                       1 if is_user_consented else 0))
                            conn.commit()
                            conn.close()
                            # print("DB 저장 완료") -> 실제 서비스엔 로그만 남김
                        
                        st.markdown("""
                        <div class="refund-box">
                            <b>💁‍♂️ 결과가 만족스럽지 않으신가요?</b><br>
                            분석 오류나 불만족 시 100% 환불해 드립니다.<br>
                            문의: <u>help@safehome.com</u> (주문번호 포함)
                        </div>
                        """, unsafe_allow_html=True)
                       
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

# --------------------------------------------------------------------------
# [Footer]
# --------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px; line-height: 1.6;'>
    <b>세이프홈 Pro (SafeHome)</b> | 대표: 홍길동<br>
    사업자등록번호: 000-00-00000 (발급 진행 중)<br>
    본 서비스는 AI 분석 결과로 법적 효력이 없으며, 최종 판단의 책임은 사용자에게 있습니다.
</div>
""", unsafe_allow_html=True)