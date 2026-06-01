import streamlit as st

# 프로젝트 루트의 utils.py 를 import 할 수 있도록 경로 추가
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from utils import load_places, region_selectors, filter_places, render_results

auth.login_widget()

st.title("🛍️ 내 주변 펫 용품점 찾기")
st.write("내 위치(시/군/구/동)를 선택하면 가까운 반려동물 용품점을 지도에 표시해 드립니다.")

st.divider()

df = load_places("stores.csv")

sido, sigungu, dong = region_selectors(df, key_prefix="shop")
filtered = filter_places(df, sido, sigungu, dong)

render_results(filtered, kind_label="용품점")
