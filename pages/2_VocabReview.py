import streamlit as st
import requests
import pandas as pd
import time
from Home import add_bottom, translate, run_assistant

st.set_page_config(
    page_title = "Vocabulary Review",
    page_icon = "📚",
)

#Secret Keys
vocab_assistant = st.secrets.vocabulary_assistant

# Initialize chat history in session state if not present
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chatbot_active' not in st.session_state:
    st.session_state.chatbot_active = False
if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False


#Removing Hooter and Footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


def get_or_create_user_id(email):
    try:
        response = requests.post('https://wernicke-backend.onrender.com/get_or_create_user', json={'email': email})
        if response.status_code == 200:
            return response.json().get('user_id')
        else:
            st.error(f"Failed to retrieve or create user ID. Status code: {response.status_code}")
    except requests.RequestException as e:
        st.error(f"Error connecting to the backend: {e}")

def print_words(words, JP):
    st.header(translate("あなたがこの１週間で学習した単語は", "Words you have learned this week are", JP))

    with st.expander("See Your Achievement!", expanded=True):
        num_columns = 3
        columns = st.columns(num_columns)
        for index, word in enumerate(words):
            with columns[index % num_columns]:
                st.write(word)

def display_table(table_content, user_id, JP):
    st.header(translate("あなたがこの１週間で学習した単語は", "Words you have learned this week are", JP))
    
    column_order = ['word', 'pronunciation', 'definition', 'synonyms', 'examples']
    df = pd.DataFrame(table_content, columns=column_order)

    # Check for missing content
    missing_content = any(df[col].eq('').any() for col in column_order)
    if missing_content:
        # Button to fill missing content
        if st.button('Fill Missing Content'):
            fill_missing_content_for_user(user_id)
            st.rerun()
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def fill_missing_content_for_user(user_id):
    with st.spinner(text='Filling missing content. This may take some time for more words...'):
        response = requests.post('https://wernicke-backend.onrender.com/fill_missing_content', json={'user_id': user_id})
        if response.status_code == 200:
            data = response.json()
            if data.get('result') == 'success':
                st.success(f'Missing content filled for {data.get("updated")} words.')
            else:
                st.info('No missing content needed to be filled.')
        else:
            st.error('Failed to fill missing content due to an error.')


def fetch_table_content(user_id, JP):
    request_url = f'https://wernicke-backend.onrender.com/get_words?user_id={user_id}'
    try:
        response = requests.get(request_url)
        response.raise_for_status()  # Will raise an exception for HTTP errors
        # Directly return the JSON response since it's already the list of word details
        return response.json()
    except requests.RequestException as e:
        st.error(f'Failed to retrieve word details: {e}')
        return []

def activate_chatbot():
    st.session_state.chatbot_active = True

def display_chat_history():
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

def handle_chat_input(JP):
    user_input = st.chat_input(translate(
        "単語の意味について質問したりクイズを出してもらいましょう！",
        "Ask about the meanings of words or get quizzed!", JP),
        key="user_input")

    if user_input:
        response = run_assistant(vocab_assistant, user_input, return_content=True, display_chat=False)
        st.session_state.chat_history.extend([("user", user_input), ("assistant", response)])
        display_chat_history()

def make_request(endpoint, json_data):
    base_url = 'https://wernicke-backend.onrender.com'
    request_url = f'{base_url}/{endpoint}'
    response = requests.post(request_url, json=json_data)
    if response.status_code == 200:
        return True
    else:
        st.error(f'Status code: {response.status_code}')
        return False

def add_word_form():
    with st.form(key='add_word_form', clear_on_submit=True, border=False):
        added_word = st.text_input("Enter a word to add 👇", key="add_word_input")
        submit_add = st.form_submit_button("Add Word")
        if submit_add and added_word.strip():
            if make_request("add_word", {'user_id': st.query_params['user'], 'word': added_word}):
                st.session_state['added_success'] = True
                st.rerun()
            else:
                st.error("Failed to add a word. Please try again")
        elif submit_add:
            st.warning("Please enter a word to add.", icon="⚠️")

    # Handle success message
    if st.session_state.get('added_success', False):
        st.success("Word added successfully!")
        st.session_state['added_success'] = False

    st.session_state.chatbot_active = False
    
