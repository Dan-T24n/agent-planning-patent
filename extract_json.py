import json
import os

# --- Configuration Section ---
# TODO: Update these values before running the script.

# Path to the input JSONL file (e.g., "data/nlp/nlp.jsonl")
INPUT_FILE_PATH = "data/nlp/nlp.jsonl"

# Publication number of the patent to extract (e.g., "US-2020073983-A1")
PUBLICATION_NUMBER_TO_FIND = "US-2020073983-A1"

# Base directory for output. The script will create a subdirectory named after the
# PUBLICATION_NUMBER_TO_FIND within this base directory.
# (e.g., "data/nlp/pdf_and_image/")
OUTPUT_DIRECTORY_BASE = "data/nlp/pdf_and_image/"
# --- End Configuration Section ---

def extract_and_save_patent_data(input_file_path, publication_number_to_find, output_directory_base):
    """
    Searches for a patent by its publication number in a JSONL file,
    extracts its data, and saves it to a new JSON file in a specified directory.

    Args:
        input_file_path (str): The path to the input JSONL file.
        publication_number_to_find (str): The publication number of the patent to find.
        output_directory_base (str): The base directory where the output subdirectory
                                     and file will be created.
    """
    found_patent_data = None
    absolute_input_file_path = os.path.abspath(input_file_path)
    absolute_output_directory_base = os.path.abspath(output_directory_base)

    try:
        with open(absolute_input_file_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                try:
                    patent_data = json.loads(line.strip())
                    if patent_data.get("publication_number") == publication_number_to_find:
                        found_patent_data = patent_data
                        break
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line in {absolute_input_file_path}: {line.strip()}")
                    continue

        if found_patent_data:
            specific_output_directory = os.path.join(absolute_output_directory_base, publication_number_to_find)
            os.makedirs(specific_output_directory, exist_ok=True)

            output_file_path = os.path.join(specific_output_directory, f"{publication_number_to_find}.json")

            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                json.dump(found_patent_data, f_out, indent=4)
            print(f"Successfully extracted and saved data for {publication_number_to_find} to {output_file_path}")
        else:
            print(f"Patent with publication number {publication_number_to_find} not found in {absolute_input_file_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {absolute_input_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ensure the configuration values are set
    if not INPUT_FILE_PATH or not PUBLICATION_NUMBER_TO_FIND or not OUTPUT_DIRECTORY_BASE:
        print("Error: Please update the configuration variables (INPUT_FILE_PATH, PUBLICATION_NUMBER_TO_FIND, OUTPUT_DIRECTORY_BASE) at the top of the script.")
    else:
        # Call the function to extract and save patent data
        extract_and_save_patent_data(INPUT_FILE_PATH, PUBLICATION_NUMBER_TO_FIND, OUTPUT_DIRECTORY_BASE)
