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

# Updated prompt template
prompt_template = """
Generate {num_questions} unique multiple-choice questions (MCQs) about {topic} with {difficulty} difficulty. The questions should be of type: {question_type}.

Topic Focus: Ensure all questions are directly related to {topic}. Do not include questions about unrelated concepts unless explicitly requested.

Difficulty Levels:
{difficulty_definition}

Question Types:
{question_type_instruction}

Format each question and answer as follows:

Q1. [Question text]
1) [Option 1]
2) [Option 2]
3) [Option 3]
4) [Option 4]
Correct answer: [Correct option number]
Difficulty: {difficulty}
Subject: [Relevant subject area]
Topic: {topic}
Sub-topic: [Relevant sub-topic of {topic}]
Tags: [Relevant tags related to {topic}]

---

Repeat this format for all {num_questions} questions. Ensure that each question is separated by the "---" delimiter.

Remember to vary the complexity and focus of the questions while maintaining the specified difficulty level and question type, always focusing on {topic}.
"""

conceptual_instruction = """
Focus on theoretical understanding of {topic}. Questions should test knowledge of definitions, principles, and concepts without necessarily involving code.
"""

factual_instruction = """
Emphasize specific facts, rules, or characteristics related to {topic}. Questions should test recall and precise knowledge of {topic}.
"""

problem_solving_instruction = """
For problem-solving questions related to {topic}, provide code snippets where required and focus on the following types of questions:

1. Output prediction: "What will be the output of the following code that demonstrates {topic}?"
2. Error identification: "Which line contains an error related to {topic} in the code below?"
3. Debugging: "What change needs to be made to fix the bug related to {topic} in this code?"
   For debugging questions, provide a code snippet with a bug and ask what change is needed to fix it. 
   The options should be in code format. For example:

   The following code snippet attempts to demonstrate the use of {topic}:
   ```
   // Code demonstrating {topic}
   // ...
   ```
   What change needs to be made to fix the bug related to {topic} in this code?

   1) ```
      // Option 1 demonstrating a fix related to {topic}
      ```
   2) ```
      // Option 2 demonstrating a fix related to {topic}
      ```
   3) ```
      // Option 3 demonstrating a fix related to {topic}
      ```
   4) ```
      // Option 4 demonstrating a fix related to {topic}
      ```

4. Code completion: "Which option correctly completes the missing part of this code related to {topic}?"
5. Concept identification: "Which {topic}-related concept is demonstrated in this snippet?"
6. Best practices: "Which of the following changes would improve the code's use of {topic}?"
7. Function behavior: "What does the following function do with respect to {topic}?"
8. Variable state: "What will be the value of variable X after this code related to {topic} executes?"
9. Logical equivalence: "Which of the following code snippets is logically equivalent to the given code in terms of {topic}?"
10. Code optimization: "Which option provides the most optimized version of this code with respect to {topic}?"
11. Algorithm selection: "Which algorithm is most appropriate for implementing this {topic}-related functionality?"
12. Time complexity: "What is the time complexity of the following algorithm related to {topic}?"
13. Space complexity: "What is the space complexity of the following function implementing {topic}?"

Ensure a mix of these question types in your generated MCQs, always focusing on {topic}. For debugging questions, always provide the options in code format. Use pseudocode or a general programming syntax that can be easily understood across different programming languages.
"""

# Conceptual/Factual difficulty definitions
conceptual_factual_easy = """
- Test basic understanding and recall of {topic} concepts
- Use simple terminology and straightforward questions
- Focus on fundamental aspects of {topic}
- Have clear, distinct options with only one correct answer
- Require basic knowledge and simple application of {topic}

Example:
Q: What is the primary purpose of {topic} in programming?
1) [Basic purpose 1]
2) [Basic purpose 2]
3) [Basic purpose 3]
4) [Basic purpose 4]
Correct answer: [Correct option number]
"""

conceptual_factual_medium = """
- Test deeper understanding of {topic} concepts
- Require application of knowledge in slightly more complex scenarios
- May involve comparing or contrasting different aspects of {topic}
- Include more nuanced options that require careful consideration
- Test understanding of how {topic} relates to other basic programming concepts

Example:
Q: How does {topic} differ from [related concept] in terms of [specific aspect]?
1) [Nuanced difference 1]
2) [Nuanced difference 2]
3) [Nuanced difference 3]
4) [Nuanced difference 4]
Correct answer: [Correct option number]
"""

