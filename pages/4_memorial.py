import streamlit as st
import pandas as pd

st.title("🕯️ 따뜻한 마지막 안녕")
st.write("신뢰할 수 있는 지역별 장례식장을 안내해 드립니다.")

region = st.selectbox("조회할 지역 선택", ["서울/경기", "부산/경남", "기타 지역"])

# 지도에 표시할 더미(가짜) 위도/경도 데이터 (추후 실제 CSV 데이터로 교체)
dummy_map_data = pd.DataFrame({
    'lat': [37.5665, 37.5500], # 위도 예시
    'lon': [126.9780, 126.9900] # 경도 예시
})

st.write("**📍 제휴 장례식장 위치**")
st.map(dummy_map_data) # 지도 출력

st.divider()

st.subheader("비대면 장례 상담 신청")
contact = st.text_input("연락처를 남겨주시면 전문 상담원이 안내해 드립니다.", placeholder="010-XXXX-XXXX")
if st.button("상담 신청하기"):
    st.success("신청이 완료되었습니다. 곧 연락드리겠습니다.")
