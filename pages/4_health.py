import streamlit as st
from datetime import date, timedelta
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from db import (get_pets, get_schedules, add_schedule, complete_schedule,
                get_records, add_record, delete_record)

auth.login_widget()

st.title("📒 건강 수첩")
st.write("예방접종·구충 같은 반복 일정부터 병원 진료 내용까지, "
         "우리 아이의 건강 기록을 한곳에서 관리하세요.")

pets = get_pets()                            # [{id, name, ...}, ...]
pet_options = {p["name"]: p["id"] for p in pets}   # 드롭다운 표시용

tab_schedule, tab_record, tab_medication = st.tabs(["📅 케어 일정", "🏥 진료 기록", "💊 투약 관리"])


def pet_picker(label, key, allow_text=True):
    """반려동물 선택 위젯. 등록된 게 없으면 텍스트 입력으로 대체."""
    if pet_options:
        name = st.selectbox(label, list(pet_options.keys()), key=key)
        return pet_options[name], name
    if allow_text:
        name = st.text_input(label, placeholder="이름 입력", key=key + "_txt")
        return None, name or "미지정"
    return None, "미지정"


# ════════════════════════════════════════════════════════════════════
# 탭 1. 케어 일정
# ════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader("➕ 일정 추가")

    col1, col2 = st.columns(2)
    with col1:
        sch_pet_id, _ = pet_picker("대상 반려동물", "sch_pet")
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
        add_schedule(sch_pet_id, care_type, last_done, cycle_days, next_due)
        st.success(f"'{care_type}' 일정이 등록되었어요.")
        st.rerun()

    st.divider()

    st.subheader("🔔 다가오는 일정")
    schedules = get_schedules()
    if not schedules:
        st.caption("아직 등록된 일정이 없어요.")
    else:
        today = date.today()
        for s in schedules:
            next_due = date.fromisoformat(s["next_due"])
            d_day = (next_due - today).days
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
                c1.write(f"**{s['pet_name'] or '미지정'}** · {s['care_type']}")
                c2.write(f"예정일: {next_due}  {label}")
                if c3.button("완료", key=f"done_{s['id']}"):
                    complete_schedule(s["id"], today, s["cycle_days"])
                    st.rerun()


# ════════════════════════════════════════════════════════════════════
# 탭 2. 진료 기록
# ════════════════════════════════════════════════════════════════════
with tab_record:
    st.subheader("🏥 진료 기록 추가")
    st.caption("병원에서 받은 진단·처방·검사 결과 등을 기록해 두면 다음 진료 때 도움이 됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        rec_pet_id, _ = pet_picker("대상 반려동물", "rec_pet")
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
            add_record(
                pet_id=rec_pet_id,
                visit_date=visit_date,
                hospital=hospital.strip(),
                visit_type=visit_type,
                weight=weight_at_visit if weight_at_visit > 0 else None,
                cost=cost,
                diagnosis=diagnosis.strip(),
                prescription=prescription.strip(),
                memo=memo.strip(),
            )
            st.success("진료 기록이 저장되었어요.")
            st.rerun()

    st.divider()

    st.subheader("📋 진료 이력")

    # 반려동물 필터
    filter_pet_id = None
    if pet_options:
        flt = st.selectbox("반려동물로 필터", ["전체"] + list(pet_options.keys()),
                           key="rec_filter")
        if flt != "전체":
            filter_pet_id = pet_options[flt]

    records = get_records(pet_id=filter_pet_id)

    if not records:
        st.caption("아직 진료 기록이 없어요.")
    else:
        total_cost = sum(r["cost"] or 0 for r in records)
        st.metric("누적 진료비", f"{total_cost:,}원")

        for r in records:
            title = f"{r['visit_date']} · {r['pet_name'] or '미지정'} · {r['visit_type']}"
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

                if st.button("이 기록 삭제", key=f"del_rec_{r['id']}"):
                    delete_record(r["id"])
                    st.rerun()
with tab_medication:
    st.subheader("💊 맞춤형 투약 스케줄러")

    # 1. 약 등록 섹션
    with st.form("med_add_form", clear_on_submit=True):
        new_med = st.text_input("약 이름", placeholder="예: 심장약")
        unit = st.radio("복용 주기 단위", ["매일", "주 단위", "월 단위"], horizontal=True)
        
        # 주 단위 선택 시
        days_of_week = []
        if unit == "주 단위":
            days_of_week = st.multiselect("요일 선택", ["월", "화", "수", "목", "금", "토", "일"])
        
        # 월 단위 선택 시
        day_of_month = None
        if unit == "월 단위":
            day_of_month = st.number_input("매월 며칠에 복용할지 입력 (1-31)", min_value=1, max_value=31, value=1)

        end_date = st.date_input("복용 종료일")
        
        if st.form_submit_button("일정 추가하기"):
            if new_med:
                if "med_list" not in st.session_state: st.session_state.med_list = []
                st.session_state.med_list.append({
                    "name": new_med, "end": end_date, "unit": unit,
                    "days": days_of_week, "date": day_of_month
                })
                st.rerun()

    st.divider()

    # 2. 오늘 복용 체크 섹션
    st.markdown("### ✅ 오늘 먹어야 할 약")
    today = date.today()
    day_map = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}

    if "med_list" in st.session_state:
        for idx, med in enumerate(st.session_state.med_list):
            if med["end"] >= today:
                should_take = False
                if med["unit"] == "매일": should_take = True
                elif med["unit"] == "주 단위":
                    current_day_name = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]
                    should_take = current_day_name in med["days"]
                elif med["unit"] == "월 단위":
                    should_take = (today.day == med["date"])

                if should_take:
                    # 체크박스 상태 유지 (날짜 바뀌면 초기화)
                    if "last_check_date" not in st.session_state or st.session_state.last_check_date != today:
                        st.session_state.checked_meds = []
                        st.session_state.last_check_date = today
                    
                    is_checked = st.checkbox(f"{med['name']} ({med['unit']})", key=f"check_{idx}", 
                                             value=idx in st.session_state.checked_meds)
                    if is_checked and idx not in st.session_state.checked_meds: st.session_state.checked_meds.append(idx)
                    elif not is_checked and idx in st.session_state.checked_meds: st.session_state.checked_meds.remove(idx)
        
        st.write("---")
        for idx, med in enumerate(st.session_state.med_list):
            if st.button(f"삭제: {med['name']}", key=f"del_{idx}"):
                st.session_state.med_list.pop(idx); st.rerun()
