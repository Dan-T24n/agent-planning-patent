'''
Main script for single patent crew execution.
'''

import warnings
import os
from typing import List, Dict, Any
from pathlib import Path
import json
import agentops
import time 

from dotenv import load_dotenv
load_dotenv() 

from patent_crew.crew import PatentAnalysisCrew 


# --- Global Configuration ---
DEFAULT_CATEGORY = "nlp"  # Choose category to process: {nlp, material_chemistry, computer_science}
KNOWLEDGE_ROOT_DIR = "knowledge" # This is used as the base for making json_file_path relative
OUTPUT_DIR = "output"
TARGET_PUBLICATION_NUMBER = "US-11423042-B2" # Specify the patent to process.
# ---------------------------

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def get_patent_metadadata(category: str, knowledge_root_dir: str = KNOWLEDGE_ROOT_DIR) -> List[Dict[str, Any]]:
    """
    Reads the {category}.jsonl file to get patent metadata.
    Args:
        category: The category of patents to process (e.g., 'nlp').
        knowledge_root_dir: The root directory of the knowledge base, used as a reference.

    Returns:
        A list of dictionaries, where each dictionary contains:
        - 'publication_number': The publication number of the patent.
        - 'json_file_path': Path to the JSON file, made relative to knowledge_root_dir.
        - 'pdf_file_path': Path to the PDF file, derived from json_file_path.
        - 'category': The category of the patent.
        - 'absolute_image_paths': A list of verified absolute file paths for associated images.
    """
    patent_info_list: List[Dict[str, Any]] = []
    jsonl_file_name = f"{category}.jsonl"
    base_jsonl_path = Path(knowledge_root_dir) / category / jsonl_file_name

    if not base_jsonl_path.exists():
        raise FileNotFoundError(f"JSONL index file not found at {base_jsonl_path}")

    with open(base_jsonl_path, 'r') as f_jsonl:
        for line in f_jsonl:
            patent_data = json.loads(line.strip())
            publication_number = patent_data.get('publication_number')
            json_path_str = patent_data.get('json_file_path')
            image_paths_from_jsonl = patent_data.get('image_file_paths', [])

            if publication_number and json_path_str:
                pdf_path_str = json_path_str.rsplit('.', 1)[0] + '.pdf'
                
                absolute_image_paths = [
                    p for p in image_paths_from_jsonl if os.path.isabs(p) and os.path.exists(p)
                ]
                
                image_paths_str = "\n".join(absolute_image_paths)
                patent_info_list.append({
                    'publication_number': publication_number,
                    'json_file_path': json_path_str,
                    'category': category,
                    'absolute_image_paths': absolute_image_paths,
                    'image_path_str': image_paths_str,
                    'pdf_file_path': pdf_path_str
                })

    return patent_info_list

def run():
    """
    Run the Patent Analysis crew for a specific patent.
    """
    if not TARGET_PUBLICATION_NUMBER:
        print("Error: TARGET_PUBLICATION_NUMBER is not set. Please specify a patent to process.")
        return

    agentops.init(auto_start_session=False)
    session = agentops.start_session(tags=[f"patent_{TARGET_PUBLICATION_NUMBER}"])

    output_base_dir = Path(OUTPUT_DIR) / DEFAULT_CATEGORY
    output_base_dir.mkdir(parents=True, exist_ok=True)

    all_patents = get_patent_metadadata(DEFAULT_CATEGORY, KNOWLEDGE_ROOT_DIR)
    
    patent_to_process = next((p for p in all_patents if p['publication_number'] == TARGET_PUBLICATION_NUMBER), None)

    if not patent_to_process:
        print(f"Error: Patent with publication number '{TARGET_PUBLICATION_NUMBER}' not found in category '{DEFAULT_CATEGORY}'.")
        agentops.end_session('Fail')
        return
    
    print(f"Processing patent: {TARGET_PUBLICATION_NUMBER}")
    start_time = time.monotonic()

    crew_instance_manager = PatentAnalysisCrew()
    crew = crew_instance_manager.crew()
    crew.kickoff(inputs=patent_to_process)

    duration = time.monotonic() - start_time
    print(f"Patent processing completed in {duration:.2f} seconds.")
    agentops.end_session('Success')


if __name__ == "__main__":
    run() 