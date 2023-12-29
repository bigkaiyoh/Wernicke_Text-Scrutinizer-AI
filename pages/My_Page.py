import streamlit as st
import pandas as pd
from Home import establish_gsheets_connection, add_bottom, translate

st.set_page_config(
    page_title="My Page",
    page_icon="🧠",
)

# Removing Header and Footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def fetch_user_data(conn, user_email):
    sheet_data = conn.read(worksheet="シート1", usecols=list(range(4)), ttl=5)  # Adjusted to correct worksheet name
    user_data = sheet_data[sheet_data['user_email'] == user_email]  # Filter by email
    return user_data

def main():
    # Add logo to the sidebar
    logo_url = "https://nuginy.com/wp-content/uploads/2023/12/b21208974d2bc89426caefc47db0fca5.png"
    st.sidebar.image(logo_url, width=190)  # Adjust width as needed
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

    user_email = st.session_state.email if 'email' in st.session_state else None

    if user_email:
        #sidebar message
        st.sidebar.write("Successfully Subscribed!")
        st.sidebar.write(st.session_state.email)
        #content
        conn, _ = establish_gsheets_connection()
        user_data = fetch_user_data(conn, user_email)
        st.write("Your Past Submissions:")
        st.write(user_data)
    else:
        st.error("You need to be logged in to view this page.")

if __name__ == "__main__":
    main()
