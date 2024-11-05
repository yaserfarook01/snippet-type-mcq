import anthropic
import json
import datetime
import logging
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Initialize the AzureOpenAI client
claude_endpoint = os.getenv('CLAUDE_API_KEY')
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def perform_deep_qc_checks(question):
    """
    Perform deep QC checks on individual question
    Returns (is_valid, issues)
    """
    issues = []
    
    # 1. Code Analysis
    if "```" in question:
        code_block = re.search(r'```(\w+)\n(.*?)```', question, re.DOTALL)
        if code_block:
            code = code_block.group(2)
            # Check code indentation
            if not all(line.startswith((' ' * 4, '\t')) for line in code.split('\n') if line.strip()):
                issues.append("Inconsistent code indentation")
            # Check for unclosed brackets/parentheses
            if code.count('{') != code.count('}') or code.count('(') != code.count(')'):
                issues.append("Mismatched brackets or parentheses in code")
            # Check for semicolons in languages that require them
            if code_block.group(1) in ['java', 'javascript', 'cpp']:
                if not all(line.strip().endswith(';') for line in code.split('\n') if line.strip() and not line.strip().endswith('{')):
                    issues.append("Missing semicolons in code")

    # 2. Question Text Analysis
    question_text = re.search(r'Q\d+\.\s*(.*?)(?=\n```|\n1\)|\Z)', question, re.DOTALL)
    if question_text:
        text = question_text.group(1)
        # Check for clarity
        if len(text.split()) < 5:
            issues.append("Question text too short")
        if text.count('?') != 1:
            issues.append("Question should have exactly one question mark")
        # Check for ambiguous words
        ambiguous_words = ['maybe', 'possibly', 'sometimes', 'often', 'usually']
        if any(word in text.lower() for word in ambiguous_words):
            issues.append("Question contains ambiguous words")

    # 3. Options Analysis
    options = re.findall(r'\d+\)\s*(.*?)(?=\n\d+\)|\nCorrect answer:|\Z)', question, re.DOTALL)
    if len(options) == 4:
        # Check option lengths
        lengths = [len(opt.strip()) for opt in options]
        if max(lengths) > 3 * min(lengths):
            issues.append("Options have significantly different lengths")
        
        # Check for similar options
        from difflib import SequenceMatcher
        for i, opt1 in enumerate(options):
            for opt2 in options[i+1:]:
                similarity = SequenceMatcher(None, opt1, opt2).ratio()
                if similarity > 0.8:
                    issues.append("Options too similar to each other")
                    break

        # Check for negative options
        negative_words = ['not', 'never', 'none', 'cannot']
        negative_count = sum(1 for opt in options if any(word in opt.lower() for word in negative_words))
        if negative_count > 1:
            issues.append("Too many negative options")

    # 4. Difficulty Level Check
    difficulty_match = re.search(r'Difficulty:\s*(\w+)', question)
    if difficulty_match:
        difficulty = difficulty_match.group(1).lower()
        if difficulty == 'easy':
            # Check if question is actually easy
            complex_indicators = ['advanced', 'complex', 'detailed', 'in-depth']
            if any(indicator in question.lower() for indicator in complex_indicators):
                issues.append("Question complexity doesn't match Easy difficulty")

    return len(issues) == 0, issues

