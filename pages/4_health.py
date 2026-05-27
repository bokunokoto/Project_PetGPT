import streamlit as st
from datetime import date, timedelta

st.title("📒 건강 수첩")
st.write("예방접종·구충 같은 반복 일정부터 병원 진료 내용까지, 우리 아이의 건강 기록을 한곳에서 관리하세요.")

# ── 상태 초기화 ────────────────────────────────────────────────────
if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "records" not in st.session_state:
    st.session_state.records = []   # 병원 진료 기록

pet_names = [p["name"] for p in st.session_state.get("pets", [])]

tab_schedule, tab_record = st.tabs(["📅 케어 일정", "🏥 진료 기록"])


# ════════════════════════════════════════════════════════════════════
# 탭 1. 케어 일정
# ════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader("➕ 일정 추가")

    col1, col2 = st.columns(2)
    with col1:
        if pet_names:
            pet = st.selectbox("대상 반려동물", pet_names, key="sch_pet")
        else:
            pet = st.text_input("대상 반려동물", placeholder="이름 입력", key="sch_pet_txt")
        care_type = st.selectbox(
            "케어 종류",
            ["예방접종", "심장사상충 약", "구충", "목욕/미용", "건강검진", "생일", "기타"],
        )
    with col2:
        last_done = st.date_input("최근 시행일", value=date.today())
        cycle_days = st.number_input("반복 주기 (일)", min_value=0, max_value=365,
                                     value=30, step=1,
                                     help="0이면 1회성 일정입니다.")

    if st.button("일정 등록", type="primary", key="add_schedule"):
        next_due = last_done + timedelta(days=cycle_days) if cycle_days else last_done
        st.session_state.schedules.append({
            "pet": pet or "미지정",
            "type": care_type,
            "last": last_done,
            "cycle": cycle_days,
            "next": next_due,
        })
        st.success(f"'{care_type}' 일정이 등록되었어요.")

    st.divider()

    st.subheader("🔔 다가오는 일정")
    schedules = st.session_state.schedules
    if not schedules:
        st.caption("아직 등록된 일정이 없어요.")
    else:
        today = date.today()
        for i, s in enumerate(sorted(schedules, key=lambda x: x["next"])):
            d_day = (s["next"] - today).days
            if d_day < 0:
                label = f"🔴 {-d_day}일 지남"
            elif d_day == 0:
                label = "🟠 오늘"
            elif d_day <= 7:
                label = f"🟡 D-{d_day}"
            else:
                label = f"🟢 D-{d_day}"

            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{s['pet']}** · {s['type']}")
                c2.write(f"예정일: {s['next']}  {label}")
                if c3.button("완료", key=f"done_{i}"):
                    if s["cycle"]:
                        s["last"] = today
                        s["next"] = today + timedelta(days=s["cycle"])
                    else:
                        st.session_state.schedules.remove(s)
                    st.rerun()


# ════════════════════════════════════════════════════════════════════
# 탭 2. 진료 기록
# ════════════════════════════════════════════════════════════════════
with tab_record:
    st.subheader("🏥 진료 기록 추가")
    st.caption("병원에서 받은 진단·처방·검사 결과 등을 기록해 두면 다음 진료 때 도움이 됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        if pet_names:
            rec_pet = st.selectbox("대상 반려동물", pet_names, key="rec_pet")
        else:
            rec_pet = st.text_input("대상 반려동물", placeholder="이름 입력", key="rec_pet_txt")
        visit_date = st.date_input("진료일", value=date.today(), key="visit_date")
        hospital = st.text_input("병원 이름", placeholder="예: OO 동물병원")
    with col2:
        visit_type = st.selectbox(
            "진료 유형",
            ["일반 진료", "예방접종", "정기검진", "수술", "응급", "치과", "기타"],
        )
        weight_at_visit = st.number_input("진료 시 체중 (kg)", min_value=0.0, step=0.1,
                                          help="0이면 기록하지 않습니다.")
        cost = st.number_input("진료비 (원)", min_value=0, step=1000)

    diagnosis = st.text_input("진단 / 증상", placeholder="예: 외이염, 슬개골 1기")
    prescription = st.text_area("처방 / 약", placeholder="예: 항생제 7일분, 귀 세정제")
    memo = st.text_area("메모 / 다음 진료 안내", placeholder="예: 2주 뒤 재방문, 식단 조절 권고")

    if st.button("진료 기록 저장", type="primary", key="add_record"):
        if not diagnosis.strip() and not memo.strip():
            st.warning("진단 내용이나 메모 중 하나는 입력해 주세요.")
        else:
            st.session_state.records.append({
                "pet": rec_pet or "미지정",
                "date": visit_date,
                "hospital": hospital.strip(),
                "type": visit_type,
                "weight": weight_at_visit,
                "cost": cost,
                "diagnosis": diagnosis.strip(),
                "prescription": prescription.strip(),
                "memo": memo.strip(),
            })
            st.success("진료 기록이 저장되었어요.")

    st.divider()

    st.subheader("📋 진료 이력")
    records = st.session_state.records

    if pet_names:
        flt = st.selectbox("반려동물로 필터", ["전체"] + pet_names, key="rec_filter")
        if flt != "전체":
            records = [r for r in records if r["pet"] == flt]

    if not records:
        st.caption("아직 진료 기록이 없어요.")
    else:
        total_cost = sum(r["cost"] for r in records)
        st.metric("누적 진료비", f"{total_cost:,}원")

        for i, r in enumerate(sorted(records, key=lambda x: x["date"], reverse=True)):
            title = f"{r['date']} · {r['pet']} · {r['type']}"
            with st.expander(title):
                if r["hospital"]:
                    st.write(f"🏥 **병원**: {r['hospital']}")
                if r["diagnosis"]:
                    st.write(f"🩺 **진단/증상**: {r['diagnosis']}")
                if r["prescription"]:
                    st.write(f"💊 **처방/약**: {r['prescription']}")
                if r["weight"]:
                    st.write(f"⚖️ **체중**: {r['weight']}kg")
                if r["cost"]:
                    st.write(f"💰 **진료비**: {r['cost']:,}원")
                if r["memo"]:
                    st.info(f"📝 {r['memo']}")

                if st.button("이 기록 삭제", key=f"del_rec_{r['date']}_{i}"):
                    st.session_state.records.remove(r)
                    st.rerun()
