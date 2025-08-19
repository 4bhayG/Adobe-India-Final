import os
import json
from pathlib import Path
import ast
import re
from typing import List
from operator import itemgetter
import logging

# Third-party library imports
import fitz  # PyMuPDF
from dotenv import load_dotenv
import pandas as pd

from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
# from vertexai.generative_models import GenerativeModel, GenerationConfig

load_dotenv()

# --- Gemini API Configuration ---
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
model_name = os.getenv("GEMINI_MODEL")

client = genai.Client()
# --- PDF Parsing and Text Extraction Functions ---

def pdf_to_dict(path):
    """
    Main function to process a PDF file and extract its title, potential headings,
    and full text content.
    """
    doc = fitz.open(path)
    font_counts, styles = fonts(doc, granularity=True)
    size_tag = font_tags(font_counts, styles)
    elements, list_of_text = headers_para(doc, size_tag)

    final = []
    for ele in elements:
        text = ele['text']
        # Heuristics to identify potential headings
        if (3 < len(text) < 90 and not re.match(r'[a-z].', text) and re.search(r'[^\d\s]', text) and
            re.match(r'.*[^.,;({\[]\s*$', text)):
            final.append(ele)

    title = find_primary_heading(final)
    title_text = title['text'] if title else ""
    return title_text, final, list_of_text

def relative_borderdistance(list_of_bboxes, x_page, y_page, whole_page=True):
    """Sorts text blocks by their position on the page (y then x)."""
    list_of_bboxlists = []
    for entry_count, box in enumerate(list_of_bboxes):
        x_left, y_top, x_right, y_bottom = box
        entry = [round(y_top / y_page, 3), round(x_left / x_page, 3), round(y_bottom / y_page, 3), round(x_right / x_page, 3), entry_count, y_top, x_left]
        list_of_bboxlists.append(entry)

    column_names = ['y_top_rel', 'x_left_rel', 'y_bottom_rel', 'x_right_rel', 'entry_count', 'y_sort', 'x_sort']
    df_bboxes_sorted = pd.DataFrame(list_of_bboxlists, columns=column_names).sort_values(by=['y_sort', 'x_sort'])
    return df_bboxes_sorted['entry_count'].to_list()

def fonts(doc, granularity):
    """Extracts font styles and counts their usage."""
    styles = {}
    font_counts = {}
    for page in doc:
        blocks = page.get_text("dict", flags=11)["blocks"]
        for b in blocks:
            if b['type'] == 0:  # Text block
                for l in b["lines"]:
                    for s in l["spans"]:
                        identifier = f"{s['size']}{s['flags']}{s['font']}_{s['color']}"
                        styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'], 'color': s['color']}
                        font_counts[identifier] = font_counts.get(identifier, 0) + 1
    
    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)
    if not font_counts:
        raise ValueError("Zero discriminating fonts found!")
    return font_counts, styles

def font_tags(font_counts, styles):
    """Creates tags (e.g., <p>, <h1>) based on font size relative to the most common font."""
    if not font_counts: return {}
    p_style_id = font_counts[0][0]
    sort_on_size = dict(sorted(styles.items(), key=lambda x: x[1]['size']))
    
    try:
        index_of_p = list(sort_on_size.keys()).index(p_style_id)
    except ValueError:
        index_of_p = 0
        p_style_id = list(sort_on_size.keys())[0] if sort_on_size else None
    
    if not p_style_id: return {}
    
    app_tag = {p_style_id: "<p>"}
    for i, style_id in enumerate(list(sort_on_size.keys())[:index_of_p]):
        app_tag[style_id] = f"<s{index_of_p - i}>"
    for i, style_id in enumerate(list(sort_on_size.keys())[index_of_p + 1:]):
        app_tag[style_id] = f"<h{i + 1}>"
    return app_tag

def headers_para(doc, size_tag):
    """Extracts and merges text elements, filtering out headers/footers."""
    header_para, text_list = [], []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=11)["blocks"]
        text_blocks = [b for b in blocks if b['type'] == 0]
        if not text_blocks: continue

        bboxes_ordered = relative_borderdistance([b['bbox'] for b in text_blocks], page.rect.width, page.rect.height)
        
        page_text = ""
        for b_index in bboxes_ordered:
            block = text_blocks[b_index]
            for line in block["lines"]:
                for span in line["spans"]:
                    font_label = f"{span['size']}{span['flags']}{span['font']}_{span['color']}"
                    if span['text'].strip():
                        header_para.append({
                            'tag': size_tag.get(font_label, "<p>"), 'text': span['text'], 'page_num': page_num,
                            'p_position_y': span['origin'][1], 'bbox': span['bbox'], 'font_size': span['size']
                        })
                        page_text += span['text'] + " "
        text_list.append(page_text.strip())

    merged_elements = []
    i = 0
    while i < len(header_para):
        current_elem = header_para[i]
        # Filter out headers (top 5%) and footers (bottom 10%)
        if current_elem['p_position_y'] < (page.rect.height * 0.05) or current_elem['p_position_y'] > (page.rect.height * 0.9):
            i += 1
            continue
        merged_elements.append(current_elem)
        i += 1
    return merged_elements, text_list

