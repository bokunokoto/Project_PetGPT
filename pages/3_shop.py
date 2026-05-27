import streamlit as st

st.title("🛍️ 큐레이션 용품 샵")
st.write("우리아이 생애주기에 꼭 필요한 용품만 엄선했습니다.")

# 카테고리 탭 생성
tab1, tab2, tab3 = st.tabs(["전체", "장난감/훈련", "위생/배변"])

with tab1:
    st.subheader("🔥 베스트셀러")
    col1, col2 = st.columns(2)
    with col1:
        st.write("🐾 프리미엄 덴탈 껌")
        st.write("**12,000원**")
        st.button("장바구니 담기", key="item1")
    with col2:
        st.write("🐾 먼지 없는 친환경 모래")
        st.write("**24,000원**")
        st.button("장바구니 담기", key="item2")

with tab2:
    st.write("장난감 목록 (데이터베이스 연결 예정)")

with tab3:
    st.write("위생용품 목록 (데이터베이스 연결 예정)")
