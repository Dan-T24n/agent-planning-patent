import os
from typing import List 
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
# import agentops

# Import the new tool
from patent_crew.tools.custom_tool import PatentJsonLoaderTool, PatentImageLoaderTool

# Initialize AgentOps
# agentops.init()

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

    # Removed json_knowledge_source and agent_knowledge_sources that used JSONKnowledgeSource directly

    # Instantiate tools
    search_tool = SerperDevTool(
        country="us",
        n_results=5
    )
    patent_json_loader_tool = PatentJsonLoaderTool()
    patent_image_loader_tool = PatentImageLoaderTool()

    # Define knowledge config (can be kept if it has other uses, or removed if only for JSONKnowledgeSource)
    # For now, assuming it might be used by the agent or other tools for general knowledge handling if any.
    custom_knowledge_config = KnowledgeConfig(
        results_limit=5, 
        score_threshold=0.5
    )

    @agent
    def patent_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['patent_analyst'],
            tools=[self.search_tool, self.patent_json_loader_tool],
            verbose=True,
            knowledge_config=self.custom_knowledge_config # Keep for now
            # Removed knowledge_sources that pointed to the old JSONKnowledgeSource
        )

    @agent
    def patent_analyst_visual(self) -> Agent:
        return Agent(
            config=self.agents_config['patent_analyst_visual'],
            tools=[
                self.search_tool,
                self.patent_json_loader_tool,
                self.patent_image_loader_tool
            ],
            verbose=True,
            multimodal=True # Ensure multimodal is enabled
            # knowledge_config can be added if needed
        )

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'],
            tools=[self.search_tool],
            verbose=True
        )

    @agent
    def managing_partner(self) -> Agent:
        return Agent(
            config=self.agents_config['managing_partner'],
            verbose=True
            # Add tools here if the managing_partner needs them, e.g., tools=[self.search_tool]
        )

    @task
    def document_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['document_analysis_task'],
            agent=self.patent_analyst()
        )

    @task
    def document_visual_analysis_task(self) -> Task:
        task_config = self.tasks_config['document_visual_analysis_task']
        return Task(
            config=task_config,
            agent=self.patent_analyst_visual()
        )

    @task
    def patent_context_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['patent_context_research_task'],
            agent=self.product_manager(), 
            context=[self.document_visual_analysis_task()]
        )

    @task
    def market_fit_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_fit_research_task'],
            agent=self.product_manager(),
            context=[
                self.document_visual_analysis_task()
            ]
        )

    @task
    def usp_validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['usp_validation_task'],
            agent=self.product_manager(),
            context=[
                self.document_visual_analysis_task(),
                self.patent_context_research_task(),
                self.market_fit_research_task() # As per plan
            ]
        )

    @task
    def product_definition_task(self) -> Task:
        # The task description uses {publication_number}
        # The output_file in tasks_nlp.yaml uses {publication_number}
        return Task(
            config=self.tasks_config['product_definition_task'],
            agent=self.managing_partner(),
            context=[
                self.document_visual_analysis_task(),
                self.patent_context_research_task(),
                self.market_fit_research_task(),
                self.usp_validation_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        # print(f"[DEBUG crew.py] ..Assembling crew for patent {self.publication_number}..") # Original, self.publication_number might not be set here
        print(f"[DEBUG crew.py] Assembling crew with agents: {[agent.role for agent in self.agents]}") # DEBUG PRINT
        print(f"[DEBUG crew.py] Assembling crew with tasks: {[task.description[:50] + '...' for task in self.tasks]}") # DEBUG PRINT

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            # Removed knowledge_sources that pointed to the old JSONKnowledgeSource
            verbose=True
        )
