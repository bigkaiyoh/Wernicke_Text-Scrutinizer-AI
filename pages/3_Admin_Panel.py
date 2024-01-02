import streamlit as st
from streamlit_authenticator import Authenticate

st.set_page_config(
    page_title = "Admin_Panel",
    page_icon = "👤",
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



# Define your user credentials here
credentials = {
    'usernames': {
        'username1': 'password1',
        'username2': 'password2',
        # Add more usernames and passwords as needed
    }
}

authenticator = Authenticate(credentials, 
                             'Wernicke_Org', 
                             'abcdef', 
                             cookie_expiry_days=30)

name, authentication_status, username = authenticator.login('Login', 'main')


if authentication_status:
    st.write(f'Welcome *{name}*')
    # Add your application's main functionality here

elif authentication_status == False:
    st.error('Username/password is incorrect')

elif authentication_status == None:
    st.warning('Please enter your username and password')

st.write("Authentication status:", authentication_status)
st.write("Username entered:", username)

