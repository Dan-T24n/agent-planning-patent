'''
# Goal
This utility script is used to compile individual patent-product json into a jsonl file.
For a specific category, e.g. "nlp", we have results in output/nlp/{batch_idx}/{publication_number}_output.json.

The goal is to compile all the individual patent-product json into a jsonl file for each category,
the jsonl file should be at: output/{category}/{category}_output.jsonl.

Each input json "output/nlp/{batch_idx}/{publication_number}_output.json" is a valid json/dictionary,
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
│           └── US-2020073983-A1_output.json  # Output for patent US-2020073983-A1
│           └── ...                           # Output for other patents
│       └── 1/                                # Batch 1
│           └── US-2020073983-A1_output.json  # Output for patent US-2020073983-A1
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
CATEGORY = "nlp"  # reload the crew config to get specialized agents

# All paths are now absolute and relative to project root
INPUT_FILE_PATH = PROJECT_ROOT / f"data/{CATEGORY}/{CATEGORY}.jsonl"
SOURCE_PATENT_ARTIFACTS_DIR = PROJECT_ROOT / f"data/{CATEGORY}/pdf_and_image/"
KNOWLEDGE_BASE_OUTPUT_DIR = PROJECT_ROOT / f"knowledge/{CATEGORY}/pdf_and_image/"

# --- End Configuration ---

