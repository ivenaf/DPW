import streamlit as st

def add_logo():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-image: url("https://upload.wikimedia.org/wikipedia/commons/3/3e/Str%C3%B6er_Logo.svg");
            background-repeat: no-repeat;
            background-position: 15px bottom;
            background-size: 80% auto;
            padding-bottom: 100px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )