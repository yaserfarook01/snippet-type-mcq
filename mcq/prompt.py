import json
import logging
from openai import AzureOpenAI
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the AzureOpenAI client
azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')
client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version="2024-02-01"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load JSON files
try:
    with open('question_type_instructions.json', 'r') as f:
        question_type_instructions = json.load(f)
    logger.info("Successfully loaded question_type_instructions.json")
except Exception as e:
    logger.error(f"Error loading question_type_instructions.json: {e}")
    question_type_instructions = {}

try:
    with open('difficulty_definitions.json', 'r') as f:
        difficulty_definitions = json.load(f)
    logger.info("Successfully loaded difficulty_definitions.json")
except Exception as e:
    logger.error(f"Error loading difficulty_definitions.json: {e}")
    difficulty_definitions = {}

try:
    with open('few_shot_examples.json', 'r') as f:
        few_shot_examples = json.load(f)
    logger.info("Successfully loaded few_shot_examples.json")
except Exception as e:
    logger.error(f"Error loading few_shot_examples.json: {e}")
    few_shot_examples = {}

# Define problem_solving_types
problem_solving_types = [
    "Output prediction",
    "Error identification",
    "Debugging",
    "Code completion",
    "Time complexity",
    "Space complexity",
    "Concept identification",
    "Best practices",
    "Function behavior",
    "Variable state",
    "Logical equivalence",
    "Code optimization",
    "Output ordering",
    "Data structure selection",
    "Algorithm selection"
]

