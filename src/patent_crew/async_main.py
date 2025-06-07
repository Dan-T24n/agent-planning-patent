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

from dotenv import load_dotenv
load_dotenv() 

from patent_crew.crew import PatentAnalysisCrew # Import the original crew class

# --- Global Configuration ---
DEFAULT_CATEGORY = "computer_science"  # Choose category to process: {nlp, material_chemistry, computer_science}
KNOWLEDGE_ROOT_DIR = "knowledge" # This is used as the base for making json_file_path relative
OUTPUT_DIR = "output"
MAX_BATCHES_TO_PROCESS = 2 # Set to 1 to process only first batch of 10 patents
BATCH_SIZE = 5  # Number of patents to process in each batch
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

async def process_batch(crew, batch: List[Dict[str, Any]]) -> List[Any]:
    """
    Process a batch of patents with the crew.
    """
    return await crew.kickoff_for_each_async(inputs=batch)

async def run_async():
    """
    Run the Patent Analysis crew for each patent found in the specified category's JSONL file using async kickoff.
    """
    
    agentops.init(auto_start_session=False)

    output_base_dir = Path(OUTPUT_DIR) / DEFAULT_CATEGORY
    output_base_dir.mkdir(parents=True, exist_ok=True)

    patent_processing_inputs = get_patent_metadadata(DEFAULT_CATEGORY, KNOWLEDGE_ROOT_DIR)

    if not patent_processing_inputs:
        return

    batches = []
    for i in range(0, len(patent_processing_inputs), BATCH_SIZE):
        batch = patent_processing_inputs[i:i+BATCH_SIZE]
        batches.append(batch)
    
    crew_instance_manager = PatentAnalysisCrew()
    crew = crew_instance_manager.crew() 

    for batch_idx, batch in enumerate(batches):
        if batch_idx >= MAX_BATCHES_TO_PROCESS:
            break
        
        print(f" ********** Processing Batch {batch_idx + 1} **********")
        
        # Create batch-specific output directory
        batch_output_dir = output_base_dir / str(batch_idx)
        batch_output_dir.mkdir(parents=True, exist_ok=True)
        
        session = agentops.start_session(tags=[f"batch_{batch_idx}"])

        try:
            # Add batch_idx to each input for dynamic file path generation
            inputs_with_batch_idx = [{**patent_input, 'batch_idx': batch_idx} for patent_input in batch]
            await process_batch(crew, inputs_with_batch_idx)
            
            # Finished 1 batch: sleep and end session
            print(f"Batch {batch_idx + 1} success. Sleeping for 30 seconds...")
            await asyncio.sleep(30)
            agentops.end_session('Success')
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error processing batch {batch_idx + 1}: {e}")
            agentops.end_session('Fail')
            print("Continuing to next batch after 30 seconds...")
            await asyncio.sleep(30)

def run():
    """
    Wrapper function to run the async crew execution.
    """
    asyncio.run(run_async())


if __name__ == "__main__":
    run()

