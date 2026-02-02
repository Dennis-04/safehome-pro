import streamlit as st
from openai import OpenAI
import base64
import os
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit.components.v1 as components

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
    .price-box {
        background-color: #263238; padding: 15px; border-radius: 10px;
        border: 2px solid #00e676; text-align: center; margin-bottom: 15px;
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
# [보안] Secrets 키 가져오기 (Streamlit Cloud 용)
# --------------------------------------------------------------------------
api_key = st.secrets["OPENAI_API_KEY"]
toss_client_key = st.secrets.get("TOSS_CLIENT_KEY", "test_ck_DnyRpQWGrNzkLXLyLYegrKwv1M9E")

# --------------------------------------------------------------------------
# [함수] 구글 시트 데이터 저장 (B2B 자산화)
# --------------------------------------------------------------------------
def save_to_google_sheets(data_json):
    try:
        # Streamlit Secrets에서 구글 인증 정보 로드
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 'safehome_db'라는 이름의 시트를 엽니다 (미리 만들어둬야 함)
        # 없으면 1번째 시트를 엽니다.
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
        print(f"DB 저장 실패: {e}") # 사용자에게는 에러 안 보이게 로그만
        return False

# --------------------------------------------------------------------------
# [UI] 사이드바 & 헤더
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_code = st.text_input("관리자 패스워드", type="password")
    is_admin = (admin_code == "safe2026")
    if is_admin:
        st.success("✅ 관리자 모드: 무료 통과")

st.title("🏠 세이프홈 Pro")
st.markdown("### 대학생을 위한 **전세사기 방어 솔루션**")

st.markdown("""
<div class="guide-box">
    <h4 style="margin-top:0; color:white;">⚡ 3초 만에 내 보증금 지키기</h4>
    <p>1. 계약서 <span class="highlight-green">[특약사항]</span> 촬영<br>
    2. <b>AI 정밀 분석</b> 및 <b>독소조항 탐지</b><br>
    3. <b>법적 효력</b> 있는 문자 메시지 초안 제공</p>
</div>
""", unsafe_allow_html=True)

# [기능 1] 샘플 리포트
with st.expander("👀 분석 결과가 어떻게 나오나요? (예시 보기)"):
    st.info("실제 분석 시 아래와 같이 독소조항을 콕 집어 알려드립니다.")
    st.markdown("""
    > **🤖 AI 변호사 분석 결과**
    > **[위험] 특약 제 3조:** *"퇴실 시 청소비 30만 원을 정액으로 공제한다."*
    > 👉 **문제점:** 실제 청소 비용과 무관하게 고액을 요구하는 독소 조항입니다.
    > 💡 **수정 제안:** "퇴실 시 청소비는 실비를 기준으로 영수증 증빙 후 정산한다"로 변경 요청하세요.
    """)

# [기능 2] 파일 업로드 방식 선택
tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 앨범에서 선택"])
uploaded_file = None

with tab1:
    camera_image = st.camera_input("계약서를 평평한 곳에 두고 찍어주세요")
    if camera_image: uploaded_file = camera_image
with tab2:
    file_image = st.file_uploader("계약서 사진 업로드", type=['jpg', 'png', 'jpeg'])
    if file_image: uploaded_file = file_image

# --------------------------------------------------------------------------
# [로직] 요금제 선택 및 결제
# --------------------------------------------------------------------------
query_params = st.query_params
is_paid_success = ("payment" in query_params and query_params["payment"] == "success")
final_paid_status = is_paid_success or is_admin

if uploaded_file is not None:
    st.image(uploaded_file, caption='업로드된 계약서', use_container_width=True)

    # 결제 전 화면: 요금제 선택 UI
    if not final_paid_status:
        st.divider()
        st.subheader("💰 요금제 선택")
        
        # 1. 요금제 플랜 선택
        plan_option = st.radio(
            "원하는 분석 수준을 선택하세요",
            ["🥉 Basic (필수 분석 + 문자 초안)", "🥇 Premium (Basic + 전문가용 요약본 PDF)"],
            index=0
        )
        
        # 2. 데이터 제공 동의 (할인 옵션)
        st.markdown("""
        <div style='background-color: #f1f8e9; padding: 10px; border-radius: 5px; color: #33691e; font-size: 14px;'>
        <b>🎁 데이터 제공 할인 이벤트</b><br>
        익명화된 계약 데이터를 연구용으로 제공하는 데 동의하시면 <b>즉시 할인</b>해 드립니다.<br>
        (이름, 연락처 등 개인정보는 <b>완벽하게 삭제(마스킹)</b>되어 저장됩니다.)
        </div>
        """, unsafe_allow_html=True)
        agree_data = st.checkbox("네, 익명 데이터 제공에 동의하고 할인받겠습니다. (추천)", value=True)

        # 가격 계산 로직
        if "Basic" in plan_option:
            base_price = 990
            discounted_price = 790
            plan_code = "BASIC"
        else:
            base_price = 3900
            discounted_price = 2900
            plan_code = "PREMIUM"
            
        final_price = discounted_price if agree_data else base_price
        
        # 가격 표시 박스
        st.markdown(f"""
        <div class="price-box">
            <span style='color:#bbb; text-decoration:line-through;'>{base_price}원</span> → 
            <span style='font-size: 24px; font-weight: bold; color: #00e676;'>{final_price}원</span> 결제
        </div>
        """, unsafe_allow_html=True)

        # 토스페이먼츠 결제 버튼
        # 주의: f-string 안에 final_price 변수를 넣어 동적으로 가격이 바뀜
        html_code = f"""
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <div style="text-align: center; margin-top: 20px;">
            <button id="payment-button" style="background-color: #3182f6; color: white; padding: 16px 24px; border: none; border-radius: 12px; font-size: 17px; font-weight: bold; cursor: pointer; width: 100%;">
                🛡️ 보증금 지키기 ({final_price}원)
            </button>
        </div>
        <script>
            var clientKey = '{toss_client_key}'
            var tossPayments = TossPayments(clientKey)
            var button = document.getElementById('payment-button')
            var currentUrl = window.location.href.split('?')[0];
            button.addEventListener('click', function () {{
                tossPayments.requestPayment('카드', {{
                    amount: {final_price},
                    orderId: 'ORDER_' + new Date().getTime(),
                    orderName: '전세사기 리포트_{plan_code}',
                    customerName: '세이프홈 고객',
                    successUrl: currentUrl + '?payment=success&plan={plan_code}&data_agree={agree_data}',
                    failUrl: currentUrl + '?payment=fail',
                }})
            }})
        </script>
        """
        components.html(html_code, height=150)

    # ----------------------------------------------------------------------
    # 결제 완료 후: AI 분석 및 DB 저장 로직
    # ----------------------------------------------------------------------
    else:
        if "welcome_msg" not in st.session_state:
            st.toast("🎉 결제 성공! 분석을 시작합니다.", icon="✅")
            st.session_state["welcome_msg"] = True

        tone = st.radio("문자 말투 선택", ["👼 부드럽게", "⚖️ 단호하게"], index=0, horizontal=True)
        
        if st.button("🚀 AI 정밀 분석 시작 (Click)"):
            client = OpenAI(api_key=api_key)
            with st.spinner("AI가 계약서를 분석하고 데이터를 추출 중입니다..."):
                try:
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    
                    # [핵심] JSON Mode 프롬프트: 리포트와 DB데이터를 동시에 추출
                    system_prompt = f"""
                    당신은 부동산 법률 전문가입니다. 입력된 계약서 이미지를 분석하여 아래 JSON 포맷으로 응답하세요.
                    
                    1. user_report: 
                       - 독소조항 탐지(수리비, 즉시해지 등), 필수 특약 누락, 신탁 등기 여부를 상세히 분석.
                       - '{tone}' 톤으로 집주인에게 보낼 문자 메시지 초안 작성.
                       - Markdown 형식으로 가독성 있게 작성.
                    
                    2. db_data: 
                       - 통계 수집을 위한 데이터 추출.
                       - 개인정보(이름, 주민번호, 상세주소, 전화번호)는 절대 포함하지 말고 'XXX'로 마스킹하거나 제외할 것.
                       - district: 구/동 정보 (예: 마포구 서교동)
                       - deposit: 보증금 (숫자, 만약 없으면 0)
                       - rent: 월세 (숫자, 만약 없으면 0)
                       - toxic_clauses: 발견된 독소조항 리스트 (배열)
                       - risk_score: 위험도 점수 (0~100)
                    
                    반드시 유효한 JSON 형식이어야 합니다.
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": [
                                {"type": "text", "text": "분석해줘"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]}
                        ],
                        max_tokens=3000,
                        response_format={"type": "json_object"}  # JSON 모드 활성화
                    )
                    
                    # 결과 파싱
                    result = json.loads(response.choices[0].message.content)
                    user_report = result.get("user_report", "분석 결과가 없습니다.")
                    db_data = result.get("db_data", {})
                    
                    # [1] 사용자에게 리포트 보여주기
                    st.success("분석 완료!")
                    st.markdown(user_report)
                    
                    st.markdown("""
                    <div class="checklist-box">
                        <h4 style="color:#00e676;">🛑 필수 체크</h4>
                        <ul style="color:white;">
                            <li>✅ 입금 계좌주 = 집주인 이름 일치</li>
                            <li>✅ 신분증 진위 확인 (ARS 1382)</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # [2] 구글 시트에 데이터 저장 (백그라운드)
                    # 실제 결제 파라미터에서 동의 여부 확인 (URL 쿼리 활용)
                    agreed = query_params.get("data_agree", "True") 
                    
                    if agreed == "True":
                        db_data["plan_type"] = query_params.get("plan", "BASIC")
                        save_result = save_to_google_sheets(db_data)
                        if save_result:
                            print("DB 저장 성공")
                        else:
                            print("DB 저장 실패")
                    
                    # 환불 안내
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
# [필수] 사이트 하단 사업자 정보 (Footer)
# --------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px; line-height: 1.6;'>
    <b>세이프홈 Pro (SafeHome)</b> | 대표: 홍길동<br>
    사업자등록번호: 000-00-00000 (발급 진행 중) | 통신판매업신고: 준비 중<br>
    주소: 서울특별시 OO구 OO로 123<br>
    고객센터: 010-0000-0000 | 이메일: example@gmail.com<br>
    <br>
    <a href='#' style='color: #888; text-decoration: none;'>이용약관</a> | 
    <a href='#' style='color: #888; text-decoration: none;'>개인정보처리방침</a>
    <br><br>
    본 서비스는 AI 분석 결과로 법적 효력이 없으며, 최종 판단의 책임은 사용자에게 있습니다.
</div>
""", unsafe_allow_html=True)