def generate_mcqs(topic, num_questions, difficulty, question_type, selected_filters=None, max_retries=3):
    logging.info(f"Generating MCQs for topic: {topic}, num_questions: {num_questions}, difficulty: {difficulty}, question_type: {question_type}, filters: {selected_filters}")
    
    # Validate inputs
    valid_difficulties = ["Easy", "Medium", "Hard"]
    valid_question_types = ["Conceptual", "Factual", "Problem-solving", "Scenario-based"]
    
    if difficulty not in valid_difficulties:
        logging.error(f"Invalid difficulty: {difficulty}")
        raise ValueError(f"Invalid difficulty. Must be one of {valid_difficulties}")
    
    if question_type not in valid_question_types:
        logging.error(f"Invalid question_type: {question_type}")
        raise ValueError(f"Invalid question_type. Must be one of {valid_question_types}")

    # Initialize question_type_instruction
    question_type_instruction = question_type_instructions[question_type].format(topic=topic)

    # Add filter-specific instructions
    filter_instructions = ""
    if selected_filters:
        filter_instructions = "Focus EXCLUSIVELY on the following types of questions:\n"
        for filter_type in selected_filters:
            if filter_type in problem_solving_types:
                filter_instructions += f"- {filter_type}\n"

    # Retrieve relevant examples
    relevant_examples = few_shot_examples.get(question_type, {}).get(difficulty, "").format(topic=topic)

    # Safely get relevant examples
    try:
        relevant_examples = few_shot_examples.get(question_type, {}).get(difficulty, "")
        relevant_examples = relevant_examples.format(topic=topic)
    except KeyError as e:
        logging.error(f"KeyError when accessing few_shot_examples: {e}")
        relevant_examples = ""  # Use an empty string if the key is not found
    except Exception as e:
        logging.error(f"Error when formatting few_shot_examples: {e}")
        relevant_examples = ""  # Use an empty string if there's any other error

    # Meta-sorting prompt
    meta_sorting_prompt = f"""
    Task: Create a structured plan for generating {num_questions} {difficulty}-level {question_type} MCQs about {topic}.

    First, review these example questions in the desired format:

    {relevant_examples}

    Now, create a plan following this structure:

    1. List {num_questions} distinct sub-topics or aspects of {topic} that would be appropriate for {difficulty}-level {question_type} questions.
    2. For each sub-topic, briefly describe a specific concept or problem that could be addressed in an MCQ.
    3. Indicate the type of question (e.g., definition, application, analysis) for each sub-topic.
    4. Suggest a plausible correct answer and three distractors for each question.

    Format your response as a numbered list, with each item containing:
    - Sub-topic
    - Specific concept/problem
    - Question type
    - Correct answer
    - Three distractors

    Example:
    1. Sub-topic: [Specific aspect of {topic}]
       Concept: [Brief description of the concept to be tested]
       Question type: [e.g., Definition, Application, Analysis]
       Correct answer: [Brief description of the correct answer]
       Distractors: [Three plausible but incorrect options]

    2. ...

    Ensure that your plan covers a diverse range of aspects within {topic} and aligns with the {difficulty} difficulty level and {question_type} question type. Use the provided examples as a guide for the level of detail and complexity expected.
    """

    # Generate the meta-sorting plan
    for attempt in range(max_retries):
        try:
            meta_sorting_response = client.chat.completions.create(
                model="gpt-4o-mini",  # Update with your model name
                messages=[
                    {"role": "system", "content": f"You are an expert in {topic} and MCQ planning. Your task is to create a structured plan for generating high-quality, specific multiple-choice questions about {topic}, using the provided examples as a guide."},
                    {"role": "user", "content": meta_sorting_prompt}
                ]
            )
            if meta_sorting_response and meta_sorting_response.choices:
                meta_sorting_plan = meta_sorting_response.choices[0].message.content
                break
            else:
                logging.error("Empty response from LLM for meta-sorting")
        except Exception as e:
            logging.error(f"Meta-sorting attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
    else:
        raise Exception("Failed to generate meta-sorting plan after multiple attempts")

    difficulty_definition = difficulty_definitions[question_type][difficulty].format(topic=topic)
    question_type_instruction = question_type_instructions[question_type].format(topic=topic)

    if selected_filters and question_type == "Problem-solving":
        question_type_instruction += f"\nFocus specifically on these types of problem-solving questions: {', '.join(selected_filters)}."

    # Enhanced prompt with meta-sorting plan and few-shot examples
    enhanced_prompt = f"""
    Task: Generate {num_questions} unique multiple-choice questions (MCQs) about {topic} with {difficulty} difficulty. The questions should be of type: {question_type}.

    Context: You are an expert in {topic} and an experienced educator. Your goal is to create challenging yet fair MCQs that test a student's understanding of {topic} at the {difficulty} level.

    First, review these example questions in the desired format:

    {relevant_examples}

    Now, use the following meta-sorting plan to guide your question generation:

    {meta_sorting_plan}

    Guidelines:
    1. Ensure all questions are directly related to {topic}.
    2. Adhere to the following difficulty level:
    {difficulty_definitions[question_type][difficulty].format(topic=topic)}

    3. Follow these question type instructions:
    {question_type_instruction}

    4. {filter_instructions}

    5. Use the following format for each question:

    Q[number]. [Question text]
    1) [Option 1]
    2) [Option 2]
    3) [Option 3]
    4) [Option 4]
    Correct answer: [Correct option number]
    Difficulty: {difficulty}
    Subject: [Relevant subject area]
    Topic: {topic}
    Sub-topic: [Relevant sub-topic of {topic} from the meta-sorting plan]
    Tags: [Relevant tags related to {topic}]

    ---

    5. Ensure each question is separated by the "---" delimiter.
    6. Vary the complexity and focus of the questions while maintaining the specified difficulty level and question type.
    7. For each question, randomize the order of the options and ensure the correct answer is not always in the same position.
    8. Use clear and concise language, avoiding ambiguity in both questions and answer options.
    9. For problem-solving questions, include code snippets where appropriate, using a general programming syntax that can be understood across different languages.

    Quality Check:
    - Ensure each question has exactly one correct answer.
    - Verify that all distractors (incorrect options) are plausible but clearly incorrect to a knowledgeable student.
    - Check that the questions cover a range of aspects within the {topic}, as outlined in the meta-sorting plan.
    - Confirm that the difficulty of each question matches the specified {difficulty} level.

    Begin generating the MCQs now, using the example questions as a guide. Remember to maintain high quality and relevance throughout all {num_questions} questions, focusing ONLY on the specified question types and formats.
    """

    # Generate the MCQs using the enhanced prompt with meta-sorting and few-shot examples
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Update with your model name
                messages=[
                    {"role": "system", "content": f"You are an expert in {topic} and MCQ generation. Your task is to create high-quality, specific multiple-choice questions about {topic}, strictly adhering to the given instructions, meta-sorting plan, and example questions for {question_type} questions at {difficulty} difficulty."},
                    {"role": "user", "content": enhanced_prompt}
                ]
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logging.error("Empty response from LLM")
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying

    raise Exception("Failed to generate MCQs after multiple attempts")