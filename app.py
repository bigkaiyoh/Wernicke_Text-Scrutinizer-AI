import streamlit as st
from openai import OpenAI
import time

#secret keys

api = st.secrets.api_key
ielts_writing = st.secrets.ielts_writing
ielts_speaking = st.secrets.ielts_speaking

st.title("Mock Testor")

def main():
    a_id = "null"
    option = st.selectbox(
        "受けたいテストを選んでください",
        ("IELTS", "TOEFL", "TOEIC", "英検"),
        index = None,
        placeholder = "一つ選んでください",
    )
    if option == "英検":
        grade = st.select_slider(
            "級を選んでください",
            options = ["1級", "準１級", "2級", "準２級", "3級", "4級", "5級"]
        )
    else:
         grade = "null"
    style = st.selectbox(
        "WritingかSpeakingか選んでください",
        ("Writing", "Speaking"),
        index = None,
        placeholder = "Writing or Speaking?",
    )
    with st.form("Your Work"):
        txt = show_text_input()
        submit_button = st.form_submit_button("採点")
    if submit_button:
        a_id = get_GPT_response(option, grade, style, txt)

    question = st.chat_input("テキスト送信後、結果について詳しく質問できます")
    if question:    
        get_GPT_response(option, grade, style, question)
            

    



def show_text_input() -> None:
    txt = st.text_area(
        "評価してほしい文章を貼り付けてください",
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
        st.markdown("現在準備中です")
    else:
        assistant_id = "null"
        st.markdown("まずテキストを貼り付けてください")
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
                st.write("The result is on its way to you...")
                time.sleep(5)


if __name__ == "__main__":
    main()
    