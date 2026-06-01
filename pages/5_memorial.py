import streamlit as st

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from utils import load_places, region_selectors, filter_places, render_results

auth.login_widget()

st.title("🕯️ 따뜻한 마지막 안녕")
st.write("내 위치(시/군/구/동)를 선택하면 가까운 반려동물 장례식장을 지도에 표시해 드립니다.")

st.divider()

df = load_places("facilities.csv")

sido, sigungu, dong = region_selectors(df, key_prefix="memorial")
filtered = filter_places(df, sido, sigungu, dong)

render_results(filtered, kind_label="장례식장")

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
