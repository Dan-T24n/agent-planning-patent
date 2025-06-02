'''
Main script for single patent crew execution. Tested OK.
'''

import warnings
import os
from typing import List, Dict, Any
from pathlib import Path
import json
import agentops
import time # Added for timing

from dotenv import load_dotenv
load_dotenv() 

# from tests.vision_crew_test import VisualTestCrew # Import the crew for testing
from crew import PatentAnalysisCrew # Import the crew for analysis


# --- Global Configuration ---
DEFAULT_CATEGORY = "nlp"  # Choose category to process: {nlp, material_chemistry, computer_science}
KNOWLEDGE_ROOT_DIR = "knowledge" # This is used as the base for making json_file_path relative
OUTPUT_DIR = "output"
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
    # Construct the path to the JSONL file relative to the current execution, 
    base_jsonl_path = Path(knowledge_root_dir) / category / jsonl_file_name

    if not base_jsonl_path.exists():
        print(f"Error: JSONL index file not found at {base_jsonl_path}")
        return patent_info_list
    
    # Reading patent metadata from: {base_jsonl_path}
    try:
        with open(base_jsonl_path, 'r') as f_jsonl:
            for line in f_jsonl:
                try:
                    patent_data = json.loads(line.strip())
                    publication_number = patent_data.get('publication_number')
                    # Expecting absolute path from JSONL for json_file_path
                    json_path_str = patent_data.get('json_file_path') 
                    # Expecting list of absolute paths from JSONL for image_file_paths
                    image_paths_from_jsonl = patent_data.get('image_file_paths', [])
                    
                    # Check if publication_number and json_path_str are present
                    if publication_number and json_path_str:
                        print(f"[DEBUG main.py] Found publication_number: {publication_number}")
                        # Assuming the PDF file has the same name but .pdf extension
                        pdf_path_str = json_path_str.rsplit('.', 1)[0] + '.pdf'
                        #verify each image_path_from_jsonl is an absolute path and valid
                        for image_path in image_paths_from_jsonl:
                            if not os.path.isabs(image_path):
                                print(f"[DEBUG main.py] Warning: Image path is not absolute: {image_path}")
                                continue
                            if not os.path.exists(image_path):
                                print(f"[DEBUG main.py] Warning: Image path does not exist: {image_path}")
                                continue
                        print(f"[DEBUG main.py] Found {len(image_paths_from_jsonl)} absolute image paths.")
                        
                        # turn image_paths_from_jsonl into a string with newlines between each path
                        image_paths_str = "\n".join(image_paths_from_jsonl)
                        patent_info_list.append({
                            'publication_number': publication_number,
                            'json_file_path': json_path_str, 
                            'category': category,
                            'absolute_image_paths': image_paths_from_jsonl,
                            'image_path_str': image_paths_str,
                            'pdf_file_path': pdf_path_str     
                        })
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON line in {base_jsonl_path}: {line.strip()}")
                    continue
    except Exception as e:
        print(f"Error: An unexpected error occurred while processing {base_jsonl_path}: {str(e)}")

    if patent_info_list: # Check if list is not empty before accessing index 0
      print(f"Compile patent_info_list successfully. Proceed to analyze patents.")
    
    return patent_info_list

def run():
    """
    Run the Patent Analysis crew for the first patent found in the specified category's JSONL file using simple kickoff.
    Processes only one single patent.
    """
    # Initialize AgentOps: avoid circular import issues by calling in run()
    print("## Initializing AgentOps...")
    agentops.init()
    
    print("## Starting Patent Analysis Crew (Single Patent Processing)")
    print('---------------------------------------')

    output_base_dir = Path(OUTPUT_DIR) / DEFAULT_CATEGORY 
    output_base_dir.mkdir(parents=True, exist_ok=True)

    patent_processing_inputs = get_patent_metadadata(DEFAULT_CATEGORY, KNOWLEDGE_ROOT_DIR)

    if not patent_processing_inputs:
        print("No patents found to process.")
        return

    # ---Process only the first patent---
    single_patent_input = patent_processing_inputs[0]
    publication_number = single_patent_input.get('publication_number', 'Unknown')
    # ---End single patent selection---

    # ---Running the crew for single patent---
    start_time = time.monotonic()
    
    try:
        crew_instance_manager = PatentAnalysisCrew() # choose the Crew to run
        crew = crew_instance_manager.crew() 

        print(f"Starting crew execution for patent: {publication_number}")
        
        # Use simple kickoff for single patent
        result = crew.kickoff(inputs=single_patent_input)
        
        end_time = time.monotonic()
        duration = end_time - start_time
        
        print(f"--- Patent processing completed ---")
        print(f"Patent: {publication_number}")
        print(f"Processing time: {duration:.2f} seconds")
        
        # Process result correctly for single patent operation
        if result:
            print(f"\n--- Verifying output file ---")
            # Construct expected output file path relative to the dynamic output_base_dir
            expected_output_file = output_base_dir / f"{publication_number}_output.json"
            if expected_output_file.exists(): # Check existence of the file in the correct output directory
                print(f"  ✓ Confirmed output file: {expected_output_file}")
            else:
                print(f"  ⚠ WARNING: Output file not found at {expected_output_file}")
        else:
            print("No result returned from crew execution.")

    except Exception as e:
        print(f"An error occurred during the single patent processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # End AgentOps session
        agentops.end_session('Success')
        print("## AgentOps session ended")


if __name__ == "__main__":
    run() 