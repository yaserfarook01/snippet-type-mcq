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

def convert_to_json_format(input_file, qb_id, created_by):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    questions = re.split(r'\n---\n', content)
    logging.info(f"Total questions split: {len(questions)}")
    json_questions = []

    for i, question in enumerate(questions, 1):
        logging.info(f"Processing question {i}")
        
        try:
            # Extract question text and code block, removing the trailing asterisks
            question_match = re.search(r'Q\d+\.\s*(.*?)(?:\*\*)?(?=\n```|\n1\)|\Z)', question, re.DOTALL)
            if not question_match:
                logging.warning(f"Question {i}: No match for question text")
                continue
            question_text = question_match.group(1).strip()

            # Extract code snippet
            code_match = re.search(r'```(?:java|html|javascript|typescript)\n(.*?)```', question, re.DOTALL)
            code_block = code_match.group(1).strip() if code_match else ""

            # Combine question text and code block
            question_data = f"<p>{question_text}</p>"
            if code_block:
                question_data += f"$$$examly{code_block}"

            # Extract options
            options = [option.replace('**', '') for option in re.findall(r'\d+\)\s*(.*?)(?=\n\d+\)|\nCorrect answer:|\Z)', question, re.DOTALL)]
            options = [option.strip() for option in options]

            # Process options to remove extra markup
            processed_options = []
            for option in options:
                # Remove ```java and ``` if present
                option = re.sub(r'```(java|html|javascript|typescript)\n?|```|`', '', option)
                # Remove leading/trailing whitespace and newlines
                option = option.strip()
                processed_options.append(option)

            if len(processed_options) < 2:
                logging.warning(f"Question {i}: Insufficient number of options: {len(processed_options)}")
                continue

            correct_answer_match = re.search(r'Correct answer:\s*(\d+)', question)
            if not correct_answer_match:
                logging.warning(f"Question {i}: No correct answer found")
                continue
            correct_answer = int(correct_answer_match.group(1)) - 1

            if correct_answer < 0 or correct_answer >= len(processed_options):
                logging.warning(f"Question {i}: Correct answer index out of range. Index: {correct_answer}, Options: {len(processed_options)}")
                continue

            difficulty = re.search(r'Difficulty:\s*(\w+)', question)
            difficulty = difficulty.group(1) if difficulty else "Easy"

            tags_match = re.search(r'Tags:\s*(.*)', question)
            tags = [tag.strip() for tag in tags_match.group(1).split(',')] if tags_match else []

            json_question = {
                "question_type": "mcq_single_correct",
                "question_data": question_data,
                "options": [{"text": option, "media": ""} for option in processed_options],
                "answer": {
                    "args": [processed_options[correct_answer]],
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

    logging.info(f"\nTotal questions successfully processed: {len(json_questions)}")
    return json_questions

def save_unique_mcqs(mcqs, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mcqs, f, ensure_ascii=False, indent=2)
