import os
from typing import List # Added for type hinting
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai_tools import SerperDevTool

# Ensure the output directory exists
output_dir = "output/nlp"
os.makedirs(output_dir, exist_ok=True)

@CrewBase
class PatentAnalysisCrew():
    """PatentAnalysisCrew"""
    agents_config = 'config/agents_nlp.yaml'
    tasks_config = 'config/tasks_nlp.yaml'

    # Type hints for agents and tasks lists, to be populated by decorators
    agents: List[Agent]
    tasks: List[Task]

    # Define the JSONKnowledgeSource
    # The path is relative to the 'knowledge' directory at the project root
    patent_json_path = "nlp/pdf_and_image/US-2020073983-A1/US-2020073983-A1.json"
    json_knowledge_source = JSONKnowledgeSource(file_paths=[patent_json_path])

    # Instantiate tools
    search_tool = SerperDevTool(
        country="us",
        n_results=5
    )

    @agent
    def patent_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['patent_analyst'],
            tools=[self.search_tool],
            verbose=True
        )

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'],
            tools=[self.search_tool],
            verbose=True
        )

    @task
    def patent_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['patent_analysis_task'],
            agent=self.patent_analyst()
        )

    @task
    def product_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_creation_task'],
            agent=self.product_manager(),
            context=[self.patent_analysis_task()]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            knowledge_sources=[self.json_knowledge_source],
            verbose=True
        )
