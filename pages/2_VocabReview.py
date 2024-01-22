import streamlit as st
import requests
from Home import add_bottom, translate, run_assistant

#Secret Keys
vocab_assistant = st.secrets.vocabulary_assistant

def print_words(words, JP):
    st.header(translate("あなたがこの１週間で学習した単語は", "Words you have learned this week are", JP))

    with st.expander("See Your Achievement!"):
        num_columns = 3  # You can adjust this number based on your preference
        columns = st.columns(num_columns)
        for index, word in enumerate(words):
            with columns[index % num_columns]:
                st.write(word)

def setup(JP):
    if "user" in st.query_params:
        user_id = st.query_params.user
        # Replace with the URL of your Flask backend
        request_url = f'https://wernicke-flask-39b91a2e8071.herokuapp.com/get_words?user_id={user_id}'
        response = requests.get(request_url)

        
        if response.status_code == 200:
            words = response.json().get('words', [])
            if words:
                print_words(words, JP)
                return words
            else:
                st.write("No words found for you")
        else:
            st.error(f'Failed to retrieve words. Status code: {response.status_code}')
            st.write("Response content for debugging:", response.text)  # Debug: print error response    
    else:
        st.write("Please log-in through LINE")

def activate_chatbot():
    st.session_state.chatbot_active = True

def main():
    # Add logo to the sidebar
    st.title("Vocab Review!")
    logo_url = "https://nuginy.com/wp-content/uploads/2024/01/d0bdfb798eddb88d67ac8a8a5fd735cb.png"
    short_logo = "https://nuginy.com/wp-content/uploads/2024/01/23f602002a0787321609a4bf3b8ef051.png"
    st.sidebar.image(logo_url, width=190)  # Adjust width as needed
    add_bottom("https://nuginy.com/wp-content/uploads/2023/12/BottomLogo-e1702481750193.png")

    # Language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)

    # Initialize chat history in session state if not present
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chatbot_active' not in st.session_state:
        st.session_state.chatbot_active = False

    #setup the page
    words = setup(JP)

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
                
            # Display the chat history
            for role, message in st.session_state.chat_history:
                with st.chat_message(role):
                    st.write(message)
            

    if st.session_state.chatbot_active:
        # Chat input for user to continue the conversation
        user_input = st.chat_input(translate(
            "単語の意味について質問したりクイズを出してもらいましょう！",
            "Ask about the meanings of words or get quizzed!", JP),
            key="user_input")

        if user_input:
            # Send user input to the chatbot and get the response
            response = run_assistant(vocab_assistant, user_input, return_content=True, display_chat=False)

            # Update the chat history with the new user input and response
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("assistant", response))

            # Re-display updated chat history
            for role, message in st.session_state.chat_history:
                with st.chat_message(role):
                    st.write(message)




if __name__ == "__main__":
    main()