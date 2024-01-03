import streamlit as st
import hmac
import pandas as pd
from Home import establish_gsheets_connection, display_progression_graph, translate


def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            username = st.session_state.get("username")
            st.session_state.school_sheet_name = username.split('_')[1]
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

def get_emails_for_school(conn, school_sheet_name):
    """Retrieves a list of student emails from the school's specific sheet."""
    emails_df = conn.read(worksheet=school_sheet_name, usecols=[0], ttl=60)

    # Drop NaN values and convert the DataFrame column to a list
    emails_list = emails_df.dropna().iloc[:, 0].tolist()
    
    return emails_list



def display_data_and_metrics(filtered_data):
    # Example metric: Total number of submissions
    total_submissions = len(filtered_data)
    st.metric(label="Total Submissions", value=total_submissions)

    # Initialize selected frameworks and sections
    display_data = filtered_data
    unique_emails = display_data['user_email'].unique()
    unique_frameworks = display_data['test_framework'].unique()
    unique_sections = display_data['test_section'].unique()

    # selectors for filtering data
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_emails = st.multiselect('Select User Email(s):', unique_emails, default=list(unique_emails))
    with col2:
        selected_frameworks = st.multiselect('Select Test Framework(s):', unique_frameworks, default=list(unique_frameworks))
    with col3:
        selected_sections = st.multiselect('Select Test Section(s):', unique_sections, default=list(unique_sections))

    # Filtering data based on selections
    filtered_data = display_data[
        display_data['user_email'].isin(selected_emails) &
        display_data['test_framework'].isin(selected_frameworks) &
        display_data['test_section'].isin(selected_sections)
    ]
    # Display the data table
    st.dataframe(filtered_data)

    # Progression Graph for each student
    for email in selected_emails:
        st.header(f"Progression Graph for {email}")
        email_filtered_data = filtered_data[filtered_data['user_email'] == email]
        display_progression_graph(email_filtered_data, JP=True, score_column=6)

def main():
    # Admin Dashboard
    st.title("Admin Dashboard")

    # Check if authenticated
    if not check_password():
        st.stop()

    # Use the imported function
    conn, main_data = establish_gsheets_connection()

    # Get the list of student emails for this school
    student_emails = get_emails_for_school(conn, st.session_state.school_sheet_name)

    # Filter your main dataset by these emails
    # Assuming your main dataset is in another sheet and has a column 'Email'
    filtered_data = main_data[main_data['user_email'].isin(student_emails)]

    # Display the filtered data and metrics
    display_data_and_metrics(filtered_data)

if __name__ == "__main__":
    main()