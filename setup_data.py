'''
# Goal
This utility script is used to extract the patent data from the JSONL file from data/nlp/nlp.jsonl,
and save it to a new JSON file in a specified directory for each patent in knowledge/nlp/pdf_and_image/{publication_number}.

The goal is to mirror the data/nlp/pdf_and_image/ directory structure in knowledge/nlp/pdf_and_image/ directory.
Within each patent {publication_number}/ directory, there should be a json file extracted from data/nlp/nlp.jsonl.


# Directory structure:
├── data/                                     # Contains datasets and extracted patent information.
│   ├── computer_science/                     # Data specific to computer science patents.
│   ├── material_chemistry/                   # Data specific to material chemistry patents.
│   └── nlp/                                  # Data specific to NLP patents.
│       ├── nlp.jsonl
│       └── pdf_and_image/                    # Stores PDF and image files for NLP patents.
├── knowledge/                                # Knowledge base for agents, mirroring data/
│   ├── computer_science/                     
│   ├── material_chemistry/                   
│   └── nlp/                                  # Data specific to NLP patents.
│       └── pdf_and_image/                    # Stores PDF and image files for NLP patents.
│           └── US-2020073983-A1/             # Example patent data (with pdf, json, and images)

# Outcomes

1. Mirror the data/nlp/pdf_and_image/ directory structure in knowledge/nlp/pdf_and_image/ directory. Files to copy:
- pdf file: {publication_number}.pdf
- image files: numbering images, e.g. 1.png, 2.png, etc.

2. Read the JSONL file from data/nlp/nlp.jsonl -> extract the patent data for the given publication number:
- save it to the new JSON file in the knowledge/nlp/pdf_and_image/{publication_number}/ directory.
- json file: {publication_number}.json

3. For each category, create a new JSONL file: knowledge/{category}/{category}.jsonl
- each entry is a dictionary that tracks available files for each patent:
  - publication_number: the publication number of the patent
  - json_file_path: the path to the json file
  - pdf_file_path: the path to the pdf file
  - image_file_paths: list of image file paths [path_to_{1.png}, path_to_{2.png}, etc.]

4. At the end, we have the final knowledge base structure:
- knowledge/{category}/pdf_and_image/{publication_number}/ with the following files:
  - {publication_number}.json
  - {publication_number}.pdf
  - {1.png}, {2.png}, etc.

# Run
uv run setup_data.py
'''

import json
import os
import shutil
from pathlib import Path

# --- Configuration ---

#change one category at a time {nlp, computer_science, material_chemistry}
CATEGORY = "nlp" # reload the crew config to get specialized agents

# Path to the input JSONL file
INPUT_FILE_PATH = Path(f"data/{CATEGORY}/{CATEGORY}.jsonl")
# Directory containing the source patent artifacts (subdirectories named by publication number)
SOURCE_PATENT_ARTIFACTS_DIR = Path(f"data/{CATEGORY}/pdf_and_image/")
# Base directory for the knowledge base output.
KNOWLEDGE_BASE_OUTPUT_DIR = Path(f"knowledge/{CATEGORY}/pdf_and_image/")
# --- End Configuration ---

def load_all_patent_data_from_jsonl(jsonl_file_path: Path) -> dict:
    """
    Reads a JSONL file and loads all patent data into a dictionary.

    Args:
        jsonl_file_path (Path): The path to the input JSONL file.

    Returns:
        dict: A dictionary where keys are publication numbers and values are
              the corresponding patent data objects. Returns an empty dict
              if the file is not found or in case of other errors.
    """
    patent_data_map = {}
    absolute_jsonl_file_path = jsonl_file_path.resolve()

    if not absolute_jsonl_file_path.is_file():
        print(f"Error: Input JSONL file not found at {absolute_jsonl_file_path}")

    try:
        with open(absolute_jsonl_file_path, 'r', encoding='utf-8') as f_in:
            for line_number, line in enumerate(f_in, 1):
                try:
                    patent_data = json.loads(line.strip())
                    publication_number = patent_data.get("publication_number")
                    if publication_number:
                        patent_data_map[publication_number] = patent_data
                    else:
                        print(f"Warning: Missing 'publication_number' in line {line_number} of {absolute_jsonl_file_path}")
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line {line_number} in {absolute_jsonl_file_path}: {line.strip()}")
                    continue
    except Exception as e:
        print(f"An error occurred while reading {absolute_jsonl_file_path}: {e}")
    
    return patent_data_map