conceptual_factual_hard = """
- Test advanced understanding and intricate details of {topic}
- Require analysis and evaluation of complex aspects of {topic}
- May involve edge cases or less common applications of {topic}
- Have very plausible distractors that require expert knowledge to differentiate
- Test deep understanding of how {topic} interacts with advanced programming concepts

Example:
Q: In what scenario would using {topic} be disadvantageous compared to [alternative approach]?
1) [Complex scenario 1]
2) [Complex scenario 2]
3) [Complex scenario 3]
4) [Complex scenario 4]
Correct answer: [Correct option number]
"""

# Problem-solving difficulty definitions
problem_solving_easy = """
- Test basic syntax and simple programming concepts related to {topic}
- Involve single operations or straightforward code snippets
- Focus on fundamental data types, operators, and control structures relevant to {topic}
- Have clear, distinct options with only one correct answer
- Require recall of basic programming rules and simple application of knowledge about {topic}

Example:
Q: What will be the output of the following code snippet related to {topic}?
1) [Moderate complexity result 1]
2) [Moderate complexity result 2]
3) [Moderate complexity result 3]
4) [Moderate complexity result 4]
Correct answer: [Correct option number]
"""

problem_solving_medium = """
- Require application of {topic} concepts in moderately complex scenarios
- Involve multi-step problem-solving or combining multiple simple concepts related to {topic}
- Test understanding of programming principles as they relate to {topic}
- Include more nuanced distractors that require careful consideration of behavior with {topic}
- Involve control structures, basic algorithms, or simple data structures in the context of {topic}
- May require analysis of short code snippets or simple debugging tasks involving {topic}

Example:
Q: What will be the output of the following code demonstrating {topic}?
1) [Moderate complexity result 1]
2) [Moderate complexity result 2]
3) [Moderate complexity result 3]
4) [Moderate complexity result 4]
Correct answer: [Correct option number]
"""

problem_solving_hard = """
- Test deep understanding and ability to apply advanced {topic} concepts in complex scenarios
- Require critical thinking, problem-solving, and analysis of sophisticated code related to {topic}
- Involve advanced concepts like algorithms, data structures, or language-specific features as they pertain to {topic}
- Have very plausible distractors that require expert knowledge of {topic} to differentiate
- May require optimization, debugging of complex code, or understanding of underlying principles in relation to {topic}
- Focus on efficiency, best practices, and idiomatic solutions involving {topic}

Example:
Q: Which of the following code snippets most efficiently implements {topic}?
1) ```
   // Complex implementation option 1
   ```
2) ```
   // Complex implementation option 2
   ```
3) ```
   // Complex implementation option 3
   ```
4) ```
   // Complex implementation option 4
   ```
Correct answer: [Correct option number]
"""

def generate_mcqs(topic, num_questions, difficulty, question_type, selected_filters=None, max_retries=3):
    difficulty_definitions = {
        "Conceptual": {
            "Easy": conceptual_factual_easy,
            "Medium": conceptual_factual_medium,
            "Hard": conceptual_factual_hard
        },
        "Factual": {
            "Easy": conceptual_factual_easy,
            "Medium": conceptual_factual_medium,
            "Hard": conceptual_factual_hard
        },
        "Problem-solving": {
            "Easy": problem_solving_easy,
            "Medium": problem_solving_medium,
            "Hard": problem_solving_hard
        }
    }

    question_type_instructions = {
        "Conceptual": conceptual_instruction,
        "Factual": factual_instruction,
        "Problem-solving": problem_solving_instruction
    }

    difficulty_definition = difficulty_definitions[question_type][difficulty].format(topic=topic)
    question_type_instruction = question_type_instructions[question_type].format(topic=topic)

    if selected_filters and question_type == "Problem-solving":
        question_type_instruction += f"\nFocus specifically on these types of problem-solving questions: {', '.join(selected_filters)}."

    prompt = prompt_template.format(
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
        question_type=question_type,
        difficulty_definition=difficulty_definition,
        question_type_instruction=question_type_instruction
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Update with your model name
                messages=[
                    {"role": "system", "content": f"You are an expert in {topic}. Your task is to generate multiple-choice questions specifically about {topic}, adhering strictly to the given instructions for {question_type} questions at {difficulty} difficulty."},
                    {"role": "user", "content": prompt}
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
