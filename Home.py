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
    layout = "wide"
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

def establish_gsheets_connection():
    # Establishing a Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Fetch existing Wernicke data
    existing_data = conn.read(worksheet="シート1", usecols=list(range(4)), ttl=5)
    existing_data = existing_data.dropna(how="all")

    return conn, existing_data

def add_new_data(email, option, grade, style, user_input):
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


def main():
    # Add custom CSS for scrollable column
    st.markdown("""
        <style>
        .scrollable-col {
            height: 700px;  /* Adjust the height as needed */
            overflow-y: auto;
        }
        </style>
    """, unsafe_allow_html=True)

    # Add logo to the sidebar
    logo_url = "https://nuginy.com/wp-content/uploads/2023/12/b21208974d2bc89426caefc47db0fca5.png"
    st.sidebar.image(logo_url, width=190)  # Adjust width as needed
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

    #Setting Background
    #set_background_image("https://nuginy.com/wp-content/uploads/2023/12/Blurred-Papua-Background.jpg")

    # Main Area
    col1, col2 = st.columns([1, 2])

   # Check if the user is authenticated
    
    with col1:
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

    with col2:
        st.markdown('<div class="scrollable-col">', unsafe_allow_html=True)
        if submit_button:
            if user_input:
                if style == "Speaking":
                    # Transcribe audio
                    user_input = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=user_input,
                        response_format="text"
                    )
                a_id = get_GPT_response(option, grade, style, user_input)

                # Add new data and update Google Sheets
                new_data = add_new_data(st.session_state.email, option, grade, style, user_input)
                update_google_sheets(conn, existing_data, new_data)
            else:
                no_input_error(JP)
        st.markdown('</div>', unsafe_allow_html=True)

    if submit_button and user_input:
        #Question Chat Box
        question = st.chat_input(translate(
            "フィードバックについて質問ができます。",
            "You can ask further questions regarding the feedback", JP))
        if question:    
            get_GPT_response(option, grade, style, question)

if __name__ == "__main__":
    main()