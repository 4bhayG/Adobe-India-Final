import os
from dotenv import load_dotenv
import vertexai
import json
from vertexai.generative_models import GenerativeModel

# Load environment variables from a .env file
load_dotenv() 

# --- Gemini API Configurations ---
# Ensure these environment variables are set in your .env file
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION") 
model_name = os.getenv("GEMINI_MODEL")

# Initialize the Vertex AI SDK
vertexai.init(project=project_id, location=location)
gemini_model = GenerativeModel(model_name=model_name)


def extract_text_from_document(input_dir, document_name):
    """
    Extracts text from the JSON representation of a single document.
    
    This function assumes that for each 'document.pdf', a corresponding 
    'document.json' exists in a 'temp_files' subdirectory.
    """
    json_path = os.path.join(input_dir, "temp_files", document_name.replace('.pdf', '.json'))
    print(f"Extracting text from: {json_path}")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found at {json_path}. Please ensure it exists.")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            # Load the JSON content
            json_content = json.load(f)
            # The 'full_text' key is expected to contain a list of text segments
            text_list = json_content.get('full_text', [])
            # Efficiently join the list of text parts into a single string
            return "".join(text_list)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON in {json_path}: {e}")
    except Exception as e:
        raise IOError(f"Could not read file {json_path}: {e}")


def query_llm(prompt):
    """Queries the Gemini LLM API with the given prompt."""
    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.5,
                # Increased token limit for potentially larger aggregated text
                "max_output_tokens": 2048 
            }
        )
        if response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            print("Warning: No valid response generated from the API.")
            return None

    except Exception as e:
        print(f"API request failed: {e}")
        return None


def generate_prompts(text):
    """Generates prompts for key insights, facts, and counterpoints from the aggregated text."""
    prompts = {
        "key_insights": (
            "Based on the combined text from multiple documents, extract 3-5 key insights. "
            "Present them as a Python list of strings without any extra text or backticks:\n\n" + text
        ),
        "did_you_know": (
            "Based on the combined text, extract 2-3 interesting 'Did You Know?' facts. "
            "Present them as a Python list of strings without any extra text or backticks:\n\n" + text
        ),
        "counterpoints": (
            "Based on the combined text, identify 2-3 potential counterpoints or opposing views. "
            "If no direct counterpoints are present, infer potential challenges to the main arguments. "
            "Present them as a Python list of strings without any extra text or backticks:\n\n" + text
        )
    }
    return prompts


def process_all_documents_in_directory(input_dir):
    """
    Processes all PDF documents in a directory to extract and aggregate insights.
    """
    try:
        # Find all files in the directory that end with .pdf
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified input directory does not exist: {input_dir}")

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}")

    print(f"Found PDF files to process: {pdf_files}")

    all_texts = []
    for pdf_file in pdf_files:
        try:
            # Extract text from the corresponding JSON file for each PDF
            text = extract_text_from_document(input_dir, pdf_file)
            if text:
                all_texts.append(text)
        except (FileNotFoundError, ValueError) as e:
            # If a single file fails, print a warning and skip it
            print(f"Warning: Skipping file {pdf_file} due to an error: {e}")
            continue

    if not all_texts:
        raise ValueError("No text could be extracted from any of the documents.")

    # Concatenate texts from all documents using a clear separator.
    # This helps the LLM understand that the content comes from different sources.
    concatenated_text = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join(all_texts)

    print("\nGenerating prompts for the aggregated text...")
    prompts = generate_prompts(concatenated_text)
    results = {}

    # Process each prompt sequentially for the combined text
    for key, prompt in prompts.items():
        print(f"Querying LLM for {key.replace('_', ' ')}...")
        results[key] = query_llm(prompt)

    return results


def main():
    """
    Main function to run the document processing pipeline.
    """
    # Directory where your PDF files (and 'temp_files' subdirectory) are located.
    input_dir = "media/PDFsUploaded/past"

    try:
        # The function now processes the entire directory.
        results = process_all_documents_in_directory(input_dir)

        print("\n--- Generated Insights from All Documents ---")
        for key, value in results.items():
            print(f"\n## {key.replace('_', ' ').title()}:\n")
            print(value or "No response from LLM for this section.")
        print("\n-------------------------------------------")

    except Exception as e:
        print(f"\nAn error occurred during processing: {e}")


if __name__ == "__main__":
    main()