def find_primary_heading(block_strings):
    """Heuristically finds the main title of the document."""
    if not block_strings: return None
    page_0_blocks = sorted([b for b in block_strings if b['page_num'] == 0], key=lambda x: x.get('font_size', 0), reverse=True)
    return page_0_blocks[0] if page_0_blocks else None

def create_output_json(pdf_path, output_dir):
    """Creates a structured JSON file from a PDF's content."""
    title, heading_blocks, list_of_text = pdf_to_dict(pdf_path)
    outline = []
    for block in heading_blocks:
        text = block['text'].strip()
        if text:
            outline.append({
                "text": text, "page": block['page_num'], 'top_x': block['bbox'][0],
                'top_y': block['bbox'][1], 'bot_x': block['bbox'][2], 'bot_y': block['bbox'][3]
            })
    output_data = {"title": title, "outline": outline, 'full_text': list_of_text}
    output_filepath = Path(output_dir) / f"{Path(pdf_path).stem}.json"
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    return output_filepath

def call_gemini_api(system_prompt, user_prompt):
    """
    Calls the Gemini API and robustly parses the list from the response,
    even if it's inside a markdown block.
    """
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    try:
        response = client.models.generate_content(
            model= model_name,
            contents=full_prompt,
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget = 0)
            )
        )
        raw_text = response.text

        # Use regex to find the first string that looks like a Python list '[...]'
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)

        if match:
            # If a match is found, extract it
            list_string = match.group(0)
            # Safely evaluate the string into a Python list
            return ast.literal_eval(list_string)
        else:
            # If no list is found in the response, log it and return empty
            logging.warning(f"Could not find a list in Gemini response. Raw response:\n{raw_text}")
            return []

    except Exception as e:
        # Catch any other errors during parsing or API call
        logging.error(f"Error parsing Gemini response: {e}\nRaw response:\n{response.text if 'response' in locals() else 'No response object'}")
        return []

def load_files(json_folder):
    """Loads heading data from the intermediate JSON files."""
    json_files = {f.stem: f for f in Path(json_folder).glob("*.json")}
    data = []
    for name, json_path in json_files.items():
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                outline_text = [item['text'] for item in json_data.get('outline', [])]
                data.append(outline_text)
        except Exception as e:
            logging.error(f"Error processing {name}: {e}")
    print(f"Loaded heading data for {len(data)} documents.")
    return data

def extract_keywords_and_info(text):
    """Extract keywords and important info from text using Gemini API."""
    prompt = f'Extract the most important keywords and key information from this text. Return only a single line of comma-separated values.\nText: "{text}"'
    try:
        # generation_config = GenerationConfig(thinking_budget=0, temperature=0.2)
        response = client.models.generate_content(
            model= model_name,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                thinking_config=ThinkingConfig(thinking_budget = 0)
            )
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return ""

def process_headings(data, keywords):
    """Filters headings from multiple documents using the Gemini API."""
    ordered_headings = []
    system_prompt = "You are a precise filtering assistant. Given keywords and a list of document headings, return only the headings that are highly relevant to the keywords. Select a maximum of 3 headings. Output must be a Python list of strings with only the original headings."
    for doc_headings in data:
        if not doc_headings: continue
        user_prompt = f"Keywords: {keywords}\n\nList of headings: {str(doc_headings)}"
        result = call_gemini_api(system_prompt, user_prompt)
        if result:
            ordered_headings.extend(result)
    return ordered_headings

def extract_relevant_info(heading, document_page):
    """Summarizes a page section related to a specific heading using the Gemini API."""
    prompt = f'Summarize information related to the heading "{heading}" from the following text in 2-3 concise sentences.\n\nDocument Text:\n{document_page}'
    try:
        response = client.models.generate_content(
            model= model_name,
            contents=prompt,
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget = 0)
            )
        )  
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error during summarization for heading '{heading}': {e}")
        return f"Could not summarize: {heading}"

