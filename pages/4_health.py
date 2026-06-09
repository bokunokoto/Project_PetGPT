import streamlit as st
from datetime import date, timedelta
import sys, os
import pandas as pd
import calendar

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth
from db import (get_pets, get_schedules, add_schedule, complete_schedule,
                get_records, add_record, delete_record)

if "completed_schedule_ids" not in st.session_state:
    st.session_state.completed_schedule_ids = set()

if "selected_calendar_day" not in st.session_state:
    st.session_state.selected_calendar_day = date.today().day

auth.login_widget()

st.title("📒 건강 수첩")
st.write("반복 일정부터 병원 진료 내용까지, 우리 아이의 건강 기록을 관리하세요.")

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
        schedule_date = st.date_input("일정 날짜", value=date.today(), key="sch_schedule_date")
        repeat = st.radio("반복 여부", ["O", "X"], horizontal=True, key="sch_repeat")
        if repeat == "O":
            cycle_days = st.number_input("반복 주기 (일)", min_value=1, max_value=365, value=30, key="sch_cycle_days")
        else:
            cycle_days = 0

    if st.button("일정 등록", type="primary", key="add_schedule"):
        add_schedule(sch_pet_id, care_type, schedule_date, cycle_days, schedule_date)
        st.rerun()

    st.divider()

    today = date.today()
    st.subheader(f"🗓️ {today.year}년 {today.month}월 케어 달력")

    st.markdown("""
        <style>
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
            width: 100% !important;
            height: 100px !important;
            padding: 8px !important;
            border-radius: 6px !important;
            border: 1px solid rgba(128, 128, 128, 0.3) !important;
            background-color: transparent !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
            text-align: left !important;
            box-shadow: none !important;
        }
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) div[data-testid="stMarkdownContainer"] {
            width: 100% !important;
            text-align: left !important;
        }
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) p {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 13px !important;
            line-height: 1.4 !important;
            text-align: left !important;
            white-space: pre-wrap !important;
            word-break: break-all !important;
        }
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
            border-color: rgba(128, 128, 128, 0.8) !important;
            background-color: rgba(128, 128, 128, 0.05) !important;
        }
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):focus,
        div[data-testid="column"] div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):active {
            border: 2px solid rgba(128, 128, 128, 0.9) !important;
            box-shadow: none !important;
            outline: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    raw_schedules = get_schedules()
    schedules = [s for s in raw_schedules if s["id"] not in st.session_state.completed_schedule_ids]

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(today.year, today.month)

    week_headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for idx, h in enumerate(week_headers):
        color_style = "color:#888888;"
        if h == "일": color_style = "color:#e03e2d;"
        elif h == "토": color_style = "color:#2b6cb0;"
        cols_header[idx].markdown(f"<p style='text-align:center; font-weight:700; margin-bottom:5px; font-size:14px; {color_style}'>{h}</p>", unsafe_allow_html=True)

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

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                is_selected = (st.session_state.selected_calendar_day == day)

                if day == today.day:
                    button_content = f":blue[**{day}**]"
                else:
                    button_content = f"**{day}**"

                if is_selected:
                    button_content += " 👈"

                if day in schedule_map:
                    button_content += "\n"
                    for s in schedule_map[day]:
                        button_content += f"\n▪ {s['care_type']}"

                if cols[i].button(button_content, key=f"cal_day_{day}", use_container_width=True):
                    st.session_state.selected_calendar_day = day
                    st.rerun()

    sel_day = st.session_state.selected_calendar_day
    st.write("")
    st.markdown(f"#### 🔍 {sel_day}일 상세 일정 기록")

    day_schedules = schedule_map.get(sel_day, [])
    if not day_schedules:
        st.caption("선택한 날짜에 예정된 케어 일정이 없습니다. 달력의 날짜 블록을 클릭해 보세요.")
    else:
        for s in day_schedules:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                pet_display = (s.get("pet_name") or "").strip() or "이름 없음"
                c1.write(f"🐾 **{pet_display}** : `{s['care_type']}`")
                cycle_text = f"{s['cycle_days']}일마다 반복" if s.get("cycle_days") else "반복 없음"
                c1.caption(f"일정일: {s['next_due']} | {cycle_text}")
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
                    curr_day = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]
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