def perform_qc_with_claude(input_file='question_prompt.txt', output_file='qced_mcq.txt', log_file='qc_logs.txt'):
    try:
        claude = anthropic.Anthropic(api_key=claude_endpoint)
        
        with open(input_file, 'r') as f:
            mcqs = f.read()
            # Clean up input text - remove any leading text before first question
            mcqs = re.sub(r'^.*?(?=Q\d+\.)', '', mcqs, flags=re.DOTALL)
            questions = [q.strip() for q in mcqs.split('---') if q.strip() and q.strip().startswith('Q')]
            input_question_count = len(questions)
            
            question_numbers = []
            for q in questions:
                match = re.search(r'Q(\d+)\.', q)
                if match:
                    question_numbers.append(match.group(1))
            
            logger.info(f"Found {input_question_count} questions: Q{', Q'.join(question_numbers)}")

        BATCH_SIZE = 5
        all_corrected_mcqs = []
        all_qc_reports = []

        for i in range(0, len(questions), BATCH_SIZE):
            batch_questions = questions[i:i + BATCH_SIZE]
            batch_count = len(batch_questions)
            current_question_numbers = question_numbers[i:i + BATCH_SIZE]
            
            batch_mcqs = '\n\n'.join(batch_questions)
            
            logger.info(f"Processing batch {i//BATCH_SIZE + 1}: Questions Q{', Q'.join(current_question_numbers)}")

            prompt = f"""
            Review these {batch_count} MCQs and output them in the following format:

            Q[number]. [Question text]
            ```[language]
            [code]
            ```
            1) [option]
            2) [option]
            3) [option]
            4) [option]
            Correct answer: [number]
            Difficulty: [level]
            Subject: Programming
            Topic: [topic]
            Sub-topic: [subtopic]
            Tags: [tags]
            ---

            CRITICAL:
            1. Output EXACTLY {batch_count} questions
            2. Use these exact numbers: {', '.join([f'Q{n}' for n in current_question_numbers])}
            3. Keep questions in same order
            4. Add "---" after each question
            5. After all questions, add your QC report starting with "=== QC REPORT ==="

            CRITICAL REQUIREMENTS:
            1. Output Format:
               - MUST output exactly {batch_count} questions
               - Maintain original question numbers
               - Include ALL questions, corrected or not
               - Follow exact format specified below

            2. Technical Accuracy:
               - Code snippets must be syntactically perfect
               - Variable names must follow language conventions
               - Ensure proper indentation and formatting
               - Verify all technical concepts are accurate
               - Check for language-specific syntax rules

            3. Question Quality:
               - Clear, unambiguous wording
               - Single, focused learning objective
               - Appropriate difficulty level
               - No misleading or trick questions
               - Technically precise terminology

            4. Options Quality:
               - All options must be plausible
               - No partially correct answers
               - Consistent length and format
               - No overlapping answers
               - Grammatically parallel structure

            5. Difficulty Calibration:
               - Easy: Basic concepts, straightforward application
               - Medium: Combined concepts, moderate analysis
               - Hard: Complex scenarios, deep understanding

            Format for EACH question:
            Q[number]. [Clear, specific question text]
            ```[language]
            [Syntactically correct code with proper indentation]
            ```
            1) [Distinct, plausible option]
            2) [Distinct, plausible option]
            3) [Distinct, plausible option]
            4) [Distinct, plausible option]
            Correct answer: [number]
            Difficulty: [Easy/Medium/Hard]
            Subject: Programming
            Topic: [Specific programming topic]
            Sub-topic: [Specific sub-topic]
            Tags: [relevant, comma-separated, tags]

            STRICT PROHIBITIONS:
            - No "None of the above" or "All of the above"
            - No compound options ("Both A and B")
            - No True/False questions
            - No ambiguous language
            - No incorrect technical information
            - No inconsistent formatting
            - No unclear code examples
            - No missing semicolons or brackets
            - No improper indentation
            - No undefined variables

            Here are the questions to review:

            {batch_mcqs}
            """

            response = claude.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            batch_response = response.content[0].text.strip()
            
            # Extract questions (everything before QC report)
            if "=== QC REPORT ===" in batch_response:
                questions_part = batch_response.split("=== QC REPORT ===")[0].strip()
            else:
                questions_part = batch_response.strip()

            # Split into individual questions
            response_questions = [q.strip() for q in questions_part.split('---') if q.strip() and q.strip().startswith('Q')]
            
            if len(response_questions) != batch_count:
                logger.error(f"Batch {i//BATCH_SIZE + 1} response:\n{batch_response}")
                raise ValueError(f"Batch {i//BATCH_SIZE + 1} returned {len(response_questions)} questions instead of {batch_count}")

            # Validate question numbers
            for q, expected_num in zip(response_questions, current_question_numbers):
                if not q.startswith(f'Q{expected_num}.'):
                    raise ValueError(f"Question number mismatch. Expected Q{expected_num}")

            all_corrected_mcqs.extend(response_questions)
            all_qc_reports.append(f"Batch {i//BATCH_SIZE + 1} Report:\n{batch_response.split('=== QC REPORT ===')[1].strip() if '=== QC REPORT ===' in batch_response else 'No QC report provided'}")

        # Combine results
        corrected_mcqs = '\n\n---\n\n'.join(all_corrected_mcqs)
        final_qc_report = '\n\n' + '='*50 + '\n\n'.join(all_qc_reports)

        # Save results
        with open(output_file, 'w') as f:
            f.write(corrected_mcqs)
        
        with open(log_file, 'w') as f:
            f.write(f"QC Report Generated at {datetime.datetime.now()}\n")
            f.write(final_qc_report)

        return corrected_mcqs, final_qc_report

    except Exception as e:
        logger.error(f"Error in QC process: {str(e)}")
        raise

