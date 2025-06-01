import os
from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import VisionTool

@CrewBase
class VisualTestCrew():
    """VisualTestCrew for isolating and testing the patent_analyst_visual agent."""
    agents_config = 'config/agents_nlp.yaml'
    tasks_config = 'config/tasks_test.yaml'

    @agent
    def patent_analyst_visual(self) -> Agent:
        """Agent responsible for analyzing patent documents using text and images."""
        image_analysis_tool = VisionTool()
        return Agent(
            config=self.agents_config['patent_analyst_visual'],
            verbose=True,
            multimodal=True,
            tools=[image_analysis_tool],
            llm="gpt-4o"
        )

    @task
    def document_visual_analysis_task(self) -> Task:
        task_config = self.tasks_config['document_visual_analysis_task']
        return Task(
            config=task_config,
            agent=self.patent_analyst_visual()
        )

    @crew
    def crew(self) -> Crew:
        """Assembles the crew for the visual analysis test."""
        return Crew(
            agents=[self.patent_analyst_visual()],  
            tasks=[self.document_visual_analysis_task()], 
            process=Process.sequential,
            verbose=True,
            memory=True 
        ) 
