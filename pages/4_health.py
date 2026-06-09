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

# 완료된 일정을 세션 상태에서 관리하여 즉시 삭제 필터링 처리
if "completed_schedule_ids" not in st.session_state:
    st.session_state.completed_schedule_ids = set()

# 클릭한 날짜 저장을 위한 세션 상태 초기화 (기본값: 오늘 날짜)
if "selected_calendar_day" not in st.session_state:
    st.session_state.selected_calendar_day = date.today().day

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
# 탭 1. 케어 일정 (네모 블록 전체가 버튼인 진짜 플랫 캘린더)
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
    
    # 🗓️ 플랫 스타일 바둑판 달력 뷰 제작
    today = date.today()
    st.subheader(f"🗓️ {today.year}년 {today.month}월 케어 캘린더")
    
    # 완료 처리된 일정을 제외하고 남은 일정만 로드
    raw_schedules = get_schedules()
    schedules = [s for s in raw_schedules if s["id"] not in st.session_state.completed_schedule_ids]
    
    # 달력 배열 생성 (일요일 시작: firstweekday=6)
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(today.year, today.month)
    
    # 요일 헤더 표시 (세련된 차콜 앤 그레이 플랫 스타일)
    week_headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for idx, h in enumerate(week_headers):
        color_style = "color:#555555;"
        if h == "일": color_style = "color:#e03e2d;"
        elif h == "토": color_style = "color:#2b6cb0;"
        cols_header[idx].markdown(f"<p style='text-align:center; font-weight:700; margin-bottom:10px; font-size:14px; {color_style}'>{h}</p>", unsafe_allow_html=True)
        
    # 날짜별 일정 매핑 (달력용 간단 뷰)
    schedule_map = {}
    for s in schedules:
        try:
            s_date = date.fromisoformat(s["next_due"]) if isinstance(s["next_due"], str) else s["next_due"]
            if s_date.year == today.year and s_date.month == today.month:
                if s_date.day not in schedule_map:
                    schedule_map[s_date.day] = []
                schedule_map[s_date.day].append(s)
        except:
            pass

    # 스타일 설정을 위한 custom CSS 주입 (Streamlit 기본 버튼의 둥근 테두리를 깎고 커스텀 사각형 달력으로 매핑)
    st.markdown("""
        <style>
        div.stButton > button {
            border-radius: 0px !important;
            padding: 6px !important;
            text-align: left !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 바둑판 격자 화면 출력 (네모 박스 자체를 클릭 가능한 단일 컴포넌트로 완전 통합)
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")  # 공백 칸
            else:
                is_selected = (st.session_state.selected_calendar_day == day)
                
                # 달력 내부에 들어갈 텍스트 구성 (날짜 숫자 + 간단 일정 라벨)
                button_content = f"{day}\n"
                if day in schedule_map:
                    for s in schedule_map[day]:
                        button_content += f"\n📎 {s['care_type']}"
                
                # 오늘 및 선택 여부에 따라 버튼의 강조 스타일 색상 적용 (각진 플랫 실버)
                if day == today.day:
                    # 오늘 날짜: 세련된 파스텔 블루 배경
                    btn_type = "secondary"
                    st.markdown(f"<style>#root div[data-testid='stHorizontalBlock'] div:nth-child({i+1}) button {{ border: 2px solid #007aff !important; background-color: #f4f9ff !important; }}</style>", unsafe_allow_html=True)
                elif is_selected:
                    # 선택된 날짜: 선명한 다크 챠콜 플랫 테두리
                    btn_type = "primary"
                else:
                    # 일반 날짜: 군더더기 없는 각진 흰색 실버 박스
                    btn_type = "secondary"
                
                # 별도의 글자나 [선택] 칸 없이 네모 블록 전체를 버튼화하여 클릭 시 연동 구현!
                if cols[i].button(button_content, key=f"square_day_{day}", type=btn_type, use_container_width=True):
                    st.session_state.selected_calendar_day = day
                    st.rerun()

    # 📋 바둑판 사각형 네모 블록 클릭 시 하단 상세 정보 활성화 섹션
    sel_day = st.session_state.selected_calendar_day
    st.write("")
    st.markdown(f"#### 🔍 {sel_day}일 상세 일정 기록 목록")
    
    day_schedules = schedule_map.get(sel_day, [])
    if not day_schedules:
        st.caption("선택한 날짜에 예정된 케어 일정이 없습니다. 달력의 사각형 블록을 클릭해 보세요.")
    else:
        for s in day_schedules:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"🐾 **{s['pet_name'] or '아이'}** : `{s['care_type']}`")
                c1.caption(f"최근 시행일: {s['last_done']} | 반복 주기: {s['cycle_days']}일")
                if c2.button("완료", key=f"done_day_{s['id']}", type="primary", use_container_width=True):
                    st.session_state.completed_schedule_ids.add(s["id"])
                    complete_schedule(s["id"], date.today(), s["cycle_days"])
                    st.toast(f"'{s['care_type']}' 일정을 완료하여 삭제했습니다! ✨", icon="✅")
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
# 탭 3. 투약 관리
# ════════════════════════════════════════════════════════════════════
with tab_medication:
    st.subheader("💊 맞춤형 투약 관리")
    
    med_name = st.text_input("약 이름", key="input_med_name")
    cycle = st.selectbox("반복 주기", ["매일", "매주", "매월", "매년"], key="input_cycle")
    
    sub_option = None
    if cycle == "매주":
        sub_option = st.multiselect("요일 선택 (중복 가능)", ["월", "화", "수", "목", "금", "토", "일"], key="input_opt_week")
    elif cycle == "매월":
        sub_option = st.number_input("매월 며칠에 복용하나요? (1-31일)", min_value=1, max_value=31, value=1, key="input_opt_month")
    elif cycle == "매년":
        c1, c2 = st.columns(2)
        month_opt = c1.selectbox("몇 월", list(range(1, 13)), index=0, key="input_opt_year_m")
        day_opt = c2.selectbox("몇 일", list(range(1, 32)), index=0, key="input_opt_year_d")
        sub_option = {"month": month_opt, "day": day_opt}
        
    end_date = st.date_input("반복 종료일", key="input_end_date")
    
    if st.button("추가하기", type="primary", key="btn_add_med"):
        if med_name:
            if "med_list" not in st.session_state: 
                st.session_state.med_list = []
            st.session_state.med_list.append({
                "name": med_name, "cycle": cycle, "opt": sub_option, "end": end_date, "start": date.today()
            })
            st.rerun()

    st.markdown("### ✅ 오늘 먹어야 할 약")
    
    if "checked_state" not in st.session_state:
        st.session_state.checked_state = {}
    if "last_date" not in st.session_state or st.session_state.last_date != today:
        st.session_state.checked_state = {}
        st.session_state.last_date = today

    if "med_list" in st.session_state and st.session_state.med_list:
        for idx, med in enumerate(st.session_state.med_list):
            if med["end"] >= today:
                opt = med.get("opt")
                should_take = False
                
                if med["cycle"] == "매일": 
                    should_take = True
                elif med["cycle"] == "매주" and opt:
                    curr_day = ["월","화","수","목","금","토","일"][today.weekday()]
                    should_take = curr_day in opt
                elif med["cycle"] == "매월" and opt: 
                    should_take = (today.day == opt)
                elif med["cycle"] == "매년" and opt: 
                    if isinstance(opt, dict):
                        should_take = (today.month == opt.get("month") and today.day == opt.get("day"))
                
                if should_take:
                    key = f"check_{idx}"
                    was_checked = st.session_state.checked_state.get(key, False)
                    is_checked = st.checkbox(f"{med['name']} ({med['cycle']})", key=key)
                    
                    if is_checked and not was_checked:
                        st.toast(f"{med['name']} 복용 완료! 잘하셨어요 🐾", icon="✅")
                    st.session_state.checked_state[key] = is_checked
        
        st.write("---")
        for idx, med in enumerate(st.session_state.med_list):
            if st.button(f"삭제: {med['name']}", key=f"del_{idx}"):
                st.session_state.med_list.pop(idx)
                st.rerun()
    else:
        st.caption("등록된 약이 없습니다.")
