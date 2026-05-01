import json
import threading
import sys
import time
import itertools
from google import genai

# Setup Client
API_KEY = "ADD_THE_API_KEY_HERE" 
client = genai.Client(api_key=API_KEY) 
MODEL_ID = "gemini-2.5-flash"

#Method for Loading Screen Anim
class LoadingAnimation:
    def __init__(self, message="Thinking"):
        self.message = message
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._animate)

    def _animate(self):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if self.stop_event.is_set():
                break
            sys.stdout.write(f'\r{self.message}... {c} ')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 15) + '\r') 

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_event.set()
        self.thread.join()

def Prompt(problem_text):
    prompt = f"""
    You are an expert mathematician. Solve the following problem.
    INSTRUCTIONS:
    Only Provide the Final Answer with a max of 5 line explanation, clearly labeled.

    PROBLEM: {problem_text}

    RESPONSE FORMAT:
    Final Answer: [Insert answer here]
    """
    
    with LoadingAnimation("Gemini is solving the problem"):
        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=prompt
        )
    return response.text

def Judge_Comparison(generated_response, correct_answer):
    judge_prompt = f"""
    Compare the 'Generated Response' against the 'Correct Answer'.
    Generated Response: {generated_response}
    Correct Answer: {correct_answer}
    Are they mathematically/logically equivalent? Answer 'SIMILAR' or 'NOT_SIMILAR'.
    """
    
    with LoadingAnimation("Judging the result"):
        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=judge_prompt
        )
    return response.text

# Load Data
try:
    with open(r'D:\Study\BTU University Subjects\Conversational AI\Project\Questions.json') as f:
        problems = json.load(f)
except FileNotFoundError:
    print("Error: Questions.json file not found at the specified path.")
    sys.exit()

q_data = problems[2]
question = q_data['question']
ground_truth = q_data['correct_answer']

print(f"The Question is: {question}")

# Get Initial Solution
generated_output = Prompt(question)
print(f"--- LLM GENERATED ---\n{generated_output}\n")

# Compare
verdict = Judge_Comparison(generated_output, ground_truth)
if "SIMILAR" in verdict.upper() and "NOT_SIMILAR" not in verdict.upper():
    print(f"VERDICT: SUCCESS (SIMILAR)")
else:
    print("VERDICT: NOT_SIMILAR")
    print("--- Possible Hallucination ---")
    print(f"Expected: {ground_truth}")
    
    correcting_prompt = (
        f"The Question is: {question}, "
        f"LLM Generated Answer was: {generated_output}, "
        f"However, the correct answer is: {ground_truth}. "
        f"Correct the generated output using the ground truth and give the Final Response with steps."
        #f"Correct the answer replacing the generated output and give the Final Response only without steps."
    )
    #Correcting the Result
    with LoadingAnimation("Correcting the Result"):
        correction_response = client.models.generate_content(
            model=MODEL_ID, 
            contents=correcting_prompt
        )
    print(f"Correction Analysis:\n{correction_response.text}")