def synchronize_patent_knowledge_base(jsonl_data_path: Path, source_artifacts_path: Path, knowledge_base_path: Path) -> None:
    """
    Mirrors specified patent artifacts (PDFs, numbered images) and extracts/saves 
    patent-specific data from a JSONL file to the knowledge base.
    Also creates a category-level JSONL summary of available artifacts.

    Args:
        jsonl_data_path (Path): Path to the JSONL file containing patent data.
        source_artifacts_path (Path): Path to the directory containing source patent artifacts.
        knowledge_base_path (Path): Path to the base directory for the knowledge base output.
    """
    all_patent_data = load_all_patent_data_from_jsonl(jsonl_data_path)

    if not all_patent_data:
        print("No patent data loaded from JSONL file. Exiting synchronization.")
        return

    absolute_source_artifacts_path = source_artifacts_path.resolve()
    absolute_knowledge_base_path = knowledge_base_path.resolve()

    try:
        absolute_knowledge_base_path.mkdir(parents=True, exist_ok=True)
        print(f"Knowledge base directory ensured at: {absolute_knowledge_base_path}")
    except Exception as e:
        print(f"Error creating knowledge base directory {absolute_knowledge_base_path}: {e}")
        return

    if not absolute_source_artifacts_path.is_dir():
        print(f"Error: Source artifacts directory not found at {absolute_source_artifacts_path}")
        return

    print(f"Starting synchronization for category '{CATEGORY}' from {absolute_source_artifacts_path} to {absolute_knowledge_base_path}")

    processed_publication_numbers = [] 

    for item in absolute_source_artifacts_path.iterdir():
        if item.is_dir():
            publication_number = item.name
            source_patent_subdir = item
            target_patent_subdir = absolute_knowledge_base_path / publication_number
            files_copied_count = 0

            try:
                target_patent_subdir.mkdir(parents=True, exist_ok=True)

                for file_item in source_patent_subdir.iterdir():
                    if file_item.name == f"{publication_number}.pdf":
                        shutil.copy2(file_item, target_patent_subdir / file_item.name)
                        files_copied_count += 1
                    elif file_item.suffix.lower() == '.png' and file_item.stem.isdigit():
                        shutil.copy2(file_item, target_patent_subdir / file_item.name)
                        files_copied_count += 1
                
                if files_copied_count > 0:
                    print(f"Copied {files_copied_count} artifact(s) for {publication_number}")

            except Exception as e:
                print(f"Error copying artifacts for {publication_number}: {e}")
                continue 

            # Extract and Save Patent-Specific JSON
            patent_specific_data = all_patent_data.get(publication_number)

            if patent_specific_data:
                output_json_path = target_patent_subdir / f"{publication_number}.json"
                try:
                    with open(output_json_path, 'w', encoding='utf-8') as f_out:
                        json.dump(patent_specific_data, f_out, indent=4)
                    # print(f"Saved JSON for {publication_number} to {output_json_path}") # Kept for debugging if needed
                    processed_publication_numbers.append(publication_number) 
                except Exception as e:
                    print(f"Error saving JSON for {publication_number} to {output_json_path}: {e}")
            else:
                print(f"Warning: Patent data for {publication_number} not found in {jsonl_data_path.name}. JSON file not created.")
    
    # Create knowledge/{CATEGORY}/{CATEGORY}.jsonl
    if processed_publication_numbers:
        category_knowledge_entries = []
        for pub_num in processed_publication_numbers:
            current_patent_knowledge_dir = absolute_knowledge_base_path / pub_num
            
            json_file_path = (current_patent_knowledge_dir / f"{pub_num}.json").resolve()
            pdf_file_path = (current_patent_knowledge_dir / f"{pub_num}.pdf").resolve()
            
            image_file_paths_list = []
            if current_patent_knowledge_dir.is_dir(): 
                for file_item in current_patent_knowledge_dir.iterdir():
                    if file_item.suffix.lower() == '.png' and file_item.stem.isdigit():
                        image_file_paths_list.append(file_item.resolve())
            
            patent_entry = {
                "publication_number": pub_num,
                "json_file_path": str(json_file_path) if json_file_path.exists() else None,
                "pdf_file_path": str(pdf_file_path) if pdf_file_path.exists() else None,
                "image_file_paths": sorted([str(img_p) for img_p in image_file_paths_list]) 
            }
            category_knowledge_entries.append(patent_entry)

        category_jsonl_output_path = absolute_knowledge_base_path.parent / f"{CATEGORY}.jsonl"
        try:
            with open(category_jsonl_output_path, 'w', encoding='utf-8') as f_out_jsonl:
                for entry in category_knowledge_entries:
                    f_out_jsonl.write(json.dumps(entry) + '\n')
            print(f"Successfully created category knowledge summary: {category_jsonl_output_path}")
        except Exception as e:
            print(f"Error creating category knowledge summary {category_jsonl_output_path}: {e}")
    else:
        print(f"No patents were successfully processed for category {CATEGORY}. Skipping creation of {CATEGORY}.jsonl.")

    print(f"Synchronization process completed for category '{CATEGORY}'.")

if __name__ == "__main__":
    # Ensure the configuration Path objects are correctly defined at the top of the script.
    if not (INPUT_FILE_PATH and SOURCE_PATENT_ARTIFACTS_DIR and KNOWLEDGE_BASE_OUTPUT_DIR):
        print("Error: Configuration paths (INPUT_FILE_PATH, SOURCE_PATENT_ARTIFACTS_DIR, KNOWLEDGE_BASE_OUTPUT_DIR) must be set.")
    else:
        # Call the function to synchronize the patent knowledge base
        synchronize_patent_knowledge_base(INPUT_FILE_PATH, SOURCE_PATENT_ARTIFACTS_DIR, KNOWLEDGE_BASE_OUTPUT_DIR)
