import streamlit as st
import hmac
import pandas as pd
from Home import establish_gsheets_connection, display_progression_graph, add_bottom, translate
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import numpy as np

# Initialize 'username' in session state if it's not already set
if 'username' not in st.session_state:
    st.session_state['username'] = None


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
            st.session_state.username = st.session_state["username"]
            st.session_state.school_sheet_name = st.session_state.username.split('_')[1]
            del st.session_state["password"]  # Don't store the username or password.
        else:
            st.session_state["password_correct"] = False
            st.session_state.username = None

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
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
    def todays_total_submissions(data):
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).date()
        todays_total_submissions = len(data[data['date'] == today])
        st.metric(label="You received", value=todays_total_submissions, delta = "tests today")
    
    def filters(filtered_data):
        # Initialize selected frameworks and sections
        display_data = filtered_data
        unique_emails = display_data['user_email'].unique()
        unique_frameworks = display_data['test_framework'].unique()
        unique_sections = display_data['test_section'].unique()

        # selectors for filtering data
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # Allow users to select a single date or a range
            selected_date = st.date_input('Select Date(s):', [])
        with col2:
            selected_emails = st.multiselect('Select User Email(s):', unique_emails, default=list(unique_emails))
        with col3:
            selected_frameworks = st.multiselect('Select Test Framework(s):', unique_frameworks, default=list(unique_frameworks))
        with col4:
            selected_sections = st.multiselect('Select Test Section(s):', unique_sections, default=list(unique_sections))

        # If a range of dates is selected, filter between those dates
        if len(selected_date) == 2:
            start_date, end_date = selected_date
            filtered_data = filtered_data[
                (filtered_data['date'] >= start_date) & (filtered_data['date'] <= end_date)
            ]
        elif len(selected_date) == 1:
            filtered_data = filtered_data[filtered_data['date'] == selected_date[0]]
        
        # Continue to filter based on other selections
        filtered_data = filtered_data[
            display_data['user_email'].isin(selected_emails) &
            display_data['test_framework'].isin(selected_frameworks) &
            display_data['test_section'].isin(selected_sections)
        ]
        return filtered_data, selected_emails

    def plot_recent_submissions(data):
        # Set the timezone to Japan Standard Time
        jst = pytz.timezone('Asia/Tokyo')
        
        # Get today's date in JST
        today = datetime.now(jst).date()
        
        # Filter data for the last 7 days
        last_7_days = [today - timedelta(days=i) for i in range(7)]
        recent_data = data[data['date'].isin(last_7_days)]
        
        # Create a new column for the unique combination of framework and section
        recent_data['framework_section'] = recent_data['test_framework'] + '-' + recent_data['test_section']
        
        # Group by 'date' and 'framework_section', then count submissions
        grouped = recent_data.groupby(['date', 'framework_section']).size().unstack(fill_value=0)
        
        # Plot the bar chart
        ax = grouped.plot(kind='bar', stacked=True, figsize=(10, 6))
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Submissions')
        ax.set_title('Number of Submissions in the Last 7 Days by Framework-Section Combination')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
        
        # Display the plot
        st.pyplot(plt)


    # ------ STARTS HERE ------
    filtered_data['date'] = pd.to_datetime(filtered_data['timestamp']).dt.date

    # Today's total submissions
    st.header("Submissions Report")
    cl1, cl2 = st.columns([1, 4])
    with cl1:
        todays_total_submissions(filtered_data)
    with cl2:
        plot_recent_submissions(filtered_data)

    # Filter Data
    st.header("Filter data")
    with st.expander("Filter dataset"):
        filtered_data, selected_emails = filters(filtered_data)
    
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

    # Filter dataset by emails
    filtered_data = main_data[main_data['user_email'].isin(student_emails)]

    # Display the filtered data and metrics
    display_data_and_metrics(filtered_data)


    # -------- SIDEBAR --------
    with st.sidebar:
        if st.button("Logout"):
            logout()
        st.caption("logged in as:")
        st.subheader(st.session_state.username)
        add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

if __name__ == "__main__":
    main()