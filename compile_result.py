'''
# Goal
This utility script is used to compile individual patent-product json into a jsonl file.
For a specific category, e.g. "nlp", we have results in output/nlp/{batch_idx}/{publication_number}_output_short.json.

The goal is to compile all the individual patent-product json into a jsonl file for each category,
the jsonl file should be at: output/{category}/{category}_output.jsonl.

Each input json "output/nlp/{batch_idx}/{publication_number}_output_short.json" is a valid json/dictionary,
with the following structure:
{
    "publication_number": "{publication_number}",
    "title": "60-100 character product title",
    "product_description": "200-300 character description with target users, needs, and benefits", 
    "implementation": "200-300 character technical implementation approach",
    "differentiation": "200-300 character unique competitive advantages"
}

When compiling, we need to ensure that:
- each entry is a valid json/dictionary with the above structure.
- within each json entry, make sure the length of each field does not exceed the character limit.


# Directory structure:
├── ouput/                                    # Contains datasets and extracted patent information.
│   ├── computer_science/                     # Data specific to computer science patents.
│   ├── material_chemistry/                   # Data specific to material chemistry patents.
│   └── nlp/                                  # Data specific to NLP patents.
│       └── nlp_output.jsonl                  # Compiled jsonl file for NLP patent-products.
│       └── 0/                                # Batch 0
│           └── US-2020073983-A1_output_short.json  # Output for patent US-2020073983-A1
│           └── ...                           # Output for other patents
│       └── 1/                                # Batch 1
│           └── US-2020073983-A1_output_short.json  # Output for patent US-2020073983-A1
│           └── ...                           # Output for other patents




# Outcomes

A jsonl file is created at: output/{category}/{category}_output.jsonl.

Each entry in the jsonl file is a valid json/dictionary with the following structure:
{
    "publication_number": "US-2020073983-A1",
    "title": "Amazon One-Click: Instant Purchase System for E-commerce",
    "product_description": "Amazon One-Click enables online shoppers to complete purchases with a single mouse click, eliminating the need to re-enter payment and shipping information. It serves busy consumers and mobile users who want frictionless checkout experiences, significantly reducing cart abandonment and increasing conversion rates for e-commerce platforms.",
    "implementation": "The system uses the patented single-action ordering method to securely store customer payment methods, shipping addresses, and preferences. When users click the One-Click button, the system automatically processes the order using pre-stored information, handles payment authorization, and initiates fulfillment without requiring additional user input or navigation through checkout pages.",
    "differentiation": "Unlike traditional multi-step checkout processes that require users to navigate through cart, billing, and shipping pages, One-Click ordering completes purchases instantly with minimal user effort. This dramatically reduces purchase friction, decreases abandonment rates, and creates a competitive advantage through superior user experience, particularly on mobile devices where lengthy checkout flows are especially cumbersome."
}

# Run
uv run compile_result.py
'''

import json
import os
import shutil
from pathlib import Path

# --- Configuration ---

# Detect project root directory (where this script is located)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Change one category at a time {nlp, computer_science, material_chemistry}
CATEGORY = "computer_science"  # reload the crew config to get specialized agents

# All paths are now absolute and relative to project root
INPUT_JSONL_FILE = PROJECT_ROOT / f"knowledge/{CATEGORY}/{CATEGORY}.jsonl"
INPUT_JSONL_DIR = PROJECT_ROOT / f"output/{CATEGORY}"
OUTPUT_DIR = PROJECT_ROOT / f"output/{CATEGORY}"
OUTPUT_JSONL_FILE = OUTPUT_DIR / f"{CATEGORY}_output.jsonl"

# --- End Configuration ---

def get_expected_publication_numbers(jsonl_file: Path) -> set:
    """Reads a JSONL file and returns a set of publication numbers."""
    if not jsonl_file.exists():
        print(f"Input file not found: {jsonl_file}")
        return set()
    
    expected_numbers = set()
    with open(jsonl_file, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                if "publication_number" in data:
                    expected_numbers.add(data["publication_number"])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from line in {jsonl_file}: {line.strip()}")
    return expected_numbers

def validate_entry(entry: dict) -> bool:
    """Validates a single JSON entry based on the docstring requirements."""
    required_fields = {
        "publication_number": float('inf'),
        "title": 100,
        "product_description": 300,
        "implementation": 300,
        "differentiation": 300,
    }

    for field, max_len in required_fields.items():
        if field not in entry:
            print(f"Validation failed for {entry.get('publication_number', 'Unknown')}: Missing field '{field}'")
            return False
        
        field_len = len(entry[field])
        print(f"  - Field '{field}': {field_len} characters.")
        if field_len > max_len:
            print(f"Validation failed for {entry.get('publication_number', 'Unknown')}: Field '{field}' is too long ({field_len} > {max_len})")
            return False
    return True

def main():
    """Main function to compile and validate patent data."""
    print(f"Starting compilation for category: {CATEGORY}")

    # 1. Read Expected Patents from knowledge base
    expected_pub_numbers = get_expected_publication_numbers(INPUT_JSONL_FILE)
    if not expected_pub_numbers:
        print(f"Warning: No expected publication numbers found in {INPUT_JSONL_FILE}.")
    else:
        print(f"Found {len(expected_pub_numbers)} expected patents in {INPUT_JSONL_FILE}.")

    # 2. Find all individual output JSON files
    json_files = list(OUTPUT_DIR.glob("**/*_output_short.json"))
    print(f"Found {len(json_files)} individual JSON files to process in {OUTPUT_DIR}.")

    valid_entries = []
    processed_pub_numbers = set()

    # 3. Process and Validate each JSON file
    for file_path in json_files:
        try:
            print(f"\n--- Processing file: {file_path.name} ---")
            with open(file_path, "r") as f:
                data = json.load(f)
            
            if validate_entry(data):
                valid_entries.append(data)
                if "publication_number" in data:
                    processed_pub_numbers.add(data["publication_number"])
            else:
                print(f"Skipping invalid data in file: {file_path}")

        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from file: {file_path}")
        except Exception as e:
            print(f"An error occurred while processing {file_path}: {e}")

    print(f"Processed {len(valid_entries)} valid entries.")

    # 4. Write Compiled Output
    if valid_entries:
        # Sort entries by publication_number for consistent output
        valid_entries.sort(key=lambda x: x.get("publication_number", ""))
        with open(OUTPUT_JSONL_FILE, "w") as f_out:
            for entry in valid_entries:
                json.dump(entry, f_out)
                f_out.write('\n')
        print(f"Successfully compiled results to {OUTPUT_JSONL_FILE}")
    else:
        print("No valid entries to write.")

    # 5. Verify and Report Missing Patents
    if expected_pub_numbers:
        missing_pub_numbers = expected_pub_numbers - processed_pub_numbers
        if missing_pub_numbers:
            print("\n--- Missing Patents ---")
            print(f"{len(missing_pub_numbers)} expected patents were not found in the output:")
            for number in sorted(list(missing_pub_numbers)):
                print(f"- {number}")
        else:
            print("\nAll expected patents were processed and included in the output.")
    
        unexpected_pub_numbers = processed_pub_numbers - expected_pub_numbers
        if unexpected_pub_numbers:
            print("\n--- Unexpected Patents ---")
            print(f"{len(unexpected_pub_numbers)} patents were found in output but not in the knowledge base:")
            for number in sorted(list(unexpected_pub_numbers)):
                print(f"- {number}")

if __name__ == "__main__":
    main()
