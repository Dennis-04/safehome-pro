import streamlit as st

st.set_page_config(
    page_title="SafeHome Pro",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 SafeHome Pro")
st.subheader("내 소중한 보증금과 권리, AI가 지켜드립니다.")

st.markdown("""
---
### 👋 환영합니다!
왼쪽 사이드바에서 원하시는 서비스를 선택해주세요.

- **📄 계약서 분석:** 어려운 임대차 계약서, 독소조항이 없는지 3초 만에 검토해 드립니다.
- **⚖️ 거주 솔루션:** 집주인과의 갈등, 법적 효력이 있는 내용증명과 정중한 카톡 멘트로 해결해 드립니다.

---
""")

st.info("👈 왼쪽 사이드바(>)를 열어 메뉴를 선택하세요!")