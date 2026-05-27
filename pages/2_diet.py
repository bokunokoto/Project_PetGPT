import streamlit as st

st.title("🥗 건강한 맞춤 식단 매니저")
st.write("우리 아이의 상태를 입력하면 최적의 사료와 영양 성분을 추천해 드립니다.")

st.divider()

name = st.text_input("반려동물 이름", placeholder="예: 멍멍이")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("나이 (세)", min_value=0, max_value=30, step=1)
with col2:
    weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1)

health_issues = st.multiselect(
    "특별히 신경 쓰고 싶은 건강 고민 (다중 선택 가능)", 
    ["관절/뼈", "피부/모질", "체중 조절", "소화/장", "눈물 자국"]
)

if st.button("맞춤 식단 분석하기", type="primary"):
    if name:
        st.write(f"**{name}**를 위한 맞춤 영양 설계 결과입니다.")
        st.info("추천 성분: 오메가3, 글루코사민 (데이터 연동 예정)")
    else:
        st.warning("반려동물의 이름을 입력해 주세요.")