def delete_word_form():
    with st.form(key='delete_word_form', clear_on_submit=True, border=False):
        deleted_word = st.text_input("Enter a word to delete 👇", key="delete_word_input")
        submit_delete = st.form_submit_button("Delete Word")
        if submit_delete and deleted_word.strip():
            if make_request("delete_word", {'user_id': st.query_params['user'], 'word': deleted_word}):
                st.session_state['deleted_success'] = True
                st.rerun()
            else:
                st.error("Failed to delete a word. Please check spelling")
        elif submit_delete:
            st.warning("Please enter a word to delete.", icon="⚠️")
    # Handle success message
    if st.session_state.get('deleted_success', False):
        st.success("Word deleted successfully!")
        st.session_state['deleted_success'] = False

    st.session_state.chatbot_active = False

def check_nickname(user_id):
    response = requests.post('https://wernicke-backend.onrender.com/check_nickname', json={'user_id': user_id})
    if response.status_code == 200:
        return response.json().get('nickname')
    return None

def nickname_form(user_id, JP):
    with st.form("nickname_form"):
        st.header(translate("🤙🏻 ニックネームを登録してください", "🤙🏻 What Should We Call You?", JP))
        nickname = st.text_input(translate("ニックネームを入力してください",
                                                    "Please enter your nickname:", 
                                                    JP), help = translate("管理者に表示される名前です", "will be displayed on your teacher's page", JP))
        submit_button = st.form_submit_button("Submit")
        if submit_button:
            response = requests.post('https://wernicke-backend.onrender.com/update_nickname', json={'user_id': user_id, 'nickname': nickname})
            if response.ok:
                st.balloons()
                st.success("Thank you! Nickname updated successfully!")
                time.sleep(3)
                st.rerun()  # Call rerun only after successful update to avoid infinite loop
            else:
                st.error("Failed to update nickname. Please try again.")

def main():
    # Add logo to the sidebar
    st.title("Vocab Review!")
    logo_url = "https://nuginy.com/wp-content/uploads/2024/01/d0bdfb798eddb88d67ac8a8a5fd735cb.png"
    LINE_logo = "https://nuginy.com/wp-content/uploads/2024/01/126f8f4e35877e29952fe58e4f3d2379.png"
    with st.sidebar:
        st.image(logo_url, width=190)  # Adjust width as needed
        line_url = "https://lin.ee/t3WKARy"
        st.write("簡単LINE連携は[こちら！](%s)" % line_url)
        st.caption("登録メールアドレスを送信するだけ")
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

    # Language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)

    if st.session_state.is_authenticated:
        st.sidebar.write("Successfully Subscribed!")
        st.sidebar.write(st.session_state.email)
        user_id = get_or_create_user_id(st.session_state.email)
        if user_id:
            st.query_params.user = user_id

    #setup the page
    if "user" in st.query_params:
        nickname = check_nickname(st.query_params.user)
        if nickname is not None:
            table_content = fetch_table_content(st.query_params.user, JP)
            if table_content:
                tab1, tab2 = st.tabs(["🏆 Words", "📕 Dictionary"])

                with tab1:
                    words = [word['word'] for word in table_content]
                    print_words(words, JP)
                with tab2:
                    display_table(table_content, st.query_params.user, JP)

                c1, c2 = st.columns(2)
                with c1:
                    add_word_form()
                with c2:
                    delete_word_form()
            else:
                st.subheader(translate("新しく覚えた単語を追加しましょう！", "Add a word you newly learned!", JP))
                add_word_form()

            #initialize chatbot
            st.header(translate("単語復習コーチ", "Review Vocabulary With ME!", JP))

            if st.session_state.chatbot_active == False:
                chatbot = st.button(translate("単語練習を始める", "Start practicing vocabulary", JP))

                if chatbot:
                    st.session_state.chatbot_active = True
                    # Send the initial message to the chatbot and get the response
                    if table_content:
                        initial_prompt = "These are the words I have learned: {}".format(", ".join(words))
                    else:
                        initial_prompt = "I don't have specific words. Help me create the quiz with the right level for me"
                    top_message = run_assistant(vocab_assistant, initial_prompt, return_content=True, display_chat=False)
                    st.session_state.chat_history.append(("assistant", top_message))
                        
                    # Display the initial quiz
                    display_chat_history()
                    
                if st.session_state.chatbot_active:
                    handle_chat_input(JP)
        else:
            nickname_form(st.query_params.user, JP)
    else:
        st.write(translate("LINEかWernickeにログインして自分の苦手単語を復習しましょう！", 
                        "Please log-in either through LINE or Wernicke for personalized quizzes",
                        JP))
        st.link_button(translate("今すぐログイン！", "Log In Now!", JP), 
                                "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=1001045070310-kp5s24oe6o0r699fcb37joigo4qeamfp.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Ftextgrader-wernicke.streamlit.app%2F&scope=email&access_type=offline",
                                help = "Gmail Ready?")

    

if __name__ == "__main__":
    main()