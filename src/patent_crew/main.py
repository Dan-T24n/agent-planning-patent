#!/usr/bin/env python
import warnings
import os
import glob
from typing import List, Dict, Any
from pathlib import Path
import json
import agentops
import time # Added for timing

# Initialize AgentOps
agentops.init()

from tests.vision_crew_test import VisualTestCrew # Updated import

# --- Global Configuration ---
DEFAULT_CATEGORY = "nlp"  # Define the category to process here
KNOWLEDGE_ROOT_DIR = "knowledge" # This is used as the base for making json_file_path relative
OUTPUT_DIR = "output"
# ---------------------------

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def get_patent_processing_details(category: str, knowledge_root_dir: str = KNOWLEDGE_ROOT_DIR) -> List[Dict[str, Any]]:
    """
    Reads the {category}.jsonl file to get patent processing details.
    Args:
        category: The category of patents to process (e.g., 'nlp').
        knowledge_root_dir: The root directory of the knowledge base, used as a reference.

    Returns:
        A list of dictionaries, where each dictionary contains:
        - 'publication_number': The publication number of the patent.
        - 'json_file_path': Path to the JSON file, made relative to knowledge_root_dir.
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
                            'image_path_str': image_paths_str     
                        })
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON line in {base_jsonl_path}: {line.strip()}")
                    continue
    except Exception as e:
        print(f"Error: An unexpected error occurred while processing {base_jsonl_path}: {str(e)}")

    if patent_info_list: # Check if list is not empty before accessing index 0
      print(f"[DEBUG main.py] Compiled patent_info_list (first item if exists): {patent_info_list[0]}")
    
    return patent_info_list

def run():
    """
    Run the Patent Analysis crew for each patent found in the specified category's JSONL file.
    """
    print("## Starting Patent Analysis Crew")
    print('---------------------------------------')

    output_base_dir = Path(OUTPUT_DIR) / DEFAULT_CATEGORY 
    output_base_dir.mkdir(parents=True, exist_ok=True)

    patent_processing_inputs = get_patent_processing_details(DEFAULT_CATEGORY, KNOWLEDGE_ROOT_DIR)

    if not patent_processing_inputs:
        print("No patents found to process.")
        return

    # ---Testing with one patent---
    print(f"[DEBUG main.py] Total patents found: {len(patent_processing_inputs)}") 
    print(f"Found {len(patent_processing_inputs)} patent(s) in total. Processing only the first one for this run.")
    patent_processing_inputs = [patent_processing_inputs[0]]
    print(f"[DEBUG main.py] Processing input for the first patent: {patent_processing_inputs[0]}")
    # ---End of testing with one patent---

    num_patents = len(patent_processing_inputs)
    print(f"Processing {num_patents} patent(s) (selected for this run).")

    # ---Running the crew for all patents---
    try:
        crew_instance_manager = VisualTestCrew() 
        crew = crew_instance_manager.crew() 

        print(f"Kicking off crew for {num_patents} inputs...")
        
        start_time = time.monotonic()
        print(f"[DEBUG main.py] Starting crew execution with inputs: {patent_processing_inputs}")
        results = crew.kickoff_for_each(inputs=patent_processing_inputs)
        end_time = time.monotonic() 

        total_duration = end_time - start_time
        average_duration_per_patent = total_duration / num_patents if num_patents > 0 else 0
        
        print("\\n--- Crew execution finished for all patents ---")
        print(f"Number of results: {len(results)}")
        print(f"Total processing time: {total_duration:.2f} seconds")
        if num_patents > 0:
            print(f"Average time per patent: {average_duration_per_patent:.2f} seconds")

        for i, result in enumerate(results):
            processed_input = patent_processing_inputs[i]
            publication_number = processed_input.get('publication_number', 'Unknown')
            print(f"\\nResult for patent: {publication_number}")
            print(f"  Raw output snippet: {result.raw[:200]}...")
            # Construct expected output file path relative to the dynamic output_base_dir
            expected_output_file = output_base_dir / f"{publication_number}_output.json"
            if expected_output_file.exists(): # Check existence of the file in the correct output directory
                print(f"  Confirmed output file: {expected_output_file}")
            else:
                print(f"  WARNING: Output file not found at {expected_output_file}")

    except Exception as e:
        print(f"An error occurred during the batch patent processing: {e}")
        import traceback
        traceback.print_exc()

