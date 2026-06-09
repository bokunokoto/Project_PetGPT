import streamlit as st
from datetime import date, timedelta
import sys, os
import pandas as pd

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from db import (get_pets, get_schedules, add_schedule, complete_schedule,
                get_records, add_record, delete_record)

auth.login_widget()

st.title("📒 건강 수첩")
pets = get_pets()
pet_options = {p["name"]: p["id"] for p in pets}

tab_schedule, tab_record, tab_medication = st.tabs(["📅 케어 일정", "🏥 진료 기록", "💊 투약 관리"])

def pet_picker(label, key, allow_text=True):
    if pet_options:
        name = st.selectbox(label, list(pet_options.keys()), key=key)
        return pet_options[name], name
    name = st.text_input(label, placeholder="이름 입력", key=key + "_txt")
    return None, name or "미지정"

# ════════════════════════════════════════════════════════════════════
# 탭 1. 케어 일정
# ════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader("➕ 일정 추가")
    col1, col2 = st.columns(2)
    with col1:
        sch_pet_id, _ = pet_picker("대상 반려동물", "sch_pet")
        care_type = st.selectbox("케어 종류", ["예방접종", "심장사상충 약", "구충", "목욕/미용", "건강검진", "생일", "기타"])
    with col2:
        last_done = st.date_input("최근 시행일", value=date.today())
        cycle_days = st.number_input("반복 주기 (일)", min_value=0, max_value=365, value=30)
    if st.button("일정 등록", type="primary", key="add_schedule"):
        add_schedule(sch_pet_id, care_type, last_done, cycle_days, last_done + timedelta(days=cycle_days))
        st.rerun()

    st.subheader("🔔 다가오는 일정")
    for s in get_schedules():
        with st.container(border=True):
            st.write(f"**{s['pet_name']}** · {s['care_type']}")
            if st.button("완료", key=f"done_{s['id']}"):
                complete_schedule(s["id"], date.today(), s["cycle_days"]); st.rerun()

# ════════════════════════════════════════════════════════════════════
# 탭 2. 진료 기록
# ════════════════════════════════════════════════════════════════════
with tab_record:
    st.subheader("🏥 진료 기록 추가")
    col1, col2 = st.columns(2)
    with col1:
        rec_pet_id, _ = pet_picker("대상 반려동물", "rec_pet")
        visit_date = st.date_input("진료일", value=date.today())
        hospital = st.text_input("병원 이름")
    with col2:
        visit_type = st.selectbox("진료 유형", ["일반 진료", "예방접종", "정기검진", "수술", "응급", "치과", "기타"])
        cost = st.number_input("진료비 (원)", min_value=0, step=1000)
    diagnosis = st.text_input("진단 / 증상")
    if st.button("진료 기록 저장", type="primary", key="add_record"):
        add_record(rec_pet_id, visit_date, hospital, visit_type, 0, cost, diagnosis, "", "")
        st.rerun()

    records = get_records()
    if records:
        df = pd.DataFrame(records)
        st.download_button("📥 CSV 내보내기", df.to_csv(index=False), "records.csv", "text/csv")
        for r in records:
            with st.expander(f"{r['visit_date']} · {r['pet_name']} · {r['visit_type']}"):
                st.write(f"병원: {r['hospital']} / 진단: {r['diagnosis']}")
                if st.button("삭제", key=f"del_{r['id']}"): delete_record(r['id']); st.rerun()

# ════════════════════════════════════════════════════════════════════
# 탭 3. 투약 관리 (요일 선택 잔상 문제 해결 버전)
# ════════════════════════════════════════════════════════════════════
with tab_medication:
    st.subheader("💊 맞춤형 투약 관리")
    
    # 1. 폼 밖에서 주기를 먼저 선택 (이래야 UI가 즉시 갱신됨)
    med_name = st.text_input("약 이름")
    cycle = st.selectbox("반복 주기", ["매일", "매주", "매월", "매년"])
    
    # 2. 선택값에 따라 동적으로 입력 필드 분기
    sub_opt = None
    if cycle == "매주":
        sub_opt = st.multiselect("요일 선택", ["월", "화", "수", "목", "금", "토", "일"])
    elif cycle == "매월":
        sub_opt = st.number_input("날짜 선택", 1, 31, 1)
    elif cycle == "매년":
        sub_opt = st.date_input("날짜 선택")
            
    end_date = st.date_input("반복 종료일")
    
    # 3. 마지막에 버튼을 눌러 저장
    if st.button("추가하기"):
        if med_name:
            if "med_list" not in st.session_state: st.session_state.med_list = []
            st.session_state.med_list.append({"name": med_name, "cycle": cycle, "opt": sub_opt, "end": end_date})
            st.rerun()

    st.markdown("### ✅ 오늘 먹어야 할 약")
    today = date.today()
    
    if "med_list" in st.session_state:
        # 이전에 체크된 항목들을 기억하기 위한 세션 추가
        if "checked_indices" not in st.session_state:
            st.session_state.checked_indices = set()

        for idx, med in enumerate(st.session_state.med_list):
            if med["end"] >= today:
                # ... (should_take 로직은 그대로 유지) ...
                
                # 체크박스 상태 확인
                is_checked = st.checkbox(f"{med['name']} ({med['cycle']})", key=f"check_{idx}")
                
                # '새로' 체크된 경우에만 toast 발생
                if is_checked and idx not in st.session_state.checked_indices:
                    st.toast(f"{med['name']} 복용 완료! 잘하셨어요 🐾", icon="✅")
                    st.session_state.checked_indices.add(idx)
                
                # 체크 해제된 경우 세션에서 제거
                elif not is_checked and idx in st.session_state.checked_indices:
                    st.session_state.checked_indices.remove(idx)
        
        st.write("---")
        for idx, med in enumerate(st.session_state.med_list):
            if st.button(f"삭제: {med['name']}", key=f"del_{idx}"):
                st.session_state.med_list.pop(idx); st.rerun()
