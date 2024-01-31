import streamlit as st
import hmac
import pandas as pd
from Home import establish_gsheets_connection, display_progression_graph, add_bottom, translate, run_assistant
from datetime import datetime, timedelta
import numpy as np
import json
import re
from modules.modules import todays_total_submissions, plot_recent_submissions, filters

#Secret Keys
error_assistant = st.secrets.error_assistant

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

# Initialize 'username' in session state if it's not already set
if 'username' not in st.session_state:
    st.session_state['username'] = None


def check_password():
    """Returns `True` if the user had a correct password."""
    
    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

            if submitted:
                if username in st.secrets["passwords"] and hmac.compare_digest(
                    password, st.secrets.passwords[username]
                ):
                    st.session_state["password_correct"] = True
                    st.session_state['username'] = username
                    st.session_state.school_sheet_name = username.split('_')[1]
                    st.rerun()
                else:
                    st.session_state["password_correct"] = False
                    st.error("😕 User not known or password incorrect")


    if st.session_state.get("password_correct", False):
        return True
    login_form()
    return False

def logout():
    """Reset the session state variables related to authentication."""
    for key in ['password_correct', 'school_sheet_name']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def get_emails_for_school(conn, school_sheet_name):
    """Retrieves a list of student emails from the school's specific sheet."""
    emails_df = conn.read(worksheet=school_sheet_name, usecols=[0], ttl=60)

    # Drop NaN values and convert the DataFrame column to a list
    emails_list = emails_df.dropna().iloc[:, 0].tolist()
    
    return emails_list

def display_data_and_metrics(filtered_data):
    filtered_data['date'] = pd.to_datetime(filtered_data['timestamp']).dt.date

    # Today's total submissions
    st.header("Submissions Report")
    cl1, cl2 = st.columns([2, 3])
    with cl1:
        todays_total_submissions(filtered_data)
    with cl2:
        plot_recent_submissions(filtered_data)

    # Filter Data
    st.header("Filter data")
    with st.expander("Filter dataset"):
        filtered_data, selected_emails = filters(filtered_data)
    
    # Display the data table
    st.dataframe(filtered_data[['timestamp', 'user_email', 'test_framework', 'test_section', 'user_input', 'Wernicke_output']])

    error_analyzer(filtered_data)

    # Progression Graph for each student
    st.header("Progression Graph")
    for email in selected_emails:
        st.subheader(f"progress of {email}")
        email_filtered_data = filtered_data[filtered_data['user_email'] == email]
        display_progression_graph(email_filtered_data, JP=True, score_column=6)

def summarize_feedback(filtered_data):
    # Regex patterns for each section
    patterns = {
        "Identify and Explain Errors": r"\*\*Identify and Explain Errors:\*\*(.*?)\*\*",
        "Advanced Language Suggestions": r"\*\*Advanced Language Suggestions:\*\*(.*?)\*\*",
        "Feedback on Structure and Coherence": r"\*\*Feedback on Structure and Coherence:\*\*(.*?)(?=\*\*|$)"
    }

    # Initialize aggregated feedback dictionary
    aggregated_feedback = {
        "Identify and Explain Errors": [],
        "Advanced Language Suggestions": [],
        "Feedback on Structure and Coherence": []
    }

    # Process each feedback entry
    for feedback in filtered_data['Wernicke_output']:
        for section, pattern in patterns.items():
            match = re.search(pattern, feedback, re.DOTALL)
            if match and match.group(1).strip():
                aggregated_feedback[section].append(match.group(1).strip())

    # Convert the aggregated feedback to a JSON-like string
    json_like_string = json.dumps(aggregated_feedback, indent=4)
    return json_like_string

def error_analyzer(filtered_data):
    json_data = None

    if st.button('Analyze Common Errors', key='analyze_errors_btn'):
        json_data = summarize_feedback(filtered_data)
        st.write(json_data) #debugging purpose

    if json_data:
        st.session_state.assistant_response = run_assistant(error_assistant, json_data, return_content=True, display_chat=False)
        if 'assistant_response' in st.session_state:
            st.header("Common Errors Analysis")
            with st.expander("See Analysis"):
                st.write(st.session_state.assistant_response)

def main():
    # Admin Dashboard
    st.title("Admin Dashboard")

    # Check if authenticated
    if not check_password():
        st.stop()

    tab1, tab2 = st.tabs(["📜 Tests Submission Report", "📕 New Vocabulary"])

    with tab1:
        # Use the imported function
        conn, main_data = establish_gsheets_connection()

        # Get the list of student emails for this school
        student_emails = get_emails_for_school(conn, st.session_state.school_sheet_name)

        # Filter dataset by emails
        filtered_data = main_data[main_data['user_email'].isin(student_emails)]

        # Display the filtered data and metrics
        display_data_and_metrics(filtered_data)
    with tab2:
        st.subheader("Student's Vocabulary Practice")


    # -------- SIDEBAR --------
    with st.sidebar:
        if st.button("Logout"):
            logout()
        st.caption("logged in as:")
        st.subheader(st.session_state.username)
        add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

if __name__ == "__main__":
    main()