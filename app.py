import streamlit as st
import json
import os
import logging
import traceback
from prompt import generate_mcqs, problem_solving_types
from db import question_bank
from api_handler import get_all_qbs, import_mcqs_to_examly, get_all_qbs_neowise, import_mcqs_to_neowise
from convertor import save_to_file, convert_to_json_format, save_unique_mcqs

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Streamlit UI
st.title("MCQ Generator and Importer")

# MCQ Generation Section
st.header("Generate MCQs")

topic = st.text_input("Enter Topic:")
num_questions = st.number_input("Number of Questions to Generate", min_value=1, max_value=100, value=10)
difficulty = st.selectbox("Select Difficulty Level", ["Easy", "Medium", "Hard"])
question_type = st.selectbox("Select Question Type", ["Conceptual", "Factual", "Problem-solving"])

# Add filter options for problem-solving questions
selected_filters = []
if question_type == "Problem-solving":
    selected_filters = st.multiselect("Select Problem-solving Question Types", problem_solving_types)

if st.button("Generate MCQs"):
    try:
        mcqs = generate_mcqs(topic, num_questions, difficulty, question_type, selected_filters)
        question_prompt_file = 'question_prompt.txt'
        save_to_file(question_prompt_file, mcqs)
        st.success(f"{num_questions} {question_type} MCQs generated and saved to {question_prompt_file}.")
        
        # Convert generated MCQs to JSON format
        created_by = "19d0e40a-fd35-4741-89ab-11f3c7d4b118"  # This could be made an input if needed
        json_questions = convert_to_json_format(question_prompt_file, None, created_by)
        
        st.info(f"Total questions converted to JSON: {len(json_questions)}")
        
        # Add unique questions to Elasticsearch and get the list of unique questions
        unique_questions, duplicates = question_bank.add_unique_questions(json_questions)
        
        # Save unique questions to a new file
        unique_mcqs_file = 'unique_mcqs.json'
        with open(unique_mcqs_file, 'w', encoding='utf-8') as f:
            json.dump(unique_questions, f, ensure_ascii=False, indent=2)
        
        st.success(f"{len(unique_questions)} new unique questions added to Elasticsearch and saved to {unique_mcqs_file}. {duplicates} duplicates skipped.")
        
    except Exception as e:
        st.error(f"Error generating MCQs: {str(e)}")
        logger.exception("Error in MCQ generation and processing")

# Domain Selection
st.header("Select Domain")
domain = st.radio("Choose a domain:", ["LTI", "Neowise"])

# Question Bank Fetching Section
st.header("Fetch Question Banks")
token = st.text_input("Enter your authorization token:", type="password")
search_query = st.text_input("Search question banks:")

if 'question_banks' not in st.session_state:
    st.session_state.question_banks = None

if st.button("Search Question Banks"):
    if token:
        with st.spinner("Searching question banks..."):
            if domain == "LTI":
                question_banks = get_all_qbs(token, search_query, limit=50)
            else:  # Neowise
                question_banks = get_all_qbs_neowise(token, search_query, limit=50)
        st.session_state.question_banks = question_banks
    else:
        st.warning("Please enter your authorization token.")

if st.session_state.question_banks:
    question_banks = st.session_state.question_banks
    if 'results' in question_banks and 'questionbanks' in question_banks['results']:
        qb_options = [(qb['qb_name'], qb['qb_id']) for qb in question_banks['results']['questionbanks']]
        
        st.success(f"Found {len(qb_options)} matching question banks.")
        
        # Use radio buttons for selection
        st.subheader("Select a Question Bank:")
        selected_qb = st.radio(
            "Choose a question bank:",
            options=qb_options,
            format_func=lambda x: x[0]  # Display only the name in the radio button
        )

        if selected_qb:
            st.session_state.selected_qb_id = selected_qb[1]  # Store the selected qb_id
            st.info(f"Selected Question Bank: {selected_qb[0]}")
    else:
        st.error("Failed to fetch question banks. Please check your token and try again.")

# MCQ Import Section
st.header(f"Import MCQs to {domain}")

if 'selected_qb_id' in st.session_state:
    qb_id = st.session_state.selected_qb_id
    st.write(f"Selected Question Bank ID: {qb_id}")
else:
    qb_id = st.text_input("Enter Question Bank ID (qb_id):")

if st.button(f"Import MCQs to {domain}"):
    if qb_id and token:
        try:
            if domain == "LTI":
                successful_uploads, failed_uploads = import_mcqs_to_examly('unique_mcqs.json', qb_id, "19d0e40a-fd35-4741-89ab-11f3c7d4b118", token)
            else:  # Neowise
                successful_uploads, failed_uploads = import_mcqs_to_neowise('unique_mcqs.json', qb_id, "19d0e40a-fd35-4741-89ab-11f3c7d4b118", token)
            st.success(f"MCQs imported to {domain}. Successful: {successful_uploads}, Failed: {failed_uploads}")
        except Exception as e:
            st.error(f"Error importing MCQs: {str(e)}")
            st.error(f"Error details: {traceback.format_exc()}")
    else:
        st.warning("Please enter valid Question Bank ID and Authorization Token.")
