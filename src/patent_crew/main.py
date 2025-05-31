#!/usr/bin/env python
import warnings

from patent_crew.crew import PatentAnalysisCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the Patent Analysis crew.
    """
    print("## Starting Patent Analysis Crew")
    print('---------------------------------------')

    try:
        # Instantiate and kick off the crew
        # Inputs are not passed as they are hardcoded for this specific task
        result = PatentAnalysisCrew().crew().kickoff()

        print("\n######################")
        print("## Crew Execution Result:")
        print("######################")
        print(result)
        # The output file path is defined in tasks.yaml and handled by the crew.
        # print(f"\nOutput file should be generated at: {os.path.join(output_dir, output_file_name)}") # Removed

    except Exception as e:
        raise Exception(f"An error occurred while running the Patent Analysis crew: {e}")

# To run this main.py, you would typically use: `uv run src/patent_crew/main.py run`
# Or if pyproject.toml is configured: `uv run` or `crewai run`