def extract_relevant_info_for_all(final_sorted_list, json_folder, input_dir, curr_dir):
    """Gathers summaries, page numbers, and paths for the final list of headings using robust pathlib."""
    heading_set = set(final_sorted_list)
    json_folder_path, input_dir_path, curr_dir_path = Path(json_folder), Path(input_dir), Path(curr_dir)
    json_files = {f.stem: f for f in json_folder_path.glob("*.json")}
    summaries, page_numbers, doc_names, location, doc_paths = {}, {}, {}, {}, {}

    for name, json_path in json_files.items():
        pdf_filename = json_path.with_suffix('.pdf').name
        pdf_path_in_past = input_dir_path / pdf_filename
        pdf_path_in_current = curr_dir_path / pdf_filename

        source_pdf_path = None
        if pdf_path_in_past.exists():
            source_pdf_path = str(pdf_path_in_past)
        elif pdf_path_in_current.exists():
            source_pdf_path = str(pdf_path_in_current)
        else:
            logging.warning(f"PDF file not found for {json_path.name}. Looked in {pdf_path_in_past} and {pdf_path_in_current}")
            continue

        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data.get('outline', []):
                curr_heading = item['text'].strip()
                if curr_heading in heading_set:
                    doc_names[curr_heading] = os.path.basename(source_pdf_path)
                    doc_paths[curr_heading] = source_pdf_path
                    page_number = item['page']
                    page_numbers[curr_heading] = page_number
                    location[curr_heading] = [item['top_x'], item['top_y'], item['bot_x'], item['bot_y']]
                    
                    full_text = data.get('full_text', [])
                    if 0 <= page_number < len(full_text):
                        summaries[curr_heading] = extract_relevant_info(curr_heading, full_text[page_number])
                    else:
                        summaries[curr_heading] = ""
    return summaries, page_numbers, doc_names, location, doc_paths

def create_travel_plan_json(final_sorted_list, summary, page_numbers, doc_names, locat, doc_paths):
    """Creates the final JSON output object."""
    extracted_sections = []
    for i, item in enumerate(final_sorted_list):
        if item in doc_names:
            extracted_sections.append({
                "document": doc_names[item], "local_path": doc_paths.get(item, "Path not found"),
                "section_title": item, "importance_rank": i + 1, "page_number": page_numbers.get(item, -1),
                "refined_text": summary.get(item, ""), "location": locat.get(item, [])
            })
    return {"extracted_sections": extracted_sections}

def main_functionality(json_folder, text, input_dir, curr_dir):
    """Main function to process folders and generate ranked headings using Gemini API."""
    print("\n1: Turning text into keywords...")
    keywords = extract_keywords_and_info(text)
    if not keywords:
        print("Could not extract keywords from text. Halting.")
        return None

    data = load_files(json_folder)
    if not data:
        print("No source documents found to process!")
        return None

    print("\n2: Filtering relevant headings from each document...")
    ranked_headings = process_headings(data, keywords)
    if not ranked_headings:
        print("No relevant headings were found after initial filtering.")
        return None

    system_prompt = "You are a precise sorting assistant. Given keywords and a list of pre-filtered headings, sort the list in descending order of importance based on the keywords. Select a maximum of 4 headings. Output must be a Python list of strings containing only the original headings."
    user_prompt = f"Keywords: {keywords}\n\nList of headings: {str(ranked_headings)}"
    print("\n3: Ranking the combined list of relevant headings...")
    final_sorted_list = call_gemini_api(system_prompt, user_prompt)

    if not final_sorted_list:
        print("No headings remained after the final ranking.")
        return None
    print(f"Final sorted list of headings: {final_sorted_list}")

    print("\n4: Summarizing content for final headings...")
    summaries, page_numbers, doc_names, locat, doc_paths = extract_relevant_info_for_all(final_sorted_list, json_folder, input_dir, curr_dir)
    
    return create_travel_plan_json(final_sorted_list, summaries, page_numbers, doc_names, locat, doc_paths)




def main():
    input_dir = "media\PDFsUploaded\past"
    curr_dir = "media\PDFsUploaded\current"
    OUTPUT_FILE = os.path.join(input_dir, "output.json") 
    JSON_FOLDER = os.path.join(input_dir, "temp_files") 
    text = ""

    # --- Directory Creation ---
    os.makedirs(JSON_FOLDER, exist_ok=True)
    # os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(curr_dir, exist_ok=True)


    # Run the main analysis workflow
    print(main_functionality(JSON_FOLDER, text, OUTPUT_FILE, input_dir, curr_dir))
    
if __name__ == "__main__":
    main()