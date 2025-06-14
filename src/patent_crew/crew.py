import os
from typing import List, Tuple, Any
from crewai import Agent, Task, Crew, Process, LLM, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import LinkupSearchTool, SerperDevTool

# Import the patent analysis tools
from patent_crew.tools.custom_tool import PatentJsonLoaderTool, PatentGeminiPdfLoaderTool

# Ensure the output directory exists
output_dir = "output/material_chemistry"
os.makedirs(output_dir, exist_ok=True)

# Guardrail Definition
def ensure_output_exists(task_output: TaskOutput) -> Tuple[bool, Any]:
    """
    A simple guardrail to ensure the task's raw output is not empty.
    """
    if task_output.raw and task_output.raw.strip():
        return True, task_output.raw
    else:
        return False, "The task did not produce any output."


@CrewBase
class PatentAnalysisCrew():
    """Enhanced Patent-to-Product Analysis Crew with 11 tasks and 9 agents"""
    agents_config = 'config/agents_mc.yaml'
    tasks_config = 'config/tasks_mc.yaml'

    # Type hints for agents and tasks lists, to be populated by decorators
    agents: List[Agent]
    tasks: List[Task]
    
    llm_small= LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.1,
        timeout=180
    )

# Rate limit exceeded
    llm_large = LLM(
        model="gemini/gemini-2.5-pro-preview-05-06",
        temperature=0.3
    )

    llm_openai_mini = LLM(
        model="gpt-4o-mini",
        # model="openai/o3-mini",
        temperature=0,
        timeout=180
    )
    
    llm_openai_o3 = LLM(
        # model="gpt-4o-mini",
        model="openai/o3-mini",
        temperature=0.2,
        timeout=180
    )   


    # Instantiate tools
    linkup_search_tool = LinkupSearchTool(api_key=os.getenv("LINKUP_API_KEY"))
    serper_dev_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))
    patent_json_loader_tool = PatentJsonLoaderTool()
    patent_gemini_pdf_loader_tool = PatentGeminiPdfLoaderTool()

    # ===============================
    # PHASE 1: Patent & Technology Analysis (2 Agents)
    # ===============================

    @agent
    def patent_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['patent_analyst'],
            tools=[self.patent_json_loader_tool],
            verbose=False,
            llm=self.llm_small        
            )

    @agent
    def patent_analyst_visual(self) -> Agent:
        return Agent(
            config=self.agents_config['patent_analyst_visual'],
            tools=[self.patent_gemini_pdf_loader_tool],
            verbose=False,
            llm=self.llm_openai_o3
        )

    # ===============================
    # PHASE 2: Market Research & Validation (2 Agents)
    # ===============================

    @agent
    def market_research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['market_research_analyst'],
            tools=[self.linkup_search_tool],
            verbose=False,
            llm=self.llm_openai_o3,
        )

    @agent
    def product_research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['product_research_analyst'],
            tools=[self.linkup_search_tool],
            verbose=False,
            llm=self.llm_openai_o3
        )

    # ===============================
    # PHASE 3: Product Concept Generation (3 Agents)
    # ===============================

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'],
            verbose=False,
            llm=self.llm_openai_o3
        )

    @agent
    def serial_entrepreneur(self) -> Agent:
        return Agent(
            config=self.agents_config['serial_entrepreneur'],
            verbose=False,
            llm=self.llm_openai_o3
        )

    @agent
    def research_commercialization_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['research_commercialization_expert'],
            verbose=False,
            llm=self.llm_openai_o3
        )

    # ===============================
    # PHASE 4: Evaluation & Output Formatting (2 Agents)
    # ===============================

    @agent
    def product_evaluator_1(self) -> Agent:
        return Agent(
            config=self.agents_config['product_evaluator_1'],
            verbose=False,
            tools=[self.linkup_search_tool],
            llm=self.llm_openai_o3,
            max_retries=3
        )

    @agent
    def product_evaluator_2(self) -> Agent:
        return Agent(
            config=self.agents_config['product_evaluator_2'],
            verbose=False,
            tools=[self.linkup_search_tool],
            llm=self.llm_openai_o3,
            max_retries=3
        )

    @agent
    def product_evaluator_3(self) -> Agent:
        return Agent(
            config=self.agents_config['product_evaluator_3'],
            verbose=False,
            tools=[self.linkup_search_tool],
            llm=self.llm_openai_o3,
            max_retries=3
        )

    @agent
    def output_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['output_summarizer'],
            verbose=True,
            llm=self.llm_openai_o3
        )

    # ===============================
    # PHASE 1: Patent & Technology Analysis (2 Tasks)
    # ===============================

    @task
    def document_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['document_analysis_task'],
            agent=self.patent_analyst(),
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def document_visual_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['document_visual_analysis_task'],
            agent=self.patent_analyst_visual(),
            guardrail=ensure_output_exists,
            max_retries=3
        )

    # ===============================
    # PHASE 2: Market Research & Validation (2 Tasks)
    # ===============================

    @task
    def market_opportunity_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_opportunity_analysis_task'],
            agent=self.market_research_analyst(),
            context=[
                self.document_analysis_task(),
                self.document_visual_analysis_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def user_pain_point_validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['user_pain_point_validation_task'],
            agent=self.product_research_analyst(),
            context=[
                self.document_analysis_task(),
                self.document_visual_analysis_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    # ===============================
    # PHASE 3: Product Concept Generation (3 Tasks)
    # ===============================

    @task
    def product_concept_pm_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_concept_pm_task'],
            agent=self.product_manager(),
            async_execution=True,
            context=[
                self.market_opportunity_analysis_task(),
                self.user_pain_point_validation_task(),
                self.document_analysis_task(),
                self.document_visual_analysis_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def product_concept_entrepreneur_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_concept_entrepreneur_task'],
            agent=self.serial_entrepreneur(),
            async_execution=True,
            context=[
                self.market_opportunity_analysis_task(),
                self.user_pain_point_validation_task(),
                self.document_analysis_task(),
                self.document_visual_analysis_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def product_concept_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_concept_research_task'],
            agent=self.research_commercialization_expert(),
            async_execution=True,
            context=[
                self.market_opportunity_analysis_task(),
                self.user_pain_point_validation_task(),
                self.document_analysis_task(),
                self.document_visual_analysis_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    # ===============================
    # PHASE 4: Evaluation & Output Formatting (3 Tasks)
    # ===============================

    @task
    def product_evaluation_pm_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_evaluation_pm_task'],
            agent=self.product_evaluator_1(),
            context=[self.product_concept_pm_task()],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def product_evaluation_entrepreneur_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_evaluation_entrepreneur_task'],
            agent=self.product_evaluator_2(),
            context=[self.product_concept_entrepreneur_task()],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def product_evaluation_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['product_evaluation_research_task'],
            agent=self.product_evaluator_3(),
            context=[self.product_concept_research_task()],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @task
    def final_product_selection_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_product_selection_task'],
            agent=self.output_summarizer(),
            context=[
                self.product_evaluation_pm_task(),
                self.product_evaluation_entrepreneur_task(),
                self.product_evaluation_research_task()
            ],
            guardrail=ensure_output_exists,
            max_retries=3
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            verbose=True
        ) 