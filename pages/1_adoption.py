import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth

auth.login_widget()

st.title("🏠 나에게 꼭 맞는 가족 찾기")
st.write("간단한 설문을 통해 운명의 반려동물을 추천해 드립니다.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    pet_type = st.selectbox("선호하는 동물", ["강아지", "고양이", "상관없음"])
    living_env = st.radio("주거 환경", ["아파트/빌라", "단독주택", "마당 있는 집"])

with col2:
    activity_level = st.select_slider(
        "본인의 하루 활동량 (산책 가능 수준)",
        options=["매우 적음", "보통", "매우 활동적"],
    )
    has_allergy = st.checkbox("가족 중 털 알러지가 있는 분이 있나요?")


# ── 더미 후보 데이터 (추후 CSV/DB 로 교체) ─────────────────────────
CANDIDATES = [
    {"name": "보리", "type": "강아지", "breed": "푸들", "size": "소형",
     "energy": "보통", "low_allergy": True, "desc": "사람을 잘 따르는 온순한 성격"},
    {"name": "초코", "type": "강아지", "breed": "리트리버", "size": "대형",
     "energy": "매우 활동적", "low_allergy": False, "desc": "산책과 놀이를 좋아하는 활발한 친구"},
    {"name": "나비", "type": "고양이", "breed": "코리안숏헤어", "size": "소형",
     "energy": "매우 적음", "low_allergy": False, "desc": "혼자서도 잘 노는 독립적인 성격"},
    {"name": "두부", "type": "고양이", "breed": "스핑크스", "size": "소형",
     "energy": "보통", "low_allergy": True, "desc": "털 빠짐이 적어 알러지 걱정이 덜한 묘종"},
    {"name": "콩이", "type": "강아지", "breed": "비숑", "size": "소형",
     "energy": "보통", "low_allergy": True, "desc": "아파트 생활에 적합한 차분한 성격"},
]


def score(c):
    """간단한 가중치 매칭 점수 계산"""
    s = 0
    if pet_type == "상관없음" or c["type"] == pet_type:
        s += 3
    if activity_level == c["energy"]:
        s += 2
    if living_env == "아파트/빌라" and c["size"] == "소형":
        s += 1
    if has_allergy and c["low_allergy"]:
        s += 2
    elif has_allergy and not c["low_allergy"]:
        s -= 2
    return s


if st.button("추천 리스트 보기", type="primary"):
    ranked = sorted(CANDIDATES, key=score, reverse=True)
    top = [c for c in ranked if score(c) > 0][:3]

    if not top:
        st.warning("조건에 딱 맞는 친구를 찾지 못했어요. 조건을 조금 완화해 보세요.")
    else:
        st.success(f"입력하신 조건에 맞는 {len(top)}마리를 찾았어요!")
        cols = st.columns(len(top))
        for col, c in zip(cols, top):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {c['name']}")
                    st.write(f"**{c['type']} · {c['breed']}**")
                    st.caption(c["desc"])
                    if has_allergy and c["low_allergy"]:
                        st.write("✅ 알러지 저자극 묘/견종")
                    st.write(f"활동량: {c['energy']} / 크기: {c['size']}")
