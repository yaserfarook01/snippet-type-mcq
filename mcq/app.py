import streamlit as st
import json
import os
import logging
import traceback
import time
from prompt import generate_mcqs, problem_solving_types
from db import question_bank
from api_handler import get_all_qbs, import_mcqs_to_examly, get_all_qbs_neowise, import_mcqs_to_neowise
from convertor import save_to_file, convert_to_json_format, save_unique_mcqs
from qc import process_mcqs 

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
question_type = st.selectbox("Select Question Type", ["Conceptual", "Factual", "Problem-solving", "Scenario-based"])

# Add filter options for problem-solving questions
selected_filters = []
if question_type == "Problem-solving":
    selected_filters = st.multiselect("Select Problem-solving Question Types", problem_solving_types)

if st.button("Generate MCQs"):
    try:
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Generate MCQs (20%)
        status_text.text("🤖 Generating MCQs...")
        progress_bar.progress(20)
        mcqs = generate_mcqs(topic, num_questions, difficulty, question_type, selected_filters)
        question_prompt_file = 'question_prompt.txt'
        save_to_file(question_prompt_file, mcqs)
        
        # Step 2: Quality Check (40%)
        status_text.text("🔍 Performing quality check with Claude...")
        progress_bar.progress(40)
        success, corrected_mcqs, qc_report = process_mcqs(
            question_prompt_file, 
            'qced_mcq.txt',
            'qc_logs.txt'
        )
        
        if success:
            # Step 3: Convert to JSON (60%)
            status_text.text("📝 Converting to JSON format...")
            progress_bar.progress(60)
            created_by = "19d0e40a-fd35-4741-89ab-11f3c7d4b118"
            json_questions = convert_to_json_format('qced_mcq.txt', None, created_by, expected_count=num_questions)
            
            # Step 4: Add to Database (80%)
            status_text.text("💾 Adding to database...")
            progress_bar.progress(80)
            unique_questions, duplicates = question_bank.add_unique_questions(json_questions)
            
            # Step 5: Save Results (100%)
            status_text.text("✅ Finalizing results...")
            progress_bar.progress(100)
            unique_mcqs_file = 'unique_mcqs.json'
            with open(unique_mcqs_file, 'w', encoding='utf-8') as f:
                json.dump(unique_questions, f, ensure_ascii=False, indent=2)
            
            # Clear progress indicators
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            # Display results
            if "No issues found" in qc_report:
                st.success("✅ Generation completed successfully!")
            else:
                st.warning("⚠️ Generation completed with some corrections")
                with st.expander("View QC Report"):
                    st.text(qc_report)
            
            st.info(f"📊 Generated: {len(json_questions)} questions")
            st.success(f"✅ Unique questions: {len(unique_questions)}")
            if duplicates > 0:
                st.warning(f"⚠️ Duplicates skipped: {duplicates}")
            
        else:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ QC process failed. Please check the logs for details.")
            
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Error: {str(e)}")
        logger.exception("Error in MCQ generation")

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
        progress = st.progress(0)
        status = st.empty()
        
        try:
            status.text("🔍 Initializing search...")
            progress.progress(25)
            time.sleep(0.5)
            
            status.text("🔍 Searching question banks...")
            progress.progress(50)
            
            if domain == "LTI":
                question_banks = get_all_qbs(token, search_query, limit=50)
            else:
                question_banks = get_all_qbs_neowise(token, search_query, limit=50)
            
            status.text("✨ Processing results...")
            progress.progress(100)
            time.sleep(0.5)
            
            st.session_state.question_banks = question_banks
            
            status.empty()
            progress.empty()
            
        except Exception as e:
            progress.empty()
            status.empty()
            st.error(f"❌ Search failed: {str(e)}")
    else:
        st.warning("⚠️ Please enter your authorization token.")

if st.session_state.question_banks:
    question_banks = st.session_state.question_banks
    if 'results' in question_banks and 'questionbanks' in question_banks['results']:
        qb_options = [(qb['qb_name'], qb['qb_id']) for qb in question_banks['results']['questionbanks']]
        st.success(f"✅ Found {len(qb_options)} matching question banks")
        
        selected_qb = st.radio(
            "Select Question Bank:",
            options=qb_options,
            format_func=lambda x: x[0]
        )

        if selected_qb:
            st.session_state.selected_qb_id = selected_qb[1]
            st.info(f"📌 Selected: {selected_qb[0]}")
    else:
        st.error("❌ Failed to fetch question banks")

# MCQ Import Section
st.header(f"Import MCQs to {domain}")

if 'selected_qb_id' in st.session_state:
    qb_id = st.session_state.selected_qb_id
else:
    qb_id = st.text_input("Enter Question Bank ID:")

if st.button(f"Import MCQs to {domain}"):
    if qb_id and token:
        progress = st.progress(0)
        status = st.empty()
        
        try:
            status.text("📤 Preparing for import...")
            progress.progress(25)
            time.sleep(0.5)
            
            status.text("📤 Importing questions...")
            progress.progress(50)
            
            if domain == "LTI":
                successful_uploads, failed_uploads = import_mcqs_to_examly(
                    'unique_mcqs.json', qb_id, 
                    "19d0e40a-fd35-4741-89ab-11f3c7d4b118", token
                )
            else:
                successful_uploads, failed_uploads = import_mcqs_to_neowise(
                    'unique_mcqs.json', qb_id,
                    "19d0e40a-fd35-4741-89ab-11f3c7d4b118", token
                )
            
            status.text("✨ Finalizing import...")
            progress.progress(100)
            time.sleep(0.5)
            
            status.empty()
            progress.empty()
            
            st.success(f"✅ Import completed")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Successfully Imported", successful_uploads)
            with col2:
                st.metric("Failed Imports", failed_uploads)
            
        except Exception as e:
            progress.empty()
            status.empty()
            st.error(f"❌ Import Error: {str(e)}")
            with st.expander("View Error Details"):
                st.code(traceback.format_exc())
    else:
        st.warning("⚠️ Please enter Question Bank ID and Authorization Token")