import streamlit as st
from openai import OpenAI
import base64
import json
import streamlit.components.v1 as components
from utils import save_to_google_sheets

# --------------------------------------------------------------------------
# [페이지 설정]
# --------------------------------------------------------------------------
st.set_page_config(page_title="계약서 분석", page_icon="📄")

# 토스 스타일 (맛보기): 깔끔한 버튼, 카드형 UI
st.markdown("""
<style>
    .stApp { font-family: 'Pretendard', sans-serif; }
    .price-box {
        background-color: #f2f4f6; color: #4e5968; 
        padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 20px;
    }
    .premium-badge {
        background-color: #3182f6; color: white; padding: 4px 8px; 
        border-radius: 4px; font-size: 12px; font-weight: bold;
    }
    div[data-testid="stToast"] { font-weight: bold; background-color: #3182f6 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# Secrets 로드
api_key = st.secrets.get("openai", {}).get("api_key")
if not api_key:
    st.error("OpenAI API key is not configured. Add it to your secrets.toml as:\n[openai]\napi_key = \"YOUR_KEY\"")
    st.stop()

# TOSS key (optional)
toss_client_key = st.secrets.get("TOSS_CLIENT_KEY", "test_ck_DnyRpQWGrNzkLXLyLYegrKwv1M9E")

# --------------------------------------------------------------------------
# [사이드바] 관리자 & 설정
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_code = st.text_input("관리자 패스워드", type="password")
    is_admin = (admin_code == "safe2026")
    
    if is_admin:
        st.success("✅ 관리자 모드: 무료 통과 & 프리미엄 강제 적용 가능")

st.title("📄 계약서 안심 분석")
st.markdown("AI가 독소조항을 찾아내고, **안전한 계약**인지 진단해 드립니다.")

# 파일 업로드
uploaded_file = st.file_uploader("계약서(특약사항) 사진을 올려주세요", type=['jpg', 'png', 'jpeg'])

# --------------------------------------------------------------------------
# [로직] 요금제 선택 및 결제 상태 확인
# --------------------------------------------------------------------------
query_params = st.query_params
is_paid_success = ("payment" in query_params and query_params["payment"] == "success")
final_paid_status = is_paid_success or is_admin

if uploaded_file is not None:
    st.image(uploaded_file, caption='업로드된 계약서', use_container_width=True)

    # 1. 요금제 선택 UI (항상 보여주되, 결제완료 시 비활성화 느낌만 줌)
    if not final_paid_status:
        st.divider()
        st.subheader("💰 요금제 선택")
        
        plan_option = st.radio(
            "원하는 분석 수준을 선택하세요",
            ["🥉 Basic (필수 분석 + 문자 초안)", "🥇 Premium (전문가용 상세 리포트 + 법적 근거)"],
            index=1 # 테스트 편의를 위해 프리미엄 기본 선택
        )
        
        agree_data = st.checkbox("데이터 제공 동의 (할인 적용)", value=True)

        if "Premium" in plan_option:
            base_price = 3900; discounted_price = 2900; plan_code = "PREMIUM"
        else:
            base_price = 990; discounted_price = 790; plan_code = "BASIC"
            
        final_price = discounted_price if agree_data else base_price
        
        # 가격 표시
        st.markdown(f"""
        <div class="price-box">
            <span style='color:#b0b8c1; text-decoration:line-through; margin-right: 10px;'>{base_price}원</span>
            <span style='font-size: 24px; font-weight: bold; color: #3182f6;'>{final_price}원</span> 결제
        </div>
        """, unsafe_allow_html=True)

        # 토스 결제 위젯
        success_url = f"https://safehome-pro-kxtnyxxioyps79azjebgvi.streamlit.app?payment=success&plan={plan_code}&data_agree={agree_data}"
        fail_url = "https://safehome-pro-kxtnyxxioyps79azjebgvi.streamlit.app?payment=fail"

        html_code = f"""
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <button id="payment-button" style="background-color:#3182f6;color:white;padding:15px 20px;border:none;border-radius:12px;width:100%;font-size:16px;font-weight:bold;cursor:pointer;">
            {final_price}원 결제하기
        </button>
        <script>
            var tossPayments = TossPayments('{toss_client_key}')
            document.getElementById('payment-button').addEventListener('click', function () {{
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
        components.html(html_code, height=600)

    # 2. 결제 완료 (또는 관리자) 후 분석 로직
    else:
        # 관리자일 경우, 선택한 옵션이 없으면 기본값을 Premium으로 설정
        if 'plan_option' not in locals():
            # UI가 사라져서 변수가 없을 경우를 대비해 재정의
            st.info("🔓 관리자 권한으로 **Premium 기능**을 테스트합니다.")
            plan_code = "PREMIUM" 
        else:
            # 방금 선택한 값 유지
            pass

        st.divider()
        tone = st.radio("집주인에게 보낼 문자 말투", ["👼 부드럽게 (부탁조)", "⚖️ 단호하게 (법적근거)"], horizontal=True)
        
        if st.button("🚀 AI 정밀 분석 시작"):
            client = OpenAI(api_key=api_key)
            with st.spinner("🔍 계약서를 꼼꼼히 뜯어보는 중..."):
                try:
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    
                    # -------------------------------------------------------
                    # [핵심] 요금제에 따른 프롬프트 분기 (Premium vs Basic)
                    # -------------------------------------------------------
                    if plan_code == "PREMIUM":
                        role_description = "당신은 대한민국 최고의 부동산 전문 변호사입니다. 의뢰인의 보증금을 지키기 위해 아주 깐깐하게 분석해야 합니다."
                        output_instruction = """
                        [Premium 리포트 요구사항]
                        1. **독소조항 심층 분석**: 발견된 조항이 법적으로 왜 위험한지 '판례'나 '주택임대차보호법'을 인용해서 설명하세요.
                        2. **대응 전략(Action Plan)**: 이 조항을 무력화하기 위해 세입자가 특약에 추가해야 할 문구를 구체적으로 제시하세요.
                        3. **전문가 총평**: 계약 안전 점수와 함께 최종 계약 추천 여부를 100자 이내로 요약하세요.
                        """
                    else:
                        role_description = "당신은 부동산 계약 도우미입니다. 핵심적인 문제점만 빠르게 짚어주세요."
                        output_instruction = """
                        [Basic 리포트 요구사항]
                        1. 독소조항이 있는지 없는지 O/X 위주로 간단히 체크하세요.
                        2. 문제가 있다면 수정 요청 문자 초안을 작성하세요.
                        """

                    system_prompt = f"""
                    {role_description}
                    
                    사용자가 업로드한 전세 계약서 이미지를 분석하여 아래 JSON 포맷으로 응답하세요.
                    (마크다운 ```json 태그 금지, 순수 JSON만 출력)

                    {output_instruction}
                    
                    - 문자 말투: {tone}
                    
                    [JSON 출력 필드]
                    {{
                        "user_report": "분석 결과 전문 (Markdown 형식으로 가독성 있게, 이모지 활용)",
                        "db_data": {{
                            "district": "구/동",
                            "deposit": 0,
                            "rent": 0,
                            "toxic_clauses": ["조항1", "조항2"],
                            "risk_score": 0
                        }}
                    }}
                    """
                    
                    # AI 호출
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": [
                                {"type": "text", "text": "분석 부탁해. 개인정보는 가려줘."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]}
                        ],
                        max_tokens=4000,
                        response_format={"type": "json_object"}
                    )

                    # 후처리 및 결과 표시
                    raw_content = response.choices[0].message.content
                    if not raw_content:
                        st.error("AI 응답 없음")
                        st.stop()
                        
                    clean_content = raw_content.replace("```json", "").replace("```", "").strip()
                    result = json.loads(clean_content)
                    
                    user_report = result.get("user_report")
                    db_data = result.get("db_data")
                    
                    # [Premium 전용 UI] 리포트 다운로드 버튼
                    if plan_code == "PREMIUM":
                        st.markdown("<span class='premium-badge'>👑 Premium Report</span>", unsafe_allow_html=True)
                        st.success("상세 분석이 완료되었습니다.")
                        st.markdown(user_report)
                        
                        # 텍스트 파일로 리포트 다운로드 기능
                        st.download_button(
                            label="📥 전문가 리포트 다운로드 (Text)",
                            data=user_report,
                            file_name="SafeHome_Premium_Report.md",
                            mime="text/markdown"
                        )
                    else:
                        st.success("기본 분석이 완료되었습니다.")
                        st.markdown(user_report)
                        st.info("💡 Premium으로 업그레이드하면 '법적 근거'와 '대응 전략'을 볼 수 있습니다.")

                    # DB 저장 (할인 동의 시)
                    if query_params.get("data_agree", "True") == "True" and db_data:
                        db_data["plan_type"] = plan_code
                        save_to_google_sheets(db_data)

                except Exception as e:
                    st.error(f"오류: {e}")