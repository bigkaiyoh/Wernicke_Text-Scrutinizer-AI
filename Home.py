import streamlit as st
from st_paywall import add_auth
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import deepl
from streamlit_option_menu import option_menu

#Secret keys
api = st.secrets.api_key
ielts_writing = st.secrets.ielts_writing
ielts_speaking = st.secrets.ielts_speaking
toefl_writing = st.secrets.toefl_writing
toefl_speaking = st.secrets.toefl_speaking
deepl_api = st.secrets.deepl

#Initialize OpenAI client and set default assistant_id
client = OpenAI(api_key=api)
a_id = "null"
#Initialize session_state
if "submit_clicked" not in st.session_state:
    st.session_state.submit_clicked = False
# if "question_clicked" not in st.session_state:
#     st.session_state.question_clicked = False
if "translation_completed" not in st.session_state:
    st.session_state['translation_completed'] = False
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

#Page Configuration
st.set_page_config(
    page_title = "Wernicke",
    page_icon = "🧠",
    layout = "wide"
)

#Removing Hooter and Footer
hide_st_style = """
            <style>
            #MainMenu {visibility: visible;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def add_logo(logo_url, width=190):
    logo_html = f"<img src='{logo_url}' width='{width}' style='margin-bottom:20px'>"
    st.markdown(logo_html, unsafe_allow_html=True)

def add_bottom(logo_url):
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] + div {{
                position:relative;
                bottom: 0;
                height:50%;
                background-image: url({logo_url});
                background-size: 85% auto;
                background-repeat: no-repeat;
                background-position-x: center;
                background-position-y: bottom;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def set_background_image(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url({url});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def translate(text_japanese, text_english, is_japanese):
    return text_japanese if is_japanese else text_english

def display_intro(JP):
    st.image("https://nuginy.com/wp-content/uploads/2023/12/b21208974d2bc89426caefc47db0fca5-e1702608203525.png",
             use_column_width="auto")

def set_test_configuration(JP, key_suffix=""):
    option = st.selectbox(
        translate("テストを選択してください", "Choose Test Framework", JP),
        translate(("IELTS", "TOEFL", "TOEIC", "英検"), ("IELTS", "TOEFL", "TOEIC", "Eiken"), JP),
        index=None,
        placeholder="Select the test",
        key=f"test_framework_selectbox_{key_suffix}"  # Dynamic key
    )

    if option in ["Eiken", "英検"]:
        grade = st.select_slider(
            "Select the grade",
            options=translate(["1級", "準１級", "2級", "準２級", "3級", "4級", "5級"],
                              ["1", "Pre-1", "2", "Pre-2", "3", "4", "5"], JP),
            key=f"grade_select_slider_{key_suffix}"  # Dynamic key
        )
    else:
        grade = "null"

    style = st.selectbox(
        translate("セクションを選択してください", "Choose Test Framework", JP),
        ("Writing", "Speaking"),
        index=None,
        placeholder="Writing or Speaking?",
        key=f"style_selectbox_{key_suffix}"  # Dynamic key
    )
    return option, grade, style

def get_user_input(style, JP):
    if style == "Speaking":
        answer = st.file_uploader(translate("スピーキングをアップロード","Upload Your Speaking", JP), type=["mp3", "wav"])
    else:
        answer = st.text_area(translate("回答を提出", "Paste Your Answer for Evaluation", JP))
    return answer

def show_text_input() -> None:
    txt = st.text_area(
        "Paste Your Answer for Evaluation",
    )
    st.write(f'{len(txt)} characters.')
    return txt

def get_GPT_response(option, grade, style, txt, return_content=False):
    # Initialize assistant_id as null
    assistant_id = "null"
    #call the right assistant
    if option == "IELTS":
        assistant_id = ielts_writing if style == "Writing" else ielts_speaking

    elif option == "TOEFL":
        assistant_id = toefl_writing if style == "Writing" else toefl_speaking

    elif option in ["TOEIC", "Eiken", "英検"]:
        st.markdown("Under Preparation")
    else:
        st.markdown("Please Provide Your Answer First")

    if assistant_id != "null":
        evaluation = run_assistant(assistant_id, txt, return_content=True)

    if return_content:
        return assistant_id, evaluation
    else:
        return assistant_id, None

def run_assistant(assistant_id, txt, return_content=False):
    if 'client' not in st.session_state:
        st.session_state.client = OpenAI(api_key=api)

        #retrieve the assistant
        st.session_state.assistant = st.session_state.client.beta.assistants.retrieve(assistant_id)
        #Create a thread 
        st.session_state.thread = st.session_state.client.beta.threads.create()
    if txt:
        #Add a Message to a Thread
        message = st.session_state.client.beta.threads.messages.create(
            thread_id = st.session_state.thread.id,
            role = "user",
            content = txt
        )

        #Run the Assistant
        run = st.session_state.client.beta.threads.runs.create(
                thread_id=st.session_state.thread.id,
                assistant_id=st.session_state.assistant.id
        )

        # Spinner for ongoing process
        with st.spinner('Neurons weaving through the layers ...'):
            while True:
                # Retrieve the run status
                run_status = st.session_state.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id
                )

                # If run is completed, process messages
                if run_status.status == 'completed':
                    messages = st.session_state.client.beta.threads.messages.list(
                        thread_id=st.session_state.thread.id
                    )

                    # Loop through messages and print content based on role
                    for msg in reversed(messages.data):
                        role = msg.role
                        content = msg.content[0].text.value
                        
                        # Use st.chat_message to display the message based on the role
                        with st.chat_message(role):
                            st.write(content)
                    break
                # Wait for a short time before checking the status again
                time.sleep(1)
    if return_content:
        return content

def establish_gsheets_connection():
    # Establishing a Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Fetch existing Wernicke data
    existing_data = conn.read(worksheet="シート1", usecols=list(range(6)), ttl=5)
    existing_data = existing_data.dropna(how="all")

    return conn, existing_data

def add_new_data(email, option, grade, style, user_input, evaluation):
    # Concatenate option and grade if Eiken/英検 is selected
    if option in ["Eiken", "英検"]:
        test_framework = f"{option}{grade}"
    else:
        test_framework = option

    # Add new data to the existing data
    new_data = pd.Series(
        {
            "user_email": email,
            "test_framework": test_framework,
            "test_section": style,
            "user_input": user_input,
            "Wernicke_output": evaluation,
        }
    )
    return new_data

def update_google_sheets(conn, existing_data, new_data):
    # Update a Google Sheets
    updated_df = pd.concat([existing_data, new_data.to_frame().T], ignore_index=True)
    conn.update(worksheet="シート1", data=updated_df)

def no_input_error(is_japanese):
    st.error(translate("先に回答をしてください", 
                       "Please provide your answer before grading.", is_japanese))

def show_mock(JP):
    mock = st.empty()
    c = mock.container()
    c.title(translate("Wernicke - 採点者AI", "Wernicke - Text Scrutinizer AI", JP))
    c.write(translate(
        "Hey, Wernicke here！今日は君の言葉が芸術になる日。  \n"
        "ログインすると実際のファイルをアップロードできます",
        "Hey, Wernicke here! Today is a blank canvas waiting for your linguistic masterpiece.  \n"
        "Log in to get your answer scored!", JP))
    c.divider()
    c.write(translate(
        "フレームワーク、セクション（Writing/Speaking）を選択後、回答を貼り付け '採点'をクリック！\n"
        "すぐに私からの個別のフィードバックが返ってきます。",
        "Choose your framework, pick a section (writing or speaking), paste your response, click 'Grade it!',  \n"
        "and receive personalized feedback from me!", JP))
    with c:
        mock_option, mock_grade, mock_style = set_test_configuration(JP, "mock")
    c.header(translate("参考フィードバック", "Sample Feedback", JP))
    c.image("https://nuginy.com/wp-content/uploads/2023/12/Screenshot-2023-12-14-at-12.58.20.jpg")
    return mock

def show_prelog(logo, JP):
    prelog = st.empty()
    c = prelog.container()
    with c:
        set_background_image("https://nuginy.com/wp-content/uploads/2023/12/Blurred-Papua-Background.jpg",)
        st.image(logo, width=400)
        st.link_button(translate("今すぐログイン！", "Log In Now!", JP), 
                                 "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=1001045070310-kp5s24oe6o0r699fcb37joigo4qeamfp.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Ftextgrader-wernicke.streamlit.app%2F&scope=email&access_type=offline",
                                 help = "Gmail Ready?")

    return prelog

def deepl_translation(text, target_language):
    translator = deepl.Translator(deepl_api)
    result = translator.translate_text(text, target_lang=target_language)
    return result.text

def main():
    # Add logo to the sidebar
    logo_url = "https://nuginy.com/wp-content/uploads/2023/12/b21208974d2bc89426caefc47db0fca5.png"
    st.sidebar.image(logo_url, width=190)  # Adjust width as needed
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")
    #set_background_image("https://nuginy.com/wp-content/uploads/2023/12/Blurred-Papua-Background.jpg")

    #language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)
    # Initialize placeholder variable
    placeholder = None

    if st.session_state.is_authenticated == False:
        #Page before Login
        placeholder = show_prelog(logo_url, JP)
        
    #authentication required
    add_auth(required = True)
    if 'placeholder' in locals() and placeholder is not None:
        placeholder.empty()
    st.session_state.is_authenticated = True
    st.sidebar.write("Successfully Subscribed!")
    st.sidebar.write(st.session_state.email)

    # Establish Google Sheets connection
    conn, existing_data = establish_gsheets_connection()

    # --- NAVIGATION MENU ---
    selected = option_menu(
    menu_title=None,
    options=[translate("採点添削", "Evaluation", JP), translate("マイページ", "My History", JP)],
    icons=["vector-pen", "person-fill"],  # https://icons.getbootstrap.com/
    orientation="horizontal",
    )

    if selected == translate("採点添削", "Evaluation", JP):
        # Main Area
        col1, col2 = st.columns([1, 2])

    # Check if the user is authenticated
        
        with col1:
            #Display title and introductory text based on the language toggle
            display_intro(JP)
            #Set Test Configuration
            option, grade, style = set_test_configuration(JP)
            
            #Get user input
            q = st.text_input(translate("問題（必須ではない）", "Question (not mandatory)", JP), 
                                help = translate("IELTS-Task2 の精度アップ", "suggested for IELTS-Task2", JP)
                                )
            user_input = get_user_input(style, JP)

            submit_button = st.button(translate("採点", "Grade it!", JP),
                                    key = "gradeit")

        with col2:
            st.header(translate("　　フィードバック", "  Feedback", JP))
            temporary = st.empty()
            t = temporary.container()
            with t:
                message = st.chat_message("assistant")
                message.write(translate(
                                "今日は君の言葉が芸術になる日£:。)",
                                "Today is a blank canvas waiting for your linguistic masterpiece.", 
                                JP))

            if submit_button:
                temporary.empty()
                if not style:  # Check if style is not selected
                    st.error("Please select a test style (Writing or Speaking) before grading.")
                else:
                    st.session_state.submit_clicked = True
                    st.session_state.translation_completed = False

                    if user_input:
                        if style == "Speaking":
                            # Transcribe audio
                            user_input = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=user_input,
                                response_format="text"
                            )
                        #reset the thread
                        if 'client' in st.session_state:
                            del st.session_state.client
                        if q:
                            user_input = "Question: " + q + "\n\n" + "Answer: " + user_input
                        a_id, evaluation = get_GPT_response(option, grade, style, user_input, return_content=True)
                        
                        # Store the evaluation in session state after generating it
                        st.session_state.evaluation = evaluation

                        # Add new data and update Google Sheets
                        new_data = add_new_data(st.session_state.email, option, grade, style, user_input, evaluation)
                        update_google_sheets(conn, existing_data, new_data)
                    else:
                        no_input_error(JP)

            # Handling the translation
            translation_button_placeholder = st.empty()
            tr = translation_button_placeholder.container()
            if st.session_state.submit_clicked and not st.session_state.translation_completed:
                if 'evaluation' in st.session_state:
                    if tr.button(translate("日本語に翻訳", "Translate Feedback to Japanese", JP), key="deepl"):
                        # Translate the evaluation
                        translated_text = deepl_translation(st.session_state.evaluation, "JA")
                        st.session_state.translated_evaluation = translated_text
                        st.session_state.translation_completed = True
                        translation_button_placeholder.empty()
                if st.session_state.translation_completed:
                    temporary.empty()
                    user_message = st.chat_message("user")
                    user_message.write(user_input)
                    translated_message = st.chat_message("assistant")
                    translated_message.write(st.session_state.translated_evaluation)


        #Question Chat Box
        # question = st.chat_input(translate(
        #     "フィードバックについて質問ができます。",
        #     "You can ask further questions regarding the feedback", JP),
        #     key = "question"
        #     )
        # if question: 
        #     st.session_state.question_clicked = True   
        #     get_GPT_response(option, grade, style, question)
        # elif question and not user_input:
        #     no_input_error(JP)

    if selected == translate("マイページ", "My History", JP):
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
            # Combine 'test_framework' and 'test_section' into a single column for plotting
            filtered_data['framework_section'] = filtered_data['test_framework'] + "-" + filtered_data['test_section']

            # Assuming the scores are in the 6th column of the original 'filtered_data'
            score_column = filtered_data.columns[4]  # Adjust this index if necessary

            # Pivot the data for plotting
            pivot_data = filtered_data.pivot_table(index=filtered_data.index, columns='framework_section', values=score_column, aggfunc='first')
            pivot_data = pivot_data.reset_index(drop=True)
            # Plot the line chart
            st.line_chart(pivot_data)
        else:
            st.error("Score data not available for plotting.")
        


if __name__ == "__main__":
    main()