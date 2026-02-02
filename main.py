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
    .price-box {
        background-color: #263238; padding: 15px; border-radius: 10px;
        border: 2px solid #00e676; text-align: center; margin-bottom: 15px;
    }
    div[data-testid="stToast"] { font-weight: bold; background-color: #00e676 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [보안] Secrets 키 가져오기
# --------------------------------------------------------------------------
# API 키가 없으면 에러가 나므로, secrets.toml 파일이 잘 있는지 확인해주세요.
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    toss_client_key = st.secrets.get("TOSS_CLIENT_KEY", "test_ck_DnyRpQWGrNzkLXLyLYegrKwv1M9E")
except Exception as e:
    st.error("Secrets 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
    st.stop()

# --------------------------------------------------------------------------
# [함수] 구글 시트 데이터 저장
# --------------------------------------------------------------------------
def save_to_google_sheets(data_json):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("safehome_db").sheet1 
        
        row = [
            str(datetime.datetime.now()),
            data_json.get("district", "Unknown"),
            data_json.get("deposit", 0),
            data_json.get("rent", 0),
            data_json.get("risk_score", 0),
            ", ".join(data_json.get("toxic_clauses", [])),
            data_json.get("plan_type", "Basic")
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"DB 저장 실패: {e}")
        return False

# --------------------------------------------------------------------------
# [UI] 사이드바 & 헤더
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_code = st.text_input("관리자 패스워드", type="password")
    is_admin = (admin_code == "safe2026")
    if is_admin:
        st.success("✅ 관리자 모드")

st.title("🏠 세이프홈 Pro")
st.markdown("### 대학생을 위한 **전세사기 방어 솔루션**")

# [기능 1] 파일 업로드
uploaded_file = st.file_uploader("계약서 사진 업로드", type=['jpg', 'png', 'jpeg'])

# --------------------------------------------------------------------------
# [로직] 요금제 선택 및 결제
# --------------------------------------------------------------------------
# URL에 결제 성공 정보가 있는지 확인
query_params = st.query_params
is_paid_success = ("payment" in query_params and query_params["payment"] == "success")
final_paid_status = is_paid_success or is_admin

if uploaded_file is not None:
    st.image(uploaded_file, caption='업로드된 계약서', use_container_width=True)

    # 결제 전 화면
    if not final_paid_status:
        st.divider()
        st.subheader("💰 요금제 선택")
        
        # 1. 요금제 선택 (라디오 버튼)
        plan_option = st.radio(
            "원하는 분석 수준을 선택하세요",
            ["🥉 Basic (필수 분석 + 문자 초안)", "🥇 Premium (Basic + 전문가용 요약본 PDF)"],
            index=0
        )
        
        # 2. 데이터 동의 체크박스
        agree_data = st.checkbox("네, 익명 데이터 제공에 동의하고 할인받겠습니다. (추천)", value=True)

        # 3. [중요] 가격 계산 로직 (여기가 핵심!)
        # Premium 글자가 포함되어 있으면 프리미엄 가격 적용
        if "Premium" in plan_option:
            base_price = 3900
            discounted_price = 2900
            plan_code = "PREMIUM"
        else:
            base_price = 990
            discounted_price = 790
            plan_code = "BASIC"
            
        final_price = discounted_price if agree_data else base_price
        
        # 4. 가격 확인용 UI (사용자가 눈으로 확인하도록)
        st.markdown(f"""
        <div class="price-box">
            <span style='color:#bbb; text-decoration:line-through;'>{base_price}원</span> → 
            <span style='font-size: 24px; font-weight: bold; color: #00e676;'>{final_price}원</span> 결제
        </div>
        """, unsafe_allow_html=True)

        # 5. 토스페이먼츠 결제 위젯
        # URL 생성
        base_url = "https://safehome-pro-kxtnyxxioyps79azjebgvi.streamlit.app"
        success_url = f"{base_url}?payment=success&plan={plan_code}&data_agree={agree_data}"
        fail_url = f"{base_url}?payment=fail"

        # HTML 코드 (높이를 height=600으로 늘려서 짤림 방지)
        html_code = f"""
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <div style="text-align: center; margin-top: 20px;">
            <button id="payment-button" style="background-color: #3182f6; color: white; padding: 16px 24px; border: none; border-radius: 12px; font-size: 17px; font-weight: bold; cursor: pointer; width: 100%;">
                {final_price}원 결제하기 (클릭)
            </button>
        </div>
        <script>
            var clientKey = '{toss_client_key}'
            var tossPayments = TossPayments(clientKey)
            var button = document.getElementById('payment-button')
            
            button.addEventListener('click', function () {{
                tossPayments.requestPayment('카드', {{
                    amount: {final_price},
                    orderId: 'ORDER_' + new Date().getTime(),
                    orderName: '전세사기 리포트_{plan_code}',
                    customerName: '세이프홈 고객',
                    successUrl: '{success_url}',
                    failUrl: '{fail_url}',
                }})
            }})
        </script>
        """
        # [핵심 수정] height를 800으로 넉넉하게 줘서 결제창이 안 짤리게 함
        components.html(html_code, height=800)

    # ----------------------------------------------------------------------
    # 결제 완료 후: AI 분석
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
                    
                    system_prompt = f"""
                    당신은 부동산 법률 전문가입니다. 입력된 계약서 이미지를 분석하여 아래 JSON 포맷으로 응답하세요.
                    
                    1. user_report: 
                       - 독소조항 탐지, 필수 특약 누락 분석.
                       - '{tone}' 톤으로 집주인에게 보낼 문자 메시지 초안.
                       - Markdown 형식.
                    
                    2. db_data: 
                       - district, deposit, rent, toxic_clauses, risk_score
                       - 개인정보는 마스킹(XXX) 처리.
                    
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
                        response_format={"type": "json_object"}
                    )
                    
                    result = json.loads(response.choices[0].message.content)
                    user_report = result.get("user_report", "분석 결과가 없습니다.")
                    db_data = result.get("db_data", {})
                    
                    st.success("분석 완료!")
                    st.markdown(user_report)
                    
                    # DB 저장 로직
                    agreed = query_params.get("data_agree", "True") 
                    if agreed == "True":
                        db_data["plan_type"] = query_params.get("plan", "BASIC")
                        save_to_google_sheets(db_data)
                        
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>세이프홈 Pro | AI 분석 결과는 법적 효력이 없습니다.</div>", unsafe_allow_html=True)