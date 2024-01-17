import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pytz

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

        # Filter data for the last 7 days
        last_7_days = [today - timedelta(days=i) for i in range(7)]
        recent_data = data[data['date'].isin(last_7_days)].copy()
        
        # Create a new column for the unique combination of framework and section
        recent_data['framework_section'] = recent_data['test_framework'] + '-' + recent_data['test_section']
        
        # Group by 'date' and 'framework_section', then count submissions
        grouped = recent_data.groupby(['date', 'framework_section']).size().unstack(fill_value=0)
        
        # Plot the bar chart
        ax = grouped.plot(kind='bar', stacked=True)
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Submissions')
        ax.set_title('Number of Submissions in the Last 7 Days by Framework-Section Combination')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
        
        # Display the plot
        st.pyplot(plt)