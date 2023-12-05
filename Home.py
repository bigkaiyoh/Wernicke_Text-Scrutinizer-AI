import streamlit as st
from st_paywall import add_auth
from openai import OpenAI
import time

#create a multi-page app
st.set_page_config(
    page_title = "Wernicke",
    page_icon = "🧠",
)

#secret keys
api = st.secrets.api_key
ielts_writing = st.secrets.ielts_writing
ielts_speaking = st.secrets.ielts_speaking

st.title("Wernicke - Text Scrutinizer AI")
st.write("Hey, Wernicke here! Today is a blank canvas waiting for your linguistic masterpiece.  \n" + "Shall we create something amazing together through the art of words?")
st.divider()
st.write("Choose your framework, pick a section (writing or speaking), paste your response, click 'Grade it!',  \n" + "and receive personalized feedback from me!")

def main():
    a_id = "null"
    option = st.selectbox(
        "Choose Test Framework",
        ("IELTS", "TOEFL", "TOEIC", "Eiken"),
        index = None,
        placeholder = "Select the test",
    )
    if option == "Eiken":
        grade = st.select_slider(
            "Select the grade",
            options = ["1", "Pre-2", "2", "Pre-2", "3", "4", "5"]
        )
    else:
         grade = "null"
    style = st.selectbox(
        "Select Section",
        ("Writing", "Speaking"),
        index = None,
        placeholder = "Writing or Speaking?",
    )

    #authentication required
    add_auth(required = True)

    #Stripe_mypage in the sidebar
    st.sidebar.write("Successfully Subscribed!")
    st.sidebar.write(st.session_state.email)
    
    if style == "Speaking":
        audio_file = st.file_uploader("Upload Your Speaking", type=["mp3", "wav"])
        submit_btn = st.button("Grade it!")
        if submit_btn:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            a_id = get_GPT_response(option, grade, style, transcript)
    else:
        with st.form("Your Work"):
            txt = show_text_input()
            submit_button = st.form_submit_button("Grade it!")
        if submit_button:
            a_id = get_GPT_response(option, grade, style, txt)

    #Question Chat Box
    question = st.chat_input("You can ask further questions after submitting your answer.")
    if question:    
        get_GPT_response(option, grade, style, question)


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
    elif option in ["TOEFL", "TOEIC", "英検"]:
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


if __name__ == "__main__":
    main()