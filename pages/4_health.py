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

tab_schedule, tab_record, tab_medication = st.tabs(["📅 케어 일정", "🏥 진료 기록"])


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
# 탭 1. 케어 일정 (수정된 코드)
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
        # 수정됨: 최근 시행일 -> 일정 예정일
        due_date = st.date_input("일정 예정일", value=date.today())
        
        # 수정됨: 반복 주기 분리 (radio 버튼 사용)
        repeat_option = st.radio("반복 여부", ["없음", "있음"], horizontal=True)
        cycle_days = 0
        if repeat_option == "있음":
            cycle_days = st.number_input("반복 주기 (일)", min_value=1, max_value=365, value=30, step=1)

    if st.button("일정 등록", type="primary", key="add_schedule"):
        # '없음'이면 0, '있음'이면 입력받은 cycle_days 사용
        final_cycle = cycle_days if repeat_option == "있음" else 0
        
        # '최근 시행일' 개념이 없어졌으므로, 등록일 자체가 예정일(next_due)이 됨
        add_schedule(sch_pet_id, care_type, due_date, final_cycle, due_date)
        st.success(f"'{care_type}' 일정이 등록되었어요.")
        st.rerun()# ════════════════════════════════════════════════════════════════════
    # 기존 일정 목록 코드 바로 밑에 아래 내용을 추가하세요
    # ════════════════════════════════════════════════════════════════════

    st.divider() # 위쪽 일정 목록과 구분선
    st.subheader("💊 약 복용 기록")
    st.caption("매일 복용하는 약을 체크하여 건강을 관리하세요.")
    
    with st.container(border=True):
        med_pet_id, _ = pet_picker("대상 반려동물", "med_pet")
        med_name = st.text_input("약 이름", placeholder="예: 심장사상충 예방약")
        
        # '오늘 복용 완료' 버튼
        if st.button("오늘 복용 완료", type="primary", key="med_done"):
            # 여기서 db.add_medication_log(med_pet_id, med_name, date.today())를 호출
            # 아직 함수를 안 만드셨다면 db.py에 추가해야 합니다.
            st.success(f"{med_name} 복용 기록이 저장되었습니다!")
            st.rerun()

    # 최근 복용 기록 간단 요약 (선택 사항)
    st.write("**최근 복용 내역**")
    st.info("여기에 최근 5건의 복용 기록을 보여주는 로직을 넣으면 더 좋습니다.")

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
  


# 새로운 탭 추가
tab_schedule, tab_record, tab_stats = st.tabs(["📅 케어 일정", "🏥 진료 기록", "📊 건강 요약"])

with tab_stats:
    st.subheader("📊 건강 준수율 및 요약")
    
    # 1. 누적 진료비 확인 (기존 코드 로직 활용)
    records = get_records()
    total_cost = sum(r["cost"] or 0 for r in records)
    st.metric("총 누적 진료비", f"{total_cost:,}원")
    
    st.divider()
    
    # 2. 약 복용 준수율 (History 테이블이 있다고 가정)
    st.subheader("💊 약 복용 준수 기록")
    st.info("여기에 '약 먹었어요!' 버튼과 데이터 시각화를 추가하면 됩니다.")
    
    if st.button("오늘 약 먹었어요!"):
        # 여기에 db.add_medication_log() 등 새 함수를 만들어 호출
        st.success("오늘의 복용 기록이 저장되었습니다.")

    # 3. 데이터 CSV 내보내기 (기존 진료 기록 전체)
    if records:
        df = pd.DataFrame(records)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("전체 건강 데이터 CSV 다운로드", csv, "pet_health_all.csv", "text/csv")
