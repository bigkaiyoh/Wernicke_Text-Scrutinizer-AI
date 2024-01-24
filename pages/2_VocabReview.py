import streamlit as st
import requests
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


def print_words(words, JP):
    st.header(translate("あなたがこの１週間で学習した単語は", "Words you have learned this week are", JP))

    with st.expander("See Your Achievement!"):
        num_columns = 3
        columns = st.columns(num_columns)
        for index, word in enumerate(words):
            with columns[index % num_columns]:
                st.write(word)

def fetch_user_words(user_id, JP):
    request_url = f'https://wernicke-flask-39b91a2e8071.herokuapp.com/get_words?user_id={user_id}'
    try:
        response = requests.get(request_url)
        response.raise_for_status()
        words = response.json().get('words', [])
        return words
    except requests.RequestException as e:
        st.error(f'Failed to retrieve words: {e}')
        st.write("Response content for debugging:", e.response.text if e.response else "No response")
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
    base_url = 'https://wernicke-flask-39b91a2e8071.herokuapp.com'
    request_url = f'{base_url}/{endpoint}'
    response = requests.post(request_url, json=json_data)
    if response.status_code == 200:
        return True
    else:
        return False

def add_word_form():
    with st.form(key='add_word_form', clear_on_submit=True, border=False):
        added_word = st.text_input("Enter a word to add 👇", key="add_word_input")
        submit_add = st.form_submit_button("Add Word")
        if submit_add:
            if make_request("add", {'user_id': st.query_params['user'], 'word': added_word}):
                st.session_state['added_success'] = True
                st.rerun()
            else:
                st.error("Failed to add a word. Please try again")
    # Handle success message
    if st.session_state.get('added_success', False):
        st.success("Word added successfully!")
        st.session_state['added_success'] = False
    
def delete_word_form():
    with st.form(key='delete_word_form', clear_on_submit=True, border=False):
        deleted_word = st.text_input("Enter a word to delete 👇", key="delete_word_input")
        submit_delete = st.form_submit_button("Delete Word")
        if submit_delete:
            if make_request("delete", {'user_id': st.query_params['user'], 'word': deleted_word}):
                st.session_state['deleted_success'] = True
                st.rerun()
            else:
                st.error("Failed to delete a word. Please check spelling")
    # Handle success message
    if st.session_state.get('deleted_success', False):
        st.success("Word deleted successfully!")
        st.session_state['deleted_success'] = False


def main():
    # Add logo to the sidebar
    st.title("Vocab Review!")
    logo_url = "https://nuginy.com/wp-content/uploads/2024/01/d0bdfb798eddb88d67ac8a8a5fd735cb.png"
    short_logo = "https://nuginy.com/wp-content/uploads/2024/01/23f602002a0787321609a4bf3b8ef051.png"
    st.sidebar.image(logo_url, width=190)  # Adjust width as needed
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

    # Language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)

    if st.session_state.is_authenticated:
        st.sidebar.write("Successfully Subscribed!")
        st.sidebar.write(st.session_state.email)
        st.query_params.user = st.session_state.email

    #setup the page
    if "user" in st.query_params:
        words = fetch_user_words(st.query_params['user'], JP)

        if words:
            print_words(words, JP)
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
                if words:
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
        st.write(translate("LINEかWernickeにログインして自分の苦手単語を復習しましょう！", 
                           "Please log-in either through LINE or Wernicke for personalized quizzes",
                           JP))

    

if __name__ == "__main__":
    main()