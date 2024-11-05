import json
import re
import logging

def save_to_file(filename, text):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(text)
        logging.info(f"File saved: {filename}")
    except Exception as e:
        logging.error(f"Failed to save file {filename}: {e}")

def convert_to_json_format(input_file, qb_id, created_by, expected_count=None):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split questions by "Q" followed by a number and period
    questions = re.split(r'(?=Q\d+\.)', content)
    # Remove empty strings and clean up
    questions = [q.strip() for q in questions if q.strip()]
    
    logging.info(f"Total questions split: {len(questions)}")
    
    # Validate question count
    if expected_count and len(questions) != expected_count:
        logging.warning(f"Question count mismatch! Expected: {expected_count}, Found: {len(questions)}")
        # Ensure we only process the expected number of questions
        questions = questions[:expected_count]
    
    json_questions = []

    for i, question in enumerate(questions, 1):
        logging.info(f"Processing question {i}")
        
        try:
            # Extract question text and code block
            question_match = re.search(r'Q\d+\.\s*(.*?)(?=\n```|\n1\)|\Z)', question, re.DOTALL)
            if not question_match:
                logging.warning(f"Question {i}: No match for question text")
                continue
            question_text = question_match.group(1).strip()

            # Extract code snippet
            code_match = re.search(r'```(\w+)\n(.*?)```', question, re.DOTALL)
            if code_match:
                language = code_match.group(1)
                code_block = code_match.group(2).strip()
            else:
                code_block = ""

            # Combine question text and code block
            question_data = f"<p>{question_text}</p>"
            if code_block:
                question_data += f"\n$$$examly{code_block}"

            # Extract options using new pattern
            options_pattern = r'\d+\)\s*(.*?)(?=\n\d+\)|\nCorrect answer:|\Z)'
            options = re.findall(options_pattern, question, re.DOTALL)
            options = [opt.strip() for opt in options]

            if len(options) != 4:
                logging.warning(f"Question {i}: Found {len(options)} options instead of 4")
                continue

            # Extract correct answer
            correct_answer_match = re.search(r'Correct answer:\s*(\d+)', question)
            if not correct_answer_match:
                logging.warning(f"Question {i}: No correct answer found")
                continue
            correct_answer = int(correct_answer_match.group(1)) - 1

            # Extract difficulty
            difficulty_match = re.search(r'Difficulty:\s*(\w+)', question)
            difficulty = difficulty_match.group(1) if difficulty_match else "Easy"

            # Extract tags
            tags_match = re.search(r'Tags:\s*(.*?)(?=\n|$)', question)
            tags = [tag.strip() for tag in tags_match.group(1).split(',')] if tags_match else []

            json_question = {
                "question_type": "mcq_single_correct",
                "question_data": question_data,
                "options": [{"text": option, "media": ""} for option in options],
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
                "createdBy": created_by
            }
            
            if qb_id:
                json_question["qb_id"] = qb_id
                
            json_questions.append(json_question)
            logging.info(f"Successfully processed question {i}")
            
        except Exception as e:
            logging.error(f"Error processing question {i}: {str(e)}")
            logging.debug(f"Question content: {question}")
            continue

     # Final validation of JSON question count
    if expected_count and len(json_questions) != expected_count:
        logging.warning(f"JSON conversion produced incorrect number of questions. Expected: {expected_count}, Got: {len(json_questions)}")
        json_questions = json_questions[:expected_count]

    logging.info(f"Total questions successfully processed: {len(json_questions)}")
    return json_questions

def save_unique_mcqs(mcqs, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mcqs, f, ensure_ascii=False, indent=2)
