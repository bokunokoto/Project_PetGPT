import streamlit as st

st.title("🏠 나에게 꼭 맞는 가족 찾기")
st.write("간단한 설문을 통해 운명의 반려동물을 추천해 드립니다.")

st.divider() # 구분선

col1, col2 = st.columns(2)
with col1:
    pet_type = st.selectbox("선호하는 동물", ["강아지", "고양이", "상관없음"])
    living_env = st.radio("주거 환경", ["아파트/빌라", "단독주택", "마당 있는 집"])

with col2:
    activity_level = st.select_slider(
        "본인의 하루 활동량 (산책 가능 수준)", 
        options=["매우 적음", "보통", "매우 활동적"]
    )
    has_allergy = st.checkbox("가족 중 털 알러지가 있는 분이 있나요?")

if st.button("추천 리스트 보기", type="primary"):
    st.success("데이터베이스에서 조건에 맞는 반려동물을 찾고 있습니다... (데이터 연동 예정)")
    # 추후 JSON/CSV 데이터를 불러와 st.dataframe()이나 카드로 보여줄 자리
