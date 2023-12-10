import streamlit as st
from st_paywall import add_auth
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

#Secret keys
api = st.secrets.api_key
ielts_writing = st.secrets.ielts_writing
ielts_speaking = st.secrets.ielts_speaking

#Initialize OpenAI client and set default assistant_id
client = OpenAI(api_key=api)
a_id = "null"

#Page Configuration
st.set_page_config(
    page_title = "Wernicke",
    page_icon = "🧠",
)

def translate(text_japanese, text_english, is_japanese):
    return text_japanese if is_japanese else text_english

def display_intro(JP):
    st.title(translate("Wernicke - テスト採点者AI", "Wernicke - Text Scrutinizer AI", JP))
    st.write(translate(
        "Hey, Wernicke here！今日は君の言葉が芸術になる日。  \n"
        "一緒に表現力豊かな言葉の使い方を学びましょう！",
        "Hey, Wernicke here! Today is a blank canvas waiting for your linguistic masterpiece.  \n"
        "Shall we create something amazing together through the art of words?", JP))
    st.divider()
    st.write(translate(
        "フレームワーク、セクション（Writing/Speaking）を選択後、回答を貼り付け '採点'をクリック！\n"
        "すぐに私からの個別のフィードバックが返ってきます。",
        "Choose your framework, pick a section (writing or speaking), paste your response, click 'Grade it!',  \n"
        "and receive personalized feedback from me!", JP))

def set_test_configuration(JP):
    option = st.selectbox(
        translate("テストを選択してください", "Choose Test Framework", JP),
        translate(("IELTS", "TOEFL", "TOEIC", "英検"), ("IELTS", "TOEFL", "TOEIC", "Eiken"), JP),
        index = None,
        placeholder = "Select the test",
    )
    if option in ["Eiken", "英検"]:
        grade = st.select_slider(
            "Select the grade",
            options = translate(["1級", "準１級", "2級", "準２級", "3級", "4級", "5級"],
                                ["1", "Pre-1", "2", "Pre-2", "3", "4", "5"], JP)
        )
    else:
         grade = "null"
    style = st.selectbox(
        translate("セクションを選択してください", "Choose Test Framework", JP),
        ("Writing", "Speaking"),
        index = None,
        placeholder = "Writing or Speaking?",
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

def get_GPT_response(option, grade, style, txt):
    #call the right assistant
    if option == "IELTS":
        assistant_id = ielts_writing
        if style == "Speaking":
            assistant_id = ielts_speaking
        run_assistant(assistant_id, txt)
    elif option in ["TOEFL", "TOEIC", "Eiken", "英検"]:
        assistant_id = "null"
        st.markdown("Under Preparation")
    else:
        assistant_id = "null"
        st.markdown("Please Provide Your Answer First")
    return assistant_id

def run_assistant(assistant_id, txt):
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

        while True:
            # Wait for 5 seconds
            time.sleep(5)

            # Retrieve the run status
            run_status = st.session_state.client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread.id,
                run_id=run.id
            )

            # If run is completed, get messages
            if run_status.status == 'completed':
                messages = st.session_state.client.beta.threads.messages.list(
                    thread_id=st.session_state.thread.id
                )

                #Loop through messages and print content based on role
                for msg in reversed(messages.data):
                    role = msg.role
                    content = msg.content[0].text.value
                    st.write(f"{role.capitalize()}: {content}")
                break
            else:
                st.write("Neurons weaving through the layers ...")
                time.sleep(5)

def establish_gsheets_connection():
    # Establishing a Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Fetch existing Wernicke data
    existing_data = conn.read(worksheet="シート1", usecols=list(range(4)), ttl=5)
    existing_data = existing_data.dropna(how="all")

    return conn, existing_data

def add_new_data(email, option, style, user_input):
    # Add new data to the existing data
    new_data = pd.Series(
        {
            "user_email": email,
            "test_framework": option,
            "test_section": style,
            "user_input": user_input,
        }
    )
    return new_data

def update_google_sheets(conn, existing_data, new_data):
    # Update a Google Sheets
    updated_df = pd.concat([existing_data, new_data.to_frame().T], ignore_index=True)
    conn.update(worksheet="シート1", data=updated_df)

def no_input_error():
    st.error(translate("先に回答をしてください", 
                        　　"Please provide your answer before grading.", JP))

def main():
    #language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)

    #Display title and introductory text based on the language toggle
    display_intro(JP)

    #Set Test Configuration
    option, grade, style = set_test_configuration(JP)

    #authentication required
    add_auth(required = True)
    st.sidebar.write("Successfully Subscribed!")
    st.sidebar.write(st.session_state.email)
    # Establish Google Sheets connection
    conn, existing_data = establish_gsheets_connection()
    
    #Get user input
    user_input = get_user_input(style, JP)

    submit_button = st.button(translate("採点", "Grade it!", JP))
    if submit_button:
        if style == "Speaking":
            # Transcribe audio
            user_input = client.audio.transcriptions.create(
                model="whisper-1",
                file=user_input,
                response_format="text"
            )
        a_id = get_GPT_response(option, grade, style, user_input)

        # Add new data
        new_data = add_new_data(st.session_state.email, option, style, user_input)

        # Update Google Sheets
        update_google_sheets(conn, existing_data, new_data)

    # If the submit button is clicked but no input is provided, show an error message
    elif submit_button and not user_input:
        no_input_error()

    #Question Chat Box
    question = st.chat_input(translate(
        "フィードバックについて質問ができます。",
        "You can ask further questions regarding the feedback", JP))
    if question:    
        get_GPT_response(option, grade, style, question)
     elif question and not user_input:
        no_input_error()

if __name__ == "__main__":
    main()