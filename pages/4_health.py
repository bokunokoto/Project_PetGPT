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
# 탭 1. 케어 일정 (바둑판 격자형 진짜 달력 구현)
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
    
    schedules = get_schedules()
    
    # 현재 월의 일자 배열 가져오기 (일요일 시작을 위해 일요일=6 설정 변경 적용)
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(today.year, today.month)
    
    # 요일 헤더 표시
    week_headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for idx, h in enumerate(week_headers):
        cols_header[idx].markdown(f"<p style='text-align:center; font-weight:bold;'>{h}</p>", unsafe_allow_html=True)
        
    # 날짜별 일정 매핑
    schedule_map = {}
    for s in schedules:
        try:
            s_date = date.fromisoformat(s["next_due"]) if isinstance(s["next_due"], str) else s["next_due"]
            if s_date.year == today.year and s_date.month == today.month:
                if s_date.day not in schedule_map:
                    schedule_map[s_date.day] = []
                schedule_map[s_date.day].append(f"📌{s['pet_name'] or '아이'}:{s['care_type']}")
        except:
            pass

    # 바둑판 격자 렌더링
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")  # 이번 달이 아닌 공백 칸
            else:
                # 오늘 날짜는 배경 테두리를 다르게 강조
                box_style = "border:1px solid #ccc; border-radius:5px; padding:3px; min-height:80px;"
                if day == today.day:
                    box_style = "border:2px solid #ff4b4b; border-radius:5px; padding:3px; min-height:80px; background-color:#fff5f5;"
                
                # 달력 칸 만들기
                cell_html = f"<div style='{box_style}'><strong>{day}</strong>"
                if day in schedule_map:
                    for item in schedule_map[day]:
                        cell_html += f"<br><span style='font-size:11px; color:#333; background-color:#e1f5fe; border-radius:3px; padding:1px 2px; display:block; margin-top:2px;'>{item}</span>"
                cell_html += "</div>"
                
                cols[i].markdown(cell_html, unsafe_allow_html=True)

    st.write("")
    st.subheader("🔔 다가오는 일정 목록")
    for s in schedules:
        with st.container(border=True):
            st.write(f"**{s['pet_name'] or '미지정'}** · {s['care_type']} (예정일: {s['next_due']})")
            if st.button("완료", key=f"done_{s['id']}"):
                complete_schedule(s["id"], date.today(), s["cycle_days"])
                st.rerun()

# ════════════════════════════════════════════════════════════════════
# 탭 2. 진료 기록
# ════════════════════════════════════════════════════════════════════
with tab_record:
    st.subheader("🏥 진료 기록 추가")
    col1, col2 = st.columns(2)
    with col1:
        rec_pet_id, _ = pet_picker("대상 반려동물", "rec_pet")
        visit_date = st.date_input("진료일", value=date.today(), key="rec_visit_date")
        hospital = st.text_input("병원 이름", key="rec_hospital")
    with col2:
        visit_type = st.selectbox("진료 유형", ["일반 진료", "예방접종", "정기검진", "수술", "응급", "치과", "기타"], key="rec_visit_type")
        cost = st.number_input("진료비 (원)", min_value=0, step=1000, key="rec_cost")

    diagnosis = st.text_input("진단 / 증상", key="rec_diagnosis")
    prescription = st.text_area("처방 / 약", key="rec_prescription")
    memo = st.text_area("메모", key="rec_memo")

    if st.button("진료 기록 저장", type="primary", key="add_record"):
        add_record(rec_pet_id, visit_date, hospital, visit_type, 0, cost, diagnosis, prescription, memo)
        st.rerun()

    st.subheader("📋 진료 이력")
    records = get_records()
    if records:
        df = pd.DataFrame(records)
        st.download_button("📥 CSV 내보내기", df.to_csv(index=False), "records.csv", "text/csv", key="btn_download_csv")
        for r in records:
            with st.expander(f"{r['visit_date']} · {r['pet_name'] or '미지정'} · {r['visit_type']}"):
                st.write(f"🏥 병원: {r['hospital']} / 🩺 진단: {r['diagnosis']}")
                if st.button("삭제", key=f"del_{r['id']}"):
                    delete_record(r['id']); st.rerun()

# ════════════════════════════════════════════════════════════════════
# 탭 3. 투약 관리 (사용자 맞춤 전면 개선 완료)
# ════════════════════════════════════════════════════════════════════
with tab_medication:
    st.subheader("💊 맞춤형 투약 관리")
    
    med_name = st.text_input("약 이름", key="input_med_name")
    cycle = st.selectbox("반복 주기", ["매일", "매주", "매월", "매년"], key="input_cycle")
    
    # 주기를 바꿀 때 요일 선택 잔상이 남지 않도록 조건문 엄격화 분리
    sub_option = None
    if cycle == "매주":
        sub_option = st.multiselect("요일 선택 (중복 가능)", ["월", "화", "수", "목", "금", "토", "일"], key="input_opt_week")
    elif cycle == "매월":
        sub_option = st.number_input("매월 며칠에 복용하나요? (1-31일)", min_value=1, max_value=31, value=1,
