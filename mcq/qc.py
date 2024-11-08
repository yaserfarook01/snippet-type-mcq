import dspy
import os
from dotenv import load_dotenv
import anthropic
import re
import datetime
import logging
from typing import Tuple, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Configure Anthropic client
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    raise ValueError("CLAUDE_API_KEY not found in environment variables")

# Configure DSPy with Anthropic
class AnthropicLLM(dspy.LM):
    def __init__(self):
        super().__init__(model="claude-3-sonnet-20240229")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 4096
        self.temperature = 0
        
    def basic_request(self, prompt, **kwargs):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logging.error(f"Error in LLM request: {str(e)}")
            raise

# Configure DSPy
lm = AnthropicLLM()
dspy.configure(lm=lm)

class MCQValidator(dspy.Signature):
    """Validate and improve MCQ quality"""
    
    input_question = dspy.InputField(desc="Input MCQ to validate")
    reasoning = dspy.OutputField(desc="Reasoning about the validation")
    valid_question = dspy.OutputField(desc="Validated and improved MCQ")
    feedback = dspy.OutputField(desc="Validation feedback and improvements made")

    def forward(self, input_question):
        """Process the input question and return validated results"""
        try:
            # Get validation prompt
            prompt = self.validate(input_question)
            
            # Process with LLM
            response = self.lm(prompt)
            
            # Extract components from response
            reasoning = "Validation complete"
            valid_question = input_question
            feedback = "Question validated successfully"
            
            # Try to extract improved question if available
            if "IMPROVED QUESTION:" in response:
                valid_question = response.split("IMPROVED QUESTION:")[1].split("FEEDBACK:")[0].strip()
                
            # Try to extract feedback if available
            if "FEEDBACK:" in response:
                feedback = response.split("FEEDBACK:")[1].strip()
            
            return dspy.Prediction(
                reasoning=reasoning,
                valid_question=valid_question,
                feedback=feedback
            )
            
        except Exception as e:
            logging.error(f"Error in validation: {str(e)}")
            return dspy.Prediction(
                reasoning="Validation failed",
                valid_question=input_question,
                feedback=f"Error: {str(e)}"
            )

    def validate(self, question):
        prompt = f"""
        Review and improve this MCQ following these exact requirements:

        FORMAT REQUIREMENTS:
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

        VALIDATION REQUIREMENTS:
        1. Question format and numbering
        2. Code block syntax and indentation
        3. Option formatting and count
        4. Metadata completeness
        5. Technical accuracy

        Original Question:
        {question}

        Please provide your response in this exact format:

        REASONING:
        [Your analysis of the question]

        IMPROVED QUESTION:
        [The complete question with any necessary improvements]

        FEEDBACK:
        [Specific changes made or improvements needed]
        """
        return prompt

class MCQProcessor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.validator = dspy.ChainOfThought(MCQValidator)
        
    def forward(self, question):
        """Process a single MCQ"""
        try:
            # Extract question number for maintaining order
            match = re.search(r'Q(\d+)\.', question)
            q_num = match.group(1) if match else "1"
            
            result = self.validator(input_question=question)
            
            if not hasattr(result, 'valid_question') or not result.valid_question:
                logging.warning(f"Validator returned incomplete result for Q{q_num}")
                return question, "Validation failed: incomplete result"
            
            # Verify the output format
            if not result.valid_question.startswith(f"Q{q_num}."):
                # Fix question number if needed
                result.valid_question = f"Q{q_num}." + result.valid_question.split('.', 1)[1]
                
            return result.valid_question, result.feedback
            
        except Exception as e:
            logging.error(f"Error in MCQ processing: {str(e)}")
            return question, f"Processing error: {str(e)}"

def process_mcqs(input_file: str, output_file: str = 'qced_mcq.txt', log_file: str = 'qc_logs.txt') -> Tuple[bool, Optional[str], Optional[str]]:
    """Process all MCQs using DSPy"""
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            questions = f.read().split('---')
            questions = [q.strip() for q in questions if q.strip()]
            
        processor = MCQProcessor()
        processed_questions = []
        feedback_list = []
        
        # Process each question
        for i, q in enumerate(questions, 1):
            print(f"Processing question {i}/{len(questions)}")
            try:
                valid_q, feedback = processor(q)
                
                # Verify and fix formatting
                if not valid_q.endswith('---'):
                    valid_q += '\n---'
                
                processed_questions.append(valid_q)
                feedback_list.append(feedback)
                
            except Exception as e:
                logging.error(f"Error processing question {i}: {str(e)}")
                # Keep original question if processing fails
                processed_questions.append(q + '\n---')
                feedback_list.append(f"Processing failed: {str(e)}")
                continue
            
        # Combine processed questions
        corrected_mcqs = '\n\n'.join(processed_questions)
            
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(corrected_mcqs)
            
        # Generate QC report
        qc_report = f"QC Report Generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for i, feedback in enumerate(feedback_list, 1):
            qc_report += f"Question {i} Feedback:\n{feedback}\n\n{'='*50}\n\n"
            
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(qc_report)
                
        return True, corrected_mcqs, qc_report
        
    except Exception as e:
        logging.error(f"Error processing MCQs: {str(e)}")
        return False, None, str(e)

if __name__ == "__main__":
    try:
        # Configuration
        input_file = 'question_prompt.txt'
        output_file = 'qced_mcq.txt'
        log_file = 'qc_logs.txt'
        
        # Process MCQs
        success, mcqs, report = process_mcqs(input_file, output_file, log_file)
        
        if success:
            print(f"MCQs processed successfully!")
            print(f"Results saved to: {output_file}")
            print(f"QC report saved to: {log_file}")
        else:
            print("Failed to process MCQs")
    except Exception as e:
        print(f"Error in main process: {str(e)}")