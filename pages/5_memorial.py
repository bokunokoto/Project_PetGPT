import streamlit as st
import pandas as pd

st.title("🕯️ 따뜻한 마지막 안녕")
st.write("신뢰할 수 있는 지역별 장례식장을 안내해 드립니다.")

region = st.selectbox("조회할 지역 선택", ["서울/경기", "부산/경남", "기타 지역"])

# ── 지역별 더미 장례식장 데이터 (추후 실제 CSV 로 교체) ────────────
FACILITIES = {
    "서울/경기": [
        {"name": "포레스트 펫 추모관", "lat": 37.5665, "lon": 126.9780, "phone": "02-1234-5678"},
        {"name": "하늘정원 반려동물 장례", "lat": 37.5500, "lon": 126.9900, "phone": "031-222-3333"},
    ],
    "부산/경남": [
        {"name": "남해 펫 메모리얼", "lat": 35.1796, "lon": 129.0756, "phone": "051-444-5555"},
        {"name": "경남 반려동물 추모공원", "lat": 35.2280, "lon": 128.6810, "phone": "055-666-7777"},
    ],
    "기타 지역": [
        {"name": "중부 펫 힐링센터", "lat": 36.3504, "lon": 127.3845, "phone": "042-888-9999"},
    ],
}

facilities = FACILITIES[region]
df = pd.DataFrame(facilities)

st.write("**📍 제휴 장례식장 위치**")
st.map(df[["lat", "lon"]])

st.markdown("#### 제휴 시설 목록")
for f in facilities:
    with st.container(border=True):
        st.write(f"**{f['name']}**")
        st.caption(f"☎ {f['phone']}")

st.divider()

st.subheader("비대면 장례 상담 신청")
contact = st.text_input(
    "연락처를 남겨주시면 전문 상담원이 안내해 드립니다.",
    placeholder="010-XXXX-XXXX",
)
if st.button("상담 신청하기"):
    if contact.strip():
        st.success("신청이 완료되었습니다. 곧 연락드리겠습니다.")
    else:
        st.warning("연락처를 입력해 주세요.")
