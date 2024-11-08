# convertor.py

import json
import re
import logging
from typing import List, Dict, Optional

def save_to_file(filename: str, text: str) -> None:
    """Save text to file with error handling"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(text)
        logging.info(f"File saved: {filename}")
    except Exception as e:
        logging.error(f"Failed to save file {filename}: {e}")
        raise

def extract_question_components(question: str, index: int) -> Optional[Dict]:
    """Extract all components of a single question"""
    try:
        # Extract question number and text
        question_match = re.search(r'Q(\d+)\.\s*(.*?)(?=\n```|\n1\))', question, re.DOTALL)
        if not question_match:
            logging.warning(f"Question {index}: Invalid question format")
            return None
            
        question_text = question_match.group(2).strip()
        
        # Extract code block if present
        code_block = ""
        code_match = re.search(r'```(\w+)\n(.*?)```', question, re.DOTALL)
        if code_match:
            code_block = code_match.group(2).strip()
            # Remove code block from question text
            question = question.replace(code_match.group(0), '')
            
        # Format question data
        question_data = f"<p>{question_text}</p>"
        if code_block:
            question_data += f"\n$$$examly{code_block}"
            
        # Extract options
        options_text = re.search(r'((?:^|\n)\d+\).*?)(?=Correct answer:|$)', question, re.DOTALL)
        if not options_text:
            logging.warning(f"Question {index}: Could not find options section")
            return None
            
        options = re.findall(r'\d+\)\s*(.*?)(?=\n\d+\)|\nCorrect answer:|\Z)', options_text.group(1), re.DOTALL)
        options = [opt.strip() for opt in options]
        
        if len(options) != 4:
            logging.warning(f"Question {index}: Found {len(options)} options instead of 4")
            return None
            
        # Extract correct answer
        correct_match = re.search(r'Correct answer:\s*(\d+)', question)
        if not correct_match:
            logging.warning(f"Question {index}: No correct answer found")
            return None
            
        correct_answer = int(correct_match.group(1)) - 1
        if correct_answer not in range(4):
            logging.warning(f"Question {index}: Invalid correct answer number")
            return None
            
        # Extract metadata
        difficulty_match = re.search(r'Difficulty:\s*(\w+)', question)
        difficulty = difficulty_match.group(1) if difficulty_match else "Easy"
        
        tags_match = re.search(r'Tags:\s*(.*?)(?=\n|$)', question)
        tags = [tag.strip() for tag in tags_match.group(1).split(',')] if tags_match else []
        
        return {
            "question_type": "mcq_single_correct",
            "question_data": question_data,
            "options": [{"text": opt, "media": ""} for opt in options],
            "answer": {
                "args": [options[correct_answer]],
                "partial": []
            },
            "subject_id": None,
            "topic_id": None,
            "sub_topic_id": None,
            "blooms_taxonomy": None,
            "course_outcome": None,
            "program_outcome": None,
            "hint": [],
            "answer_explanation": {
                "args": []
            },
            "manual_difficulty": difficulty,
            "question_editor_type": 3 if code_block else 1,
            "linked_concepts": "",
            "tags": tags,
            "question_media": [],
        }
    except Exception as e:
        logging.error(f"Error processing question {index}: {str(e)}")
        return None

def convert_to_json_format(input_file: str, qb_id: Optional[str] = None, created_by: Optional[str] = None, expected_count: Optional[int] = None) -> List[Dict]:
    """
    Convert MCQs to JSON format
    
    Args:
        input_file: Path to input file containing MCQs
        qb_id: Optional question bank ID
        created_by: Optional creator ID
        expected_count: Optional expected number of questions
        
    Returns:
        List of processed questions in JSON format
    """
    try:
        # Read and split questions
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Split by question markers and clean
        questions = re.split(r'(?=Q\d+\.)|(?=---)', content)
        questions = [q.strip() for q in questions if q.strip() and q.startswith('Q')]
        
        total_questions = len(questions)
        logging.info(f"Found {total_questions} questions to process")
        
        # Validate question count if expected_count is provided
        if expected_count and total_questions != expected_count:
            logging.warning(f"Question count mismatch! Expected: {expected_count}, Found: {total_questions}")
            if total_questions > expected_count:
                questions = questions[:expected_count]
                logging.info(f"Truncated to first {expected_count} questions")
        
        # Process questions
        json_questions = []
        for i, question in enumerate(questions, 1):
            logging.info(f"Processing question {i}/{len(questions)}")
            
            question_data = extract_question_components(question, i)
            if question_data:
                # Add additional fields if provided
                if created_by:
                    question_data["createdBy"] = created_by
                if qb_id:
                    question_data["qb_id"] = qb_id
                    
                json_questions.append(question_data)
                
        processed_count = len(json_questions)
        if expected_count and processed_count != expected_count:
            logging.warning(f"Not all questions were successfully processed. Expected: {expected_count}, Processed: {processed_count}")
        else:
            logging.info(f"Successfully processed {processed_count} questions")
            
        return json_questions
        
    except Exception as e:
        logging.error(f"Error in conversion process: {str(e)}")
        raise
    
def save_unique_mcqs(mcqs: List[Dict], filename: str) -> None:
    """Save MCQs to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(mcqs, f, ensure_ascii=False, indent=2)
        logging.info(f"Successfully saved {len(mcqs)} questions to {filename}")
    except Exception as e:
        logging.error(f"Failed to save MCQs to file: {str(e)}")
        raise

# Export all required functions
__all__ = ['save_to_file', 'convert_to_json_format', 'save_unique_mcqs']