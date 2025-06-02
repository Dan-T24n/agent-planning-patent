'''
Main script for async crew execution. Tested OK.
Renamed to keep the original main.py for testing.
!DO NOT RUN:$$$! Only run when all tests are done.
'''

import warnings
import os
import asyncio  # Add asyncio import for async operations
from typing import List, Dict, Any
from pathlib import Path
import json
import agentops
import time # Added for timing

from patent_crew.crew import PatentAnalysisCrew # Import the correct crew class

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

    if patent_info_list: # Check if list is not empty
      print(f"Compile patent_info_list successfully. Proceed to analyze patents.")
    
    return patent_info_list

async def run_async():
    """
    Run the Patent Analysis crew for each patent found in the specified category's JSONL file using async kickoff.
    Processes patents in batches of 10.
    """
    # Initialize AgentOps: avoid circular import issues by calling in run()
    print("## Initializing AgentOps...")
    agentops.init()
    
    print("## Starting Patent Analysis Crew (Async Batch Processing)")
    print('---------------------------------------')

    output_base_dir = Path(OUTPUT_DIR) / DEFAULT_CATEGORY 
    output_base_dir.mkdir(parents=True, exist_ok=True)

    patent_processing_inputs = get_patent_metadadata(DEFAULT_CATEGORY, KNOWLEDGE_ROOT_DIR)

    if not patent_processing_inputs:
        print("No patents found to process.")
        return

    # ---Create batches---
    total_patents = len(patent_processing_inputs)
    batch_size = 10
    print(f"Found {total_patents} patent(s) in total. Processing in batches of {batch_size}.")
    
    batches = []
    for i in range(0, total_patents, batch_size):
        batch = patent_processing_inputs[i:i+batch_size]
        batches.append(batch)
    
    print(f"Created {len(batches)} batch(es) to process.")
    for i, batch in enumerate(batches):
        print(f"  Batch {i+1}: {len(batch)} patents")
    # ---End of batching---

    # ---Running the crew for all patents in batches---
    all_results = []
    total_start_time = time.monotonic()
    
    try:
        crew_instance_manager = PatentAnalysisCrew() # choose the Crew to run
        crew = crew_instance_manager.crew() 

        for batch_idx, batch in enumerate(batches):
            batch_num_patents = len(batch)
            print(f"\n=== Processing Batch {batch_idx + 1}/{len(batches)} ({batch_num_patents} patents) ===")
            
            # Print patents in this batch
            for i, input_data in enumerate(batch):
                print(f"  Patent {i+1}: {input_data.get('publication_number', 'Unknown')}")
            
            batch_start_time = time.monotonic()
            print(f"[DEBUG main.py] Starting async crew execution for batch {batch_idx + 1}...")
            
            # Use kickoff_for_each_async for this batch
            batch_results = await crew.kickoff_for_each_async(inputs=batch)
            
            batch_end_time = time.monotonic()
            batch_duration = batch_end_time - batch_start_time
            average_duration_per_patent = batch_duration / batch_num_patents if batch_num_patents > 0 else 0
            
            print(f"--- Batch {batch_idx + 1} completed ---")
            print(f"Number of results: {len(batch_results) if batch_results else 0}")
            print(f"Batch processing time: {batch_duration:.2f} seconds")
            print(f"Average time per patent in batch: {average_duration_per_patent:.2f} seconds")
            
            # Store results from this batch
            if batch_results:
                all_results.extend(batch_results)
            
        total_end_time = time.monotonic()
        total_duration = total_end_time - total_start_time
        overall_average_duration = total_duration / total_patents if total_patents > 0 else 0
        
        print(f"\n=== All batches completed ===")
        print(f"Total patents processed: {total_patents}")
        print(f"Total processing time: {total_duration:.2f} seconds")
        print(f"Overall average time per patent: {overall_average_duration:.2f} seconds")

        # Process results correctly for async operations
        if all_results:
            print(f"\n--- Verifying output files ---")
            for i, result in enumerate(all_results):
                if i < len(patent_processing_inputs):
                    processed_input = patent_processing_inputs[i]
                    publication_number = processed_input.get('publication_number', 'Unknown')
                    # Construct expected output file path relative to the dynamic output_base_dir
                    expected_output_file = output_base_dir / f"{publication_number}_output.json"
                    if expected_output_file.exists(): # Check existence of the file in the correct output directory
                        print(f"  ✓ Confirmed output file: {expected_output_file}")
                    else:
                        print(f"  ⚠ WARNING: Output file not found at {expected_output_file}")
        else:
            print("No results returned from async execution.")

    except Exception as e:
        print(f"An error occurred during the async batch patent processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # End AgentOps session
        agentops.end_session('Success')
        print("## AgentOps session ended")

def run():
    """
    Wrapper function to run the async crew execution.
    """
    asyncio.run(run_async())


if __name__ == "__main__":
    run()

