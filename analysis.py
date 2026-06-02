
import streamlit as st

VALID_USERS = {
    "team": "password"
}


def require_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("Login Required")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

    st.stop()
