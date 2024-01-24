import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
from datetime import datetime, timedelta

def todays_total_submissions(data):
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).date()
        todays_data = data[data['date'] == today]
        todays_total_submissions = len(todays_data)
        todays_total_users = todays_data['user_email'].nunique()

        st.metric(label="You received", value=todays_total_submissions, delta = "tests today")
        st.metric(label="from", value=todays_total_users, delta = "students")

def plot_recent_submissions(data):
    # Set the timezone to Japan Standard Time
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.now(jst).date()

    # Ensure 'date' is a datetime object
    data['date'] = pd.to_datetime(data['date'])

    # Create a date range for the last 7 days
    last_7_days = pd.date_range(start=today - timedelta(days=6), end=today)

    # Filter data for the last 7 days
    recent_data = data[data['date'].dt.date.isin(last_7_days.date)].copy()

    # Create a new column for the unique combination of framework and section
    recent_data['framework_section'] = recent_data['test_framework'] + '-' + recent_data['test_section']

    # Group by 'date' and 'framework_section', then count submissions
    grouped = recent_data.groupby([recent_data['date'].dt.date, 'framework_section']).size()

    # Convert to DataFrame and unstack
    grouped_df = grouped.unstack(fill_value=0)

    # Reindex to include all dates in the last 7 days
    grouped_df = grouped_df.reindex(last_7_days.date, fill_value=0)

    # Check if there are no submissions in the last 7 days
    if grouped_df.sum().sum() == 0:
        st.error("No Submissions Made This Week")
        return

    # Plot the bar chart
    ax = grouped_df.plot(kind='bar', stacked=True, figsize=(10, 6))

    # Set labels and title
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Submissions')
    ax.set_title('Number of Submissions in the Last 7 Days by Framework-Section Combination')

    # Set x-axis labels
    ax.set_xticklabels([date.strftime('%Y-%m-%d') for date in last_7_days.date], rotation=45, horizontalalignment='right')

    # Display the plot
    st.pyplot(plt)

def filter_by_dates(data, selected_date):
    # Filter based on selected dates
    if len(selected_date) == 2:
        start_date, end_date = selected_date
        data = data[
            (data['date'].dt.date >= start_date) & 
            (data['date'].dt.date <= end_date)
        ]
    elif len(selected_date) == 1:
        data = data[
            data['date'].dt.date == selected_date[0]
        ]
    return data

def filters(filtered_data, apply_email_filter=True):
    # Convert the 'date' column to datetime type
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])

    # Initialize selected frameworks and sections
    unique_frameworks = filtered_data['test_framework'].unique()
    unique_sections = filtered_data['test_section'].unique()

    # Container for selected emails - only used if email filtering is applied
    if apply_email_filter:
        unique_emails = filtered_data['user_email'].unique()
        selected_emails = st.multiselect('Select User Email(s):', unique_emails, default=list(unique_emails))

    col1, col2, col3 = st.columns(3)
    with col1:
        # Allow users to select a single date or a range
        selected_date = st.date_input('Select Date(s):', [])
    with col2:
        selected_frameworks = st.multiselect('Select Test Framework(s):', unique_frameworks, default=list(unique_frameworks))
    with col3:
        selected_sections = st.multiselect('Select Test Section(s):', unique_sections, default=list(unique_sections))

    # Filter based on selected dates
    filtered_data = filter_by_dates(filtered_data, selected_date)

    # Continue to filter based on other selections
    if apply_email_filter:
        filtered_data = filtered_data[filtered_data['user_email'].isin(selected_emails)]

    filtered_data = filtered_data[
        filtered_data['test_framework'].isin(selected_frameworks) &
        filtered_data['test_section'].isin(selected_sections)
    ]

    # Conditionally return selected_emails
    if apply_email_filter:
        return filtered_data, selected_emails
    else:
        return filtered_data
    
# from VocabReview  keep it in both so that VocabReview may be used 
# independently in the future
def add_word_tinyform():
    def add_to_sheet(user_id, word):
        # Replace with the URL of your Flask backend
        request_url = f'https://wernicke-flask-39b91a2e8071.herokuapp.com/add_word'
        response = requests.post(request_url, json={'user_id': user_id, 'word': word})
        if response.status_code == 200:
            return True
        else:
            st.error(f'Failed to add word. Status code: {response.status_code}')
            return False
        
    # -------- Start Here --------
    with st.form(key='add_word_tinyform', clear_on_submit=True, border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            added_word = st.text_input("Enter a word to add 👇", key="add_word_input", placeholder="Add new vocabulary")
        with c2:
            submit_add = st.form_submit_button("Add")
        if submit_add:
            if add_to_sheet(st.query_params['user'], added_word):
                st.session_state['added_success'] = True
                st.rerun()
    # Handle success message
    if st.session_state.get('added_success', False):
        st.success("Word added successfully!")
        st.session_state['added_success'] = False