def verify_mcq_format(mcq_text):
    """
    Verify if the MCQ follows the required format
    """
    required_elements = [
        "Q", 
        "1)", 
        "2)", 
        "3)", 
        "4)", 
        "Correct answer:", 
        "Difficulty:", 
        "Subject:", 
        "Topic:", 
        "Sub-topic:", 
        "Tags:"
    ]
    
    for element in required_elements:
        if element not in mcq_text:
            return False
    return True

def process_mcqs(input_file, output_file='qced_mcq.txt', log_file='qc_logs.txt'):
    """
    Main function to process MCQs through QC
    """
    try:
        logger.info(f"Starting MCQ processing from {input_file}")
        
        # Verify input file exists and has content
        with open(input_file, 'r') as f:
            original_mcqs = f.read()
            if not original_mcqs.strip():
                raise ValueError("Input file is empty")
            
            # Verify input format
            if not verify_mcq_format(original_mcqs):
                raise ValueError("Input MCQs do not follow the required format")
        
        # Perform QC with Claude
        corrected_mcqs, qc_report = perform_qc_with_claude(input_file, output_file, log_file)
        
        # Verify output format
        if not verify_mcq_format(corrected_mcqs):
            raise ValueError("Generated MCQs do not follow the required format")
        
        # Print status
        if "No issues found" in qc_report:
            logger.info("Quality check completed! No issues found.")
            print("Quality check completed! No issues found.")
        else:
            logger.info("Quality check completed! Some issues were found and corrected.")
            print("Quality check completed! Some issues were found and corrected.")
            print("\nQC Report:")
            print(qc_report)
            
        return True, corrected_mcqs, qc_report
        
    except Exception as e:
        error_msg = f"Error in MCQ processing: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return False, None, error_msg

def save_results(mcqs, output_file):
    """
    Save the processed MCQs to a file
    """
    try:
        with open(output_file, 'w') as f:
            f.write(mcqs)
        logger.info(f"Results saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        return False

if __name__ == "__main__":
    # Configuration
    input_file = 'question_prompt.txt'
    output_file = 'qced_mcq.txt'
    log_file = 'qc_logs.txt'
    
    try:
        # Process MCQs
        success, mcqs, report = process_mcqs(input_file, output_file, log_file)
        
        if success:
            print(f"\nProcessed MCQs saved to: {output_file}")
            print(f"QC logs saved to: {log_file}")
            
            # Optional: Display statistics
            num_questions = len([q for q in mcqs.split('Q') if q.strip()])
            print(f"\nTotal questions processed: {num_questions}")
            
            if "No issues found" not in report:
                print("\nSee QC report for details on corrections made.")
        else:
            print("Failed to process MCQs")
            
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        logger.exception("Error in main process")
