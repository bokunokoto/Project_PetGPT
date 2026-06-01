"""사용자 인증 모듈.

지금은 닉네임만 입력받는 '가짜 로그인'이지만, 카카오 OAuth 로 교체할 때
페이지 코드는 거의 안 바뀌도록 인터페이스를 미리 맞춰뒀다.

페이지에서는 그냥 `auth.login_widget()` 한 줄만 호출하면 된다.
"""
import streamlit as st

from db import get_or_create_user


SESSION_USER_ID = "user_id"
SESSION_NICKNAME = "nickname"


def is_logged_in() -> bool:
    return SESSION_USER_ID in st.session_state


def login(nickname: str) -> None:
    """닉네임으로 사용자를 찾거나 만들고, 세션에 기록한다.

    카카오 OAuth 도입 시: 여기 대신 kakao_login() 같은 함수가 같은 자리에서
    `get_or_create_user(kind="kakao", external_id=<카카오 user id>, nickname=...)`
    를 호출하게 된다.
    """
    nickname = nickname.strip()
    if not nickname:
        return
    user_id = get_or_create_user(
        kind="local",
        external_id=nickname,        # 가짜 로그인에선 닉네임을 식별자로 사용
        nickname=nickname,
    )
    st.session_state[SESSION_USER_ID] = user_id
    st.session_state[SESSION_NICKNAME] = nickname


def logout() -> None:
    for key in (SESSION_USER_ID, SESSION_NICKNAME):
        st.session_state.pop(key, None)


def login_widget() -> None:
    """사이드바에 로그인/로그아웃 UI 를 그린다.

    어디서 호출해도 사이드바에 표시되도록 `with st.sidebar:` 를 내부에서 잡는다.
    """
    with st.sidebar:
        st.markdown("### 👤 사용자")
        if is_logged_in():
            st.success(f"**{st.session_state[SESSION_NICKNAME]}** 님으로 로그인됨")
            if st.button("로그아웃", use_container_width=True):
                logout()
                st.rerun()
        else:
            st.caption("로그인하면 입력한 데이터가 본인 계정에 저장돼요.")
            nickname = st.text_input("닉네임", key="login_nickname",
                                     placeholder="예: 멍멍이 보호자")
            if st.button("로그인", type="primary", use_container_width=True):
                if nickname.strip():
                    login(nickname)
                    st.rerun()
                else:
                    st.warning("닉네임을 입력해 주세요.")
            st.caption("⚠️ 현재는 테스트용 임시 로그인입니다. "
                       "비밀번호 없이 닉네임만으로 구분됩니다.")
