import streamlit as st
from Home import translate



def handle_history_section(existing_data, JP):
    user_data = existing_data[existing_data['user_email'] == st.session_state.email]  # Filter by email
    # Do not display user_email
    display_data = user_data.drop(columns=['user_email'])

    # st.write(translate("これまでのデータ:", "Your Past Submissions:", JP))
    num_submissions = len(user_data)
    st.metric(label="You have practiced", value=f"{num_submissions}", delta="tests")

    # Initialize selected frameworks and sections
    unique_frameworks = display_data['test_framework'].unique()
    unique_sections = display_data['test_section'].unique()

    # Layout for multiselect filters
    col1, col2 = st.columns(2)

    with col1:
        # Multiselect for test_framework (Column B)
        selected_frameworks = st.multiselect('Select Test Framework(s):', unique_frameworks, default=list(unique_frameworks))

    with col2:
        # Multiselect for test_section (Column C)
        selected_sections = st.multiselect('Select Test Section(s):', unique_sections, default=list(unique_sections))

    # Filtering data based on selections
    filtered_data = display_data[display_data['test_framework'].isin(selected_frameworks) & display_data['test_section'].isin(selected_sections)]

    # Display filtered data (Columns D and E)
    st.dataframe(filtered_data[['user_input', 'Wernicke_output']])

    # Progression graph
    st.header(translate("スコア推移", "Progression Graph", JP))
    if not filtered_data.empty:
        cl1, cl2 = st.columns([4, 1])
        with cl1:
            # Create a new DataFrame specifically for plotting
            plot_data = filtered_data.copy()

            # Combine 'test_framework' and 'test_section' into a single column for plotting
            plot_data['framework_section'] = plot_data['test_framework'] + "-" + plot_data['test_section']

            score_column = plot_data.columns[5]  # Adjust this index if necessary

            # Create a dictionary to store the mapping of unique combinations to their starting x-values
            combination_to_x = {}

            # Initialize x_values as an empty list
            x_values = []

            # Iterate through the rows and calculate x-values
            for index, row in plot_data.iterrows():
                combination = row['framework_section']
                if combination not in combination_to_x:
                    # If it's the first occurrence of this combination, set x to 1
                    combination_to_x[combination] = 1
                else:
                    # Otherwise, increment x for this combination
                    combination_to_x[combination] += 1
                x_values.append(combination_to_x[combination])

            # Add the x_values as a new column in the plot_data DataFrame
            plot_data['x_values'] = x_values

            # Pivot the data for plotting
            pivot_data = plot_data.pivot_table(index='x_values', columns='framework_section', values=score_column, aggfunc='first')

            # Plot the line chart with specified x-axis values and default colors
            st.line_chart(pivot_data)
        with cl2:
            # Group the data by 'framework_section' and calculate the average score for each group
            grouped_data = plot_data.groupby('framework_section')
            for group_name, group_data in grouped_data:
                # Calculate average score for this group
                average_score = group_data[score_column].mean()
                st.metric(label = "Average Score", value = f"{average_score:.2f}", delta = f"{group_name}")
    else:
        st.error("No data available for plotting.")
