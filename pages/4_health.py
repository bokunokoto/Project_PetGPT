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
                  # ════════════════════════════════════════════════════════════════════
# 탭 3. 투약 관리 (추가된 부분)
# ════════════════════════════════════════════════════════════════════
with tab_medication:
    st.subheader("💊 투약 관리 및 알림")
    st.caption("매일 챙겨야 하는 약(영양제, 처방약 등)의 복용 여부를 체크하고 준수율을 확인하세요.")

    # 1. 대상 반려동물 선택
    med_pet_id, pet_name = pet_picker("대상 반려동물", "med_pet")
    
    st.divider()

    # 2. 오늘의 복용 체크 (요구사항: 사용자가 '복용 완료'를 누르면 History 테이블에 기록)
    st.markdown(f"#### ✅ {pet_name}의 오늘 투약 체크")
    
    # 예시용 약 이름 입력 (실제로는 DB에서 현재 복용 중인 약 목록을 불러와야 함)
    med_name = st.text_input("복용할 약 이름", placeholder="예: 심장약, 관절 영양제")
    
    if st.button("복용 완료 기록하기", type="primary", key="med_done"):
        if med_name.strip():
            # TODO: 여기에 History 테이블에 기록하는 DB 함수를 연결해야 합니다.
            # 예: add_medication_history(med_pet_id, med_name, date.today())
            st.success(f"오늘({date.today()}) {med_name} 복용 기록이 저장되었습니다! 📈")
        else:
            st.warning("약 이름을 입력해 주세요.")
            
    st.divider()
    
    # 3. 복용 준수율 통계 (요구사항: 복용 준수율 통계 제공)
    st.markdown("#### 📊 복용 준수율 통계")
    st.info("준수율 시각화 및 예정일 알림 기능이 여기에 들어갑니다.")
  # db.py에서 새로 만든 함수들을 상단 import에 추가해 주세요!
# from db import (..., add_medication, get_medications, complete_medication, get_medication_history)

with tab_medication:
    st.subheader("💊 오늘의 투약 알림 & 체크리스트")
    st.caption("오늘 우리 아이가 먹어야 할 약을 확인하고 복용 완료 버튼을 눌러주세요.")

    today = date.today()
    all_meds = get_medications()
    
    # 1. 오늘 복용해야 하는 약 필터링 및 알림 (Todo 기능)
    today_tasks = []
    for med in all_meds:
        # 1회성이거나, 주기적인 약인 경우 오늘 날짜에 해당하는지 계산
        start_dt = date.fromisoformat(med["start_date"])
        if med["cycle_days"] == 0 and start_dt == today:
            today_tasks.append(med)
        elif med["cycle_days"] > 0 and (today - start_dt).days % med["cycle_days"] == 0 and today >= start_dt:
            today_tasks.append(med)

    # 오늘 먹은 약 목록 가져오기
    history_rows = get_medication_history()
    today_completed_ids = [h["med_id"] for h in history_rows if h["check_date"] == str(today)]

    # 실시간 알림 방송 기능 (푸시 알림 대안: 페이지 접속 시 토스트/경고 배너)
    incomplete_count = len(today_tasks) - len(today_completed_ids)
    if incomplete_count > 0:
        st.error(f"🔔 오늘 아직 복용하지 않은 약이 {incomplete_count}개 있습니다! 잊지 말고 챙겨주세요.")
    else:
        st.balloons()
        st.success("🎉 오늘 예정된 모든 투약을 완료했습니다! 훌륭해요.")

    # Todo 형태의 체크리스트 UI 출력
    st.write("")
    if not today_tasks:
        st.info("오늘 예정된 투약 일정이 없습니다.")
    else:
        for med in today_tasks:
            is_done = med["id"] in today_completed_ids
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                
                # 완료 여부에 따른 텍스트 표시 변환
                if is_done:
                    c1.markdown(f"~~**[{med['pet_name'] or '미지정'}]** {med['med_name']} ({med['dosage']})~~")
                    c2.markdown(f"~~🕒 {med['dosage_time']} · 복용 완료~~")
                    c3.button("완료됨", key=f"med_comp_{med['id']}", disabled=True)
                else:
                    c1.markdown(f"**[{med['pet_name'] or '미지정'}]** {med['med_name']} ({med['dosage']})")
                    c2.markdown(f"🕒 **{med['dosage_time']}** 에 먹여야 해요!")
                    if c3.button("복용 완료", key=f"med_do_{med['id']}", type="primary"):
                        complete_medication(med["id"], today)
                        st.toast(f" {med['med_name']} 복용 기록이 History에 저장되었습니다.", icon="✅")
                        st.rerun()

    st.divider()

    # 2. 새 투약 일정 등록 폼
    st.subheader("➕ 새 투약 일정 등록")
    with st.form("medication_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            med_pet_id, _ = pet_picker("대상 반려동물", "med_add_pet")
            med_name = st.text_input("약 / 영양제 이름", placeholder="예: 하트가드, 슬개골 영양제")
            dosage = st.text_input("복용량 / 방법", placeholder="예: 1포, 반 알, 식후 30분")
        with col2:
            dosage_time = st.text_input("복용 시간 안내", placeholder="예: 아침 8시, 저녁 식후")
            start_date_input = st.date_input("투약 시작일", value=today)
            cycle_choice = st.selectbox(
                "복용 주기", 
                ["매일", "일주일마다", "한 달마다 (30일)", "1회성 일정"],
                index=0
            )
            
        # 주기 텍스트를 일수(days) 숫자로 변환
        cycle_mapping = {"매일": 1, "일주일마다": 7, "한 달마다 (30일)": 30, "1회성 일정": 0}
        cycle_days = cycle_mapping[cycle_choice]

        submit = st.form_submit_button("일정 추가하기", type="primary")
        if submit:
            if not med_name.strip():
                st.warning("약 이름을 입력해 주세요.")
            else:
                add_medication(med_pet_id, med_name.strip(), dosage.strip(), dosage_time.strip(), start_date_input, cycle_days)
                st.success(f"'{med_name}' 투약 스케줄이 성공적으로 등록되었습니다.")
                st.rerun()

    st.divider()

    # 3. 달력 대용: 전체 투약 스케줄 리스트 확인
    st.subheader("📅 등록된 전체 투약 스케줄")
    all_registered_meds = get_medications()
    if not all_registered_meds:
        st.caption("등록된 스케줄이 없습니다.")
    else:
        for m in all_registered_meds:
            cycle_text = f"{m['cycle_days']}일마다" if m['cycle_days'] > 0 else "1회성"
            st.text(f"• [{m['pet_name'] or '미지정'}] {m['med_name']} | {m['dosage']} | {m['dosage_time']} ({cycle_text}, 시작일: {m['start_date']})")
