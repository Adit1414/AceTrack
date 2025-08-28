from openai import OpenAI
import random
import time
import textwrap
import os
import pandas as pd
from docx import Document
from services.PromptsDict import prompt_templates
from datetime import datetime
import json
import uuid

# ===============================================================
# === ROBUST PATH CONFIGURATION ===
# ===============================================================

# Get the absolute path of the directory containing this script (Generation.py)
# This will be .../src/MockTestAutomation/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Get the project root directory by going up two levels from the script's directory
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

# Build absolute paths to ensure files are always found
MODEL = 'gpt-4-turbo'
EXCEL_PATH = os.path.join(SCRIPT_DIR, "..", "data", "Syllabus.xlsx")
# Define the path to the backend/data directory
BACKEND_DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")

# Create the output directories inside backend/data
OUTPUT_DIR = os.path.join(BACKEND_DATA_DIR, "generated_files")
RAW_RESPONSES_DIR = os.path.join(BACKEND_DATA_DIR, "raw_responses")

# Ensure the output directories exist at the project root
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RAW_RESPONSES_DIR, exist_ok=True)


# === TOPIC LOADING AND PROMPT GENERATION ===
def load_all_topics(excel_path=EXCEL_PATH):
    """Loads and shuffles topics from the specified Excel file."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Syllabus file not found at the expected path: {excel_path}. Please ensure it exists.")
    try:
        df = pd.read_excel(excel_path)
        if df.empty or len(df.columns) == 0:
            raise ValueError("Syllabus.xlsx is empty or has no columns.")
        topic_column = df.columns[0]
        topics = df[topic_column].dropna().tolist()
        random.shuffle(topics)
        return topics
    except Exception as e:
        # Catch other potential pandas errors
        raise RuntimeError(f"Failed to read or process the Excel file at {excel_path}: {e}")

def validate_topic_capacity(plan, total_topics):
    """Validates if there are enough topics for the requested questions."""
    questions_per_chunk = 5
    total_chunks_requested = sum(num // questions_per_chunk for num in plan.values())
    if total_chunks_requested > len(total_topics) // questions_per_chunk:
        error_msg = f"Not enough unique topics to generate the requested number of questions. Topics available: {len(total_topics)}, Questions requested: {sum(plan.values())}"
        raise ValueError(error_msg)

# ... (rest of the functions like build_prompt_from_template, generate_all_prompts) ...

def build_prompt_from_template(topics_list, template_key, num_of_questions, EXAM):
    """Builds a GPT prompt from a template with the given topics."""
    topics_str = "\n".join([f"{i+1}. {topic}" for i, topic in enumerate(topics_list)])
    randomized_answer_key = ', '.join(str(n) for n in random.choices(range(1, 5), k=5))
    template = prompt_templates.get(template_key, "")
    return template.format(topics=topics_str, answer_key=randomized_answer_key, num=num_of_questions, exam=EXAM)

def generate_all_prompts(plan, topics, exam):
    """Generates a list of all prompts to be sent to the GPT API."""
    prompts = []
    topic_index = 0
    questions_per_chunk = 5
    for qtype, count in plan.items():
        if topic_index + (count // questions_per_chunk * questions_per_chunk) > len(topics):
            raise ValueError("Topic index out of bounds. This indicates a logic error in topic validation.")
        for _ in range(count // questions_per_chunk):
            chunk = topics[topic_index:topic_index + questions_per_chunk]
            topic_index += questions_per_chunk
            prompt = build_prompt_from_template(chunk, qtype, "five", exam)
            prompts.append((qtype, prompt))
    return prompts

# === FILE OPERATIONS ===
def save_to_docx(content, filename):
    """Saves the given content to a .docx file in the output directory."""
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        doc = Document()
        doc.add_paragraph(content)
        doc.save(path)
    except Exception as e:
        raise IOError(f"❌ Cannot access {path}. Details: {e}")

def save_raw_response(text, folder=RAW_RESPONSES_DIR):
    """Saves the raw GPT response for debugging purposes."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"gpt_response_{timestamp}.docx"
    path = os.path.join(folder, filename)
    doc = Document()
    doc.add_paragraph(text)
    doc.save(path)
    print(f"✅ Raw response saved to: {path}")


# === GPT HANDLING ===
def call_gpt(prompt, testing, chunks, retries=3):
    """Calls the OpenAI API with a given prompt, with retries."""
    if testing:
        time.sleep(1)
        return "\n\n".join([
            f"--Question Starting--\nQ{i+1}. This is a sample test question for type {prompt[:3]}.\nAnswer: A\nExplanation: This is a test explanation."
            for i in range(chunks)
        ])
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a JEE Mains paper setter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ GPT attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    raise RuntimeError("❌ All GPT API retries failed.")


# === CORE EXECUTION LOGIC ===
def handle_generation(prompts, TESTING):
    """Handles the question generation loop, calling GPT for each prompt."""
    all_questions = []
    skipped_chunks = []
    questions_per_chunk = 5
    for qtype, prompt in prompts:
        print(f"Generating questions for type: {qtype}")
        try:
            response = call_gpt(prompt, TESTING, questions_per_chunk)
            if not TESTING:
                save_raw_response(response) 

            questions = [q.strip() for q in textwrap.dedent(response).split("--Question Starting--") if q.strip()]
            
            if len(questions) != questions_per_chunk:
                print(f"⚠️ GPT returned {len(questions)} questions instead of {questions_per_chunk}. Skipping this chunk.")
                skipped_chunks.append(questions)
                continue
            
            all_questions.extend(questions)
        except Exception as e:
            print(f"An error occurred during generation for prompt type {qtype}: {e}")
            continue
            
    random.shuffle(all_questions)
    return all_questions, skipped_chunks


# === MAIN ENTRY POINT FOR BACKEND ===
def run_generation_task(plan: dict, testing_mode: bool, exam_name: str):
    """Main function to be called by the FastAPI """
    try:
        print(f"Starting generation for {exam_name} with plan: {plan}")
        
        run_id = uuid.uuid4().hex[:8]
        questions_filename = f"Questions_{run_id}.docx"
        skipped_filename = f"Skipped_{run_id}.docx"

        topics = load_all_topics()
        validate_topic_capacity(plan, topics)
        
        prompts = generate_all_prompts(plan, topics, exam_name)
        
        generated_questions, skipped_chunks = handle_generation(prompts, testing_mode)
        if not generated_questions:
             raise RuntimeError("No questions were successfully generated. Check logs for API errors or response format issues.")
        
        save_to_docx("\n\n".join(generated_questions), questions_filename)
        
        if skipped_chunks:
            skipped_text = "\n\n".join([
                f"Skipped Chunk {i+1}:\n" + "\n\n".join(str(q) for q in chunk)
                for i, chunk in enumerate(skipped_chunks)
            ])
            save_to_docx(skipped_text, skipped_filename)

        print("\n✅ Mock Test Generation Completed.")
        
        generated_files = {"questions": questions_filename}
        if skipped_chunks:
            generated_files["skipped"] = skipped_filename

        return {
            "success": True,
            "message": "Questions generated successfully.",
            "files": generated_files
        }

    except Exception as e:
        error_message = f"Question generation failed: {str(e)}"
        print(f"❌ {error_message}")
        return {"success": False, "message": error_message, "files": {}}