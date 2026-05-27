import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="Pet-E2E: 반려동물 통합 케어", layout="wide")

# 사이드바 내비게이션
st.sidebar.title("🐾 Pet-E2E 메뉴")
menu = st.sidebar.radio("서비스 이동", ["홈", "맞춤 입양", "식단 관리", "용품 쇼핑", "장례 서비스"])

# 1. 홈 화면
if menu == "홈":
    st.title("반려동물 생애주기 통합 관리 서비스")
    st.subheader("입양부터 마지막 순간까지, Pet-E2E가 함께합니다.")
    st.info("왼쪽 메뉴를 선택하여 각 서비스를 이용해 보세요.")

# 2. 맞춤 입양 서비스
elif menu == "맞춤 입양":
    st.title("🏠 나에게 꼭 맞는 가족 찾기")
    st.write("간단한 설문을 통해 운명의 반려동물을 추천해 드립니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("선호하는 동물", ["강아지", "고양이", "기타"])
        living_env = st.radio("주거 환경", ["아파트", "단독주택", "원룸"])
    with col2:
        activity_level = st.slider("활동량 선호도", 1, 5, 3)
    
    if st.button("맞춤 반려동물 추천받기"):
        st.success(f"{pet_type}를 위한 추천 리스트를 준비 중입니다... (CSV 데이터 연결 필요)")
        # st.dataframe(pet_data_filtered) 구조로 출력 예정

# 3. 식단 관리
elif menu == "식단 관리":
    st.title("🥗 건강한 맞춤 식단 매니저")
    name = st.text_input("반려동물 이름")
    age = st.number_input("나이 (세)", min_value=0)
    weight = st.number_input("몸무게 (kg)", min_value=0.0)
    health_issue = st.multiselect("건강 고민", ["피부", "관절", "비만", "알러지", "소화"])
    
    if st.button("추천 식단 생성"):
        st.write(f"**{name}**를 위한 맞춤 영양 설계 결과입니다.")
        st.progress(85) # 영양 밸런스 예시
        st.write("- 권장 칼로리: 450kcal/day")
        st.write("- 추천 성분: 오메가3, 저지방 단백질")

# 4. 용품 쇼핑
elif menu == "용품 쇼핑":
    st.title("🛍️ 큐레이션 용품 샵")
    category = st.tabs(["전체", "장난감", "위생용품", "의류"])
    
    with category[0]:
        st.write("인기 용품 리스트 (데이터베이스 연결 예정)")
        st.button("장바구니 담기 - 프리미엄 개껌")
        st.button("장바구니 담기 - 친환경 모래")

# 5. 장례 서비스
elif menu == "장례 서비스":
    st.title("🕯️ 따뜻한 마지막 안녕")
    st.write("신뢰할 수 있는 지역별 장례식장을 안내해 드립니다.")
    
    region = st.selectbox("지역 선택", ["서울", "경기", "인천", "기타"])
    st.map() # 실제 좌표 데이터를 연결하면 지도에 식장이 표시됩니다.
    
    if st.button("장례 상담 신청하기"):
        st.success("상담원이 곧 연락드릴 예정입니다.")
