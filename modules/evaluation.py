import streamlit as st
from Home import translate, set_test_configuration, get_user_input, get_GPT_response, add_new_data, update_google_sheets




def handle_evaluation_section(short_logo, conn, existing_data, JP):
    # Main Area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        #Display title and introductory text based on the language toggle
        st.image(short_logo,
            use_column_width="auto")
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