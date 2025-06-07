'''
This crew is used to rewrite the product concept to be a maximum of 250-300 characters.

All output files are saved in the output/{CATEGORY}/{batch_idx}/{publication_number}_output.json files.

We want to take in the json files and rewrite the product concept. 

Upon rewriting, we want to check the length of each field, make sure it's less than 300 characters.

Finally, we save the rewritten product concept in the same place, with a suffix:
output/{CATEGORY}/{batch_idx}/{publication_number}_output_short.json
'''

import glob
import json
import os
from typing import List, Tuple, Any, Dict
from crewai import Agent, Task, Crew, Process, LLM, TaskOutput
from crewai.project import CrewBase, agent, crew, task

# Import the patent analysis tools
from patent_crew.tools.custom_tool import PatentJsonLoaderTool, PatentGeminiPdfLoaderTool

# set to a specific patent number to process only that file, or None to process all files
TARGET_PATENT_NUMBER = "US-12013751-B2" 

# choose a category: nlp, computer_science, material_chemistry
CATEGORY = "computer_science"
# Ensure the output directory exists
output_dir = f"output/{CATEGORY}"
os.makedirs(output_dir, exist_ok=True)

# Guardrail Definition
def ensure_output_length(task_output: TaskOutput) -> Tuple[bool, Any]:
    """
    A simple guardrail to ensure each field of the product concept is less than 300 characters.
    """
    print("----- Running Guardrail: ensure_output_length -----")
    try:
        data = json.loads(task_output.raw)
        print("Guardrail: Successfully parsed JSON output.")
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 350:
                print(f"Guardrail FAILED: Field '{key}' is too long: {len(value)} characters.")
                return False, f"Field '{key}' is too long."
        print("Guardrail PASSED: All fields are within the length limit.")
        return True, data
    except json.JSONDecodeError as e:
        print(f"Guardrail FAILED: Invalid JSON output. Error: {e}")
        print(f"Guardrail: Raw output was: {task_output.raw}")
        return False, f"Invalid JSON output: {e}"
    
    

@CrewBase
class RewriteCrew():
    """Crew to rewrite product concepts to be more concise."""
    agents_config = 'config/rewrite_agents.yaml'
    tasks_config = 'config/rewrite_tasks.yaml'
    
    llm_openai_o3 = LLM(
        model="openai/o3-mini",
        temperature=0.2,
        timeout=180
        )

    @agent
    def product_concept_rewriter(self) -> Agent:
        return Agent(
            config=self.agents_config['product_concept_rewriter'],
            llm=self.llm_openai_o3,
        )

    @task
    def rewrite_product_concept_task(self) -> Task:
        return Task(
            config=self.tasks_config['rewrite_product_concept_task'],
            agent=self.product_concept_rewriter(),
            guardrail=ensure_output_length,
            max_retries=3
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RewriteCrew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True
        )

def find_json_files(directory: str) -> List[str]:
    """Find all JSON files ending with '_output.json' in the specified directory."""
    return glob.glob(f"{directory}/**/*_output.json", recursive=True)

if __name__ == '__main__':
    json_files = find_json_files(output_dir)
    
    print(f"Found {len(json_files)} files to process.")
    
    if not json_files:
        print(f"No '_output.json' files found in {output_dir}")
    else:
        print(f"First file: {json_files[0]}")
        
        # # test with a single file
        # files_to_process = [json_files[0]]
        # json_files = files_to_process
        
        print(f"Found {len(json_files)} files to process.")
        

    for json_file in json_files:
        if TARGET_PATENT_NUMBER and TARGET_PATENT_NUMBER not in json_file:
            continue
            
        print(f"\n----- Processing file: {json_file} -----")
        try:
            with open(json_file, 'r') as f:
                file_content = f.read()
            print(f"Successfully read file content. Size: {len(file_content)} bytes.")
            
            inputs = {'json_file': file_content}
            
            print("Kicking off RewriteCrew...")
            rewrite_crew = RewriteCrew()
            result = rewrite_crew.crew().kickoff(inputs=inputs)
            print("RewriteCrew finished.")
            
            
            # save the result to a new file
            output_filename = json_file.replace('_output.json', '_output_short.json')
            
            data_to_save = None
            # The result of a crew kickoff is a CrewOutput object.
            # The final result is in the `raw` attribute.
            if result and hasattr(result, 'raw') and result.raw:
                if isinstance(result.raw, dict):
                    data_to_save = result.raw
                else:
                    try:
                        data_to_save = json.loads(result.raw)
                    except json.JSONDecodeError:
                        print(f"Failed to process {json_file}. Result.raw is a string but not valid JSON: {result.raw}")
            else:
                 print(f"Failed to process {json_file}. Unexpected result format: {type(result)} -> {result}")

            if data_to_save:
                with open(output_filename, 'w') as f:
                    json.dump(data_to_save, f, indent=2)
                print(f"Successfully rewritten and saved to {output_filename}")
            else:
                print(f"Failed to process {json_file}. Unexpected result format: {type(result)} -> {result}")

        except Exception as e:
            print(f"An error occurred while processing {json_file}: {e}") 