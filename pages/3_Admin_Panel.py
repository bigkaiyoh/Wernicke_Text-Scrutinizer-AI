import streamlit as st

st.set_page_config(
    page_title = "Admin_Panel",
    page_icon = "👤", # https://icons.getbootstrap.com/
)

#Removing Hooter and Footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)