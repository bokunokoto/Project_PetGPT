import streamlit as st
from datetime import date, timedelta
import sys, os
import pandas as pd
import calendar

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from db import (get_pets, get_schedules, add_schedule, complete_schedule,
                get_records, add_record, delete_record)

# 만약 db 모듈에 일정 자체를 완전히 삭제하는 기능이 없다면, 
# 완료된 일정을 화면에서 안 보이게 필터링하기 위해 세션 유기적 관리 기능을 추가했습니다.
if "completed_schedule_ids" not in st.session_state:
    st.session_state.completed_schedule_ids = set()

auth.login_widget()

st.title("📒 건강 수첩")
st.write("반복 일정부터 병원 진료 내용까지, 우리 아이의 건강 기록을 관리하세요.")

# pets 데이터 로드
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
# 탭 1. 케어 일정 (완료 시 즉시 삭제 및 달력 연동 반영)
# ════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader("➕ 일정 추가")
    col1, col2 = st.columns(2)
    with col1:
        sch_pet_id, _ = pet_picker("대상 반려동물", "sch_pet")
        care_type = st.selectbox("케어 종류", ["예방접종", "심장사상충 약", "구충", "목욕/미용", "건강검진", "생일", "기타"])
    with col2:
        last_done = st.date_input("최근 시행일", value=date.today(), key="sch_last_done")
        cycle_days = st.number_input("반복 주기 (일)", min_value=0, max_value=365, value=30, key="sch_cycle_days")

    if st.button("일정 등록", type="primary", key="add_schedule"):
        next_due = last_done + timedelta(days=cycle_days) if cycle_days else last_done
        add_schedule(sch_pet_id, care_type, last_done, cycle_days, next_due)
        st.rerun()

    st.divider()
    
    # 🗓️ 진짜 아이폰 스타일 바둑판 달력 뷰 제작
    today = date.today()
    st.subheader(f"🗓️ {today.year}년 {today.month}월 케어 캘린더")
    
    # DB에서 전체 일정을 가져온 뒤, 완료(삭제) 버튼을 누른 일정은 필터링해서 제외
    raw_schedules = get_schedules()
    schedules = [s for s in raw_schedules if s["id"] not in st.session_state.completed_schedule_ids]
    
    # 현재 월의 일자 배열 가져오기 (일요일 시작: firstweekday=6)
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(today.year, today.month)
    
    # 요일 헤더 표시
    week_headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for idx, h in enumerate(week_headers):
        cols_header[idx].markdown(f"<p style='text-align:center; font-weight:bold; margin-bottom:5px;'>{h}</p>", unsafe_allow_html=True)
        
    # 날짜별 일정 매핑
    schedule_map = {}
    for s in schedules:
        try:
            s_date = date.fromisoformat(s["next_due"]) if isinstance(s["next_due"], str) else s["next_due"]
            if s_date.year == today.year and s_date.month == today.month:
                if s_date.day not in schedule_map:
                    schedule_map[s_date.day] = []
                schedule_map[s_date.day].append(f"📌 {s['pet_name'] or '아이'}: {s['care_type']}")
        except:
            pass

    # 바둑판 격자 렌더링
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")  # 이번 달이 아닌 공백 칸
            else:
                # 오늘 날짜는 테두리를 빨간색으로 다르게 강조
                box_style = "border:1px solid #ccc; border-radius:5px; padding:5px; min-height:85px; width:100%;"
                if day == today.day:
                    box_style = "border:2px solid #ff4b4b; border-radius:5px; padding:5px; min-height:85px; background
