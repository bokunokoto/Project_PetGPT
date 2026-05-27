import streamlit as st

st.title("🥗 건강한 맞춤 식단 매니저")
st.write("우리 아이의 상태를 입력하면 하루 권장 칼로리와 영양 가이드를 계산해 드립니다.")

st.divider()

name = st.text_input("반려동물 이름", placeholder="예: 멍멍이")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("나이 (세)", min_value=0, max_value=30, step=1)
    species = st.radio("종류", ["강아지", "고양이"], horizontal=True)
with col2:
    weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1)
    neutered = st.checkbox("중성화 완료", value=True)

health_issues = st.multiselect(
    "특별히 신경 쓰고 싶은 건강 고민 (다중 선택 가능)",
    ["관절/뼈", "피부/모질", "체중 조절", "소화/장", "눈물 자국"],
)


# ── 칼로리 계산 (수의학 표준 공식) ──────────────────────────────────
def calc_calories(weight_kg, age, species, neutered, weight_control):
    """RER(휴식기 에너지요구량) → MER(일일 에너지요구량)"""
    # RER = 70 * (체중 ^ 0.75)
    rer = 70 * (weight_kg ** 0.75)

    # 생애주기/상태에 따른 계수
    if age < 1:
        factor = 2.5            # 성장기
    elif weight_control:
        factor = 1.0            # 체중 감량 목표
    elif neutered:
        factor = 1.6 if species == "강아지" else 1.2
    else:
        factor = 1.8 if species == "강아지" else 1.4

    return rer, rer * factor


# 건강 고민별 추천 성분
NUTRIENT_GUIDE = {
    "관절/뼈": "글루코사민, 콘드로이틴, 오메가3",
    "피부/모질": "오메가3·6, 비오틴, 아연",
    "체중 조절": "L-카르니틴, 고단백·저지방, 식이섬유",
    "소화/장": "프로바이오틱스, 프리바이오틱스(이눌린)",
    "눈물 자국": "저알러지 단백질, 충분한 수분 공급",
}

if st.button("맞춤 식단 분석하기", type="primary"):
    if not name:
        st.warning("반려동물의 이름을 입력해 주세요.")
    elif weight <= 0:
        st.warning("몸무게를 입력해 주세요.")
    else:
        weight_control = "체중 조절" in health_issues
        rer, mer = calc_calories(weight, age, species, neutered, weight_control)

        st.write(f"### {name}를 위한 맞춤 영양 설계 결과")

        m1, m2 = st.columns(2)
        m1.metric("하루 권장 칼로리", f"{mer:,.0f} kcal")
        m2.metric("휴식기 기초대사량(RER)", f"{rer:,.0f} kcal")

        # 일반 건사료 기준 대략적인 급여량 (약 3,500 kcal/kg 가정)
        grams = mer / 3500 * 1000
        st.info(f"💡 일반 건사료 기준 하루 약 **{grams:.0f}g** 정도가 적당해요. "
                "(제품 칼로리에 따라 달라질 수 있어요)")

        if health_issues:
            st.markdown("#### 추천 영양 성분")
            for issue in health_issues:
                st.write(f"- **{issue}**: {NUTRIENT_GUIDE[issue]}")

        # ── 프로필 등록 (사이드바·다른 페이지에서 공유) ──────────────
        if "pets" not in st.session_state:
            st.session_state.pets = []

        existing = [p for p in st.session_state.pets if p["name"] != name]
        existing.append({"name": name, "age": age, "weight": weight,
                         "species": species, "mer": round(mer)})
        st.session_state.pets = existing
        st.success(f"'{name}' 프로필이 저장되었어요. 사이드바에서 확인할 수 있어요!")