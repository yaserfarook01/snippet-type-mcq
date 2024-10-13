import streamlit as st
import json
import os
import logging
from prompt import generate_mcqs, problem_solving_types
from db import question_bank
from api_handler import get_all_qbs, import_mcqs_to_examly
from convertor import save_to_file, convert_to_json_format, save_unique_mcqs

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Streamlit UI
st.title("MCQ Generator and Importer")

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
        save_unique_mcqs(unique_questions, unique_mcqs_file)
        
        st.success(f"{len(unique_questions)} new unique questions added to Elasticsearch and saved to {unique_mcqs_file}. {duplicates} duplicates skipped.")
        
        # Display a sample of the generated MCQs
        zst.text(mcqs[:500] + "...")  # Display first 500 characters
        
        # # Display all unique questions
        # st.subheader("Unique Questions:")
        # for q in unique_questions:
        #     st.write(q['question_data'])
        #     st.write("---")
        
        # Display some duplicate questions (if any)
        if duplicates > 0:
            st.subheader("Sample of Duplicate Questions:")
            duplicate_count = min(5, duplicates)  # Display up to 5 duplicates
            for i, q in enumerate(json_questions):
                if i >= duplicate_count:
                    break
                if q not in unique_questions:
                    st.write(q['question_data'])
                    st.write("---")
        
        # Ask if user wants to import to Examly
        if st.button("Import to Examly"):
            # Input field for token
            token = st.text_input("Enter Authorization Token:", type="password")
            
            if token:
                # Fetch all Question Banks
                qbs = get_all_qbs(token)
                
                if qbs and 'data' in qbs:
                    # Create a search box for QB names
                    search_term = st.text_input("Search for a Question Bank:")
                    
                    if st.button("Search"):
                        # Fetch Question Banks based on search term
                        qbs = get_all_qbs(token, search=search_term)
                    
                    if qbs and 'data' in qbs:
                        # Create a dictionary of QB names to QB IDs
                        qb_dict = {qb['name']: qb['id'] for qb in qbs['data']}
                        
                        # Display QB names in a selectbox
                        selected_qb_name = st.selectbox("Select a Question Bank:", list(qb_dict.keys()))
                        
                        if selected_qb_name:
                            selected_qb_id = qb_dict[selected_qb_name]
                            
                            if st.button(f"Import to {selected_qb_name}"):
                                try:
                                    successful_uploads, failed_uploads = import_mcqs_to_examly(unique_mcqs_file, selected_qb_id, created_by, token)
                                    st.success(f"MCQs imported to {selected_qb_name}. Successful: {successful_uploads}, Failed: {failed_uploads}")
                                except Exception as e:
                                    st.error(f"Error importing MCQs: {str(e)}")
                                    st.error(f"Error details: {logging.exception('Error during MCQ import')}")
                    else:
                        st.error("No Question Banks found. Please try a different search term.")
                else:
                    st.error("Failed to fetch Question Banks. Please check your authorization token and try again.")
            else:
                st.warning("Please enter a valid Authorization Token.")
        
    except Exception as e:
        st.error(f"Error generating MCQs: {str(e)}")
        logging.exception("Error in MCQ generation and processing")

