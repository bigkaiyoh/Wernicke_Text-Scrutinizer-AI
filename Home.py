import streamlit as st
from st_paywall import add_auth
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import deepl
from streamlit_option_menu import option_menu
from datetime import datetime
import pytz
# import parts from modules/
from modules.evaluation import handle_evaluation_section
from modules.my_history import handle_history_section


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
    existing_data = conn.read(worksheet="シート1", usecols=list(range(7)), ttl=5)
    existing_data = existing_data.dropna(how="all")

    return conn, existing_data

def add_new_data(email, option, grade, style, user_input, evaluation):
    # Concatenate option and grade if Eiken/英検 is selected
    if option in ["Eiken", "英検"]:
        test_framework = f"{option}{grade}"
    else:
        test_framework = option

    # Add new data to the existing data
    jst = pytz.timezone('Asia/Tokyo')
    timestamp_jst = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    new_data = pd.Series(
        {
            "user_email": email,
            "timestamp": timestamp_jst,
            "test_framework": test_framework,
            "test_section": style,
            "user_input": user_input,
            "Wernicke_output": evaluation
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
    logo_url = "https://nuginy.com/wp-content/uploads/2024/01/d0bdfb798eddb88d67ac8a8a5fd735cb.png"
    short_logo = "https://nuginy.com/wp-content/uploads/2024/01/23f602002a0787321609a4bf3b8ef051.png"
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
        handle_evaluation_section(short_logo, conn, existing_data, JP)

    if selected == translate("マイページ", "My History", JP):
        handle_history_section(existing_data, JP)

if __name__ == "__main__":
    main()