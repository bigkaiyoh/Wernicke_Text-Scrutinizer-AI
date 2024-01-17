import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import pytz
from datetime import datetime, timedelta

def todays_total_submissions(data):
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).date()
        todays_data = data[data['date'] == today]
        todays_total_submissions = len(todays_data)
        todays_total_users = todays_data['user_email'].nunique()

        st.metric(label="You received", value=todays_total_submissions, delta = "tests today")
        st.metric(label="from", value=todays_total_users, delta = "students")

# def plot_recent_submissions(data):
#         # Set the timezone to Japan Standard Time
#         jst = pytz.timezone('Asia/Tokyo')
#         today = datetime.now(jst).date()

#         # Filter data for the last 7 days
#         last_7_days = [today - timedelta(days=i) for i in range(7)]
#         recent_data = data[data['date'].isin(last_7_days)].copy()
        
#         # Create a new column for the unique combination of framework and section
#         recent_data['framework_section'] = recent_data['test_framework'] + '-' + recent_data['test_section']
        
#         # Group by 'date' and 'framework_section', then count submissions
#         grouped = recent_data.groupby(['date', 'framework_section']).size().unstack(fill_value=0)
        
#         # Plot the bar chart
#         ax = grouped.plot(kind='bar', stacked=True)
        
#         # Set labels and title
#         ax.set_xlabel('Date')
#         ax.set_ylabel('Number of Submissions')
#         ax.set_title('Number of Submissions in the Last 7 Days by Framework-Section Combination')
        
#         # Rotate x-axis labels for better readability
#         plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
        
#         # Display the plot
#         st.pyplot(plt)


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