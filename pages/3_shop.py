import streamlit as st

st.title("🛍️ 큐레이션 용품 샵")
st.write("우리 아이 생애주기에 꼭 필요한 용품만 엄선했습니다.")

if "cart" not in st.session_state:
    st.session_state.cart = {}


def add_to_cart(item_name, price):
    cart = st.session_state.cart
    if item_name in cart:
        cart[item_name]["qty"] += 1
    else:
        cart[item_name] = {"price": price, "qty": 1}


def product_card(name, price, key):
    with st.container(border=True):
        st.write(name)
        st.write(f"**{price:,}원**")
        st.button("장바구니 담기", key=key,
                  on_click=add_to_cart, args=(name, price))


# ── 상품 목록 (추후 DB 연결) ────────────────────────────────────────
PRODUCTS = {
    "장난감/훈련": [
        ("🦴 노즈워크 장난감", 15000),
        ("🎾 자동 공 던지기", 39000),
        ("🪢 터그 로프", 8000),
    ],
    "위생/배변": [
        ("🐾 먼지 없는 친환경 모래", 24000),
        ("🧻 배변 패드 100매", 18000),
        ("🧼 무향 물티슈", 5000),
    ],
}
BEST = [("🐾 프리미엄 덴탈 껌", 12000), ("🐾 먼지 없는 친환경 모래", 24000)]

tab1, tab2, tab3 = st.tabs(["전체", "장난감/훈련", "위생/배변"])

with tab1:
    st.subheader("🔥 베스트셀러")
    cols = st.columns(2)
    for col, (n, p) in zip(cols, BEST):
        with col:
            product_card(n, p, key=f"best_{n}")

with tab2:
    cols = st.columns(2)
    for i, (n, p) in enumerate(PRODUCTS["장난감/훈련"]):
        with cols[i % 2]:
            product_card(n, p, key=f"toy_{n}")

with tab3:
    cols = st.columns(2)
    for i, (n, p) in enumerate(PRODUCTS["위생/배변"]):
        with cols[i % 2]:
            product_card(n, p, key=f"hyg_{n}")


# ── 사이드바 장바구니 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛒 장바구니")
    cart = st.session_state.cart
    if not cart:
        st.caption("비어 있습니다.")
    else:
        total = 0
        for name, info in list(cart.items()):
            line = info["price"] * info["qty"]
            total += line
            st.write(f"{name} × {info['qty']} — {line:,}원")
        st.markdown(f"**합계: {total:,}원**")
        if st.button("장바구니 비우기"):
            st.session_state.cart = {}
            st.rerun()