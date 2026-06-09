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
tab_schedule, tab_record, tab_medication = st.tabs(["📅 케어 일정", "🏥 진료 기록", "💊 투약 관리"])

def pet_picker(label, key, allow_text=True):
    pets = get_pets()
    pet_options = {p["name"]: p["id"] for p in pets}
    if pet_options:
        name = st.selectbox(label, list(pet_options.keys()), key=key)
        return pet_options[name], name
    name = st.text_input(label, placeholder="이름 입력", key=key + "_txt")
    return None, name or "미지정"

# ════════════════════════════════════════════════════════════════════
# 탭 3. 투약 관리 (아이폰 스타일 상세 반복 설정)
# ════════════════════════════════════════════════════════════════════
with tab_medication:
    st.subheader("💊 맞춤형 투약 관리")
    
    with st.form("med_form", clear_on_submit=True):
        med_name = st.text_input("약 이름")
        cycle = st.selectbox("반복 주기", ["매일", "매주", "매월", "매년"])
        
        # 주기별 상세 옵션
        sub_option = None
        if cycle == "매주":
            sub_option = st.multiselect("요일 선택", ["월", "화", "수", "목", "금", "토", "일"])
        elif cycle == "매월":
            sub_option = st.number_input("매월 며칠에 복용?", 1, 31, 1)
        elif cycle == "매년":
            sub_option = st.date_input("매년 언제 복용?")
            
        end_date = st.date_input("반복 종료일")
        
        if st.form_submit_button("추가하기"):
            if med_name:
                if "med_list" not in st.session_state: st.session_state.med_list = []
                st.session_state.med_list.append({
                    "name": med_name, "cycle": cycle, "opt": sub_option, "end": end_date
                })
                st.rerun()

    st.markdown("### ✅ 오늘 먹어야 할 약")
    today = date.today()
    
    if "med_list" in st.session_state:
        if "last_date" not in st.session_state or st.session_state.last_date != today:
            st.session_state.checked = []
            st.session_state.last_date = today

        for idx, med in enumerate(st.session_state.med_list):
            if med["end"] >= today:
                should_take = False
                if med["cycle"] == "매일": should_take = True
                elif med["cycle"] == "매주":
                    day_map = {"월":0, "화":1, "수":2, "목":3, "금":4, "토":5, "일":6}
                    curr_day = ["월","화","수","목","금","토","일"][today.weekday()]
                    should_take = curr_day in med["opt"]
                elif med["cycle"] == "매월": should_take = (today.day == med["opt"])
                elif med["cycle"] == "매년": should_take = (today.month == med["opt"].month and today.day == med["opt"].day)

                if should_take:
                    if st.checkbox(f"{med['name']} ({med['cycle']})", key=f"check_{idx}"):
                        st.toast(f"{med['name']} 복용 완료! 잘하셨어요 🐾", icon="✅")
        
        st.write("---")
        for idx, med in enumerate(st.session_state.med_list):
            if st.button(f"삭제: {med['name']}", key=f"del_{idx}"):
                st.session_state.med_list.pop(idx); st.rerun()
