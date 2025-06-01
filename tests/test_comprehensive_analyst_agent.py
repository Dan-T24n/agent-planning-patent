#!/usr/bin/env python3
"""
Test case for a comprehensive CrewAI vision agent.
This script uses a single agent with multimodal=True AND VisionTool 
to perform a combined text extraction and visual analysis of a local image.
"""

import os
from crewai import Agent, Task, Crew, LLM
from crewai_tools import VisionTool

def test_comprehensive_image_analysis():
    """
    Tests combined text extraction (via VisionTool) and visual analysis 
    (via multimodal capabilities) by a single agent.
    """
    print("\n=== Test: Comprehensive Analyst Agent (Multimodal + VisionTool) ===")

    image_target_path = "knowledge/nlp/pdf_and_image/US-10657124-B2/1.png"
    image_path = os.path.abspath(image_target_path)

    if not os.path.exists(image_path):
        print(f"⚠️ Error: Image not found at the specified absolute path: {image_path}")
        print(f"Please ensure the image file exists at: {image_target_path} (relative to project root)")
        return

    # Initialize the VisionTool
    vision_tool = VisionTool()

    # Create a comprehensive analyst agent
    comprehensive_analyst_agent = Agent(
        role="Structured Image Report Generator",
        goal=(
            "Follow a strict three-step process for image analysis: "
            "1. Extract text using VisionTool. "
            "2. Perform visual analysis using multimodal capabilities. "
            "3. Compile findings into a single textual report with specific section headers."
        ),
        backstory=(
            "You are a meticulous analyst specializing in generating structured reports from image data. "
            "You always use VisionTool first for text, then your multimodal vision for visuals. "
            "Your final output is ALWAYS a single string formatted with clear sections: 'Text Extraction Findings', "
            "'Visual Analysis Findings', and 'Synthesis'."
        ),
        tools=[vision_tool],      # Explicitly provide VisionTool
        multimodal=True,          # Enable multimodal capabilities
        verbose=True,
        llm=LLM(model="gpt-4o")   # Vision-capable model
    )

    # Create a task for the comprehensive analysis
    comprehensive_analysis_task = Task(
        description=f"""
        Your task is to conduct a multi-step analysis of the image at: {image_path} and produce a structured report.
        
        **Step 1: Text Extraction (Mandatory Tool Use)**
        You MUST first use the 'VisionTool' with the image path '{image_path}' to extract all identifiable text. Accurately record the complete text output from VisionTool.
        
        **Step 2: Visual Analysis (Multimodal Capability)**
        After successfully obtaining the text output from VisionTool, use your inherent multimodal capabilities to independently analyze the image's visual aspects. Describe its main visual elements, their arrangement, any prominent objects/figures, and the overall composition and style. If it's a diagram, explain its general visual representation.
        
        **Step 3: Synthesized Report (Mandatory Final Format)**
        Finally, you MUST combine the text extracted by VisionTool (from Step 1) and your visual analysis (from Step 2) into a single textual report. This report MUST use the following exact section headers (e.g., using markdown ##):
        ## Text Extraction Findings
        [Insert text from VisionTool here]
        
        ## Visual Analysis Findings
        [Insert your multimodal visual analysis here]
        
        ## Synthesis
        [Insert a brief synthesis of both text and visual findings here]
        
        It is crucial you perform Step 1 before Step 2, and Step 3 is your final output format.
        """,
        expected_output=(
            "A single string report formatted exactly as follows:\n"
            "## Text Extraction Findings\n"
            "[Text content from VisionTool]\n\n"
            "## Visual Analysis Findings\n"
            "[Detailed visual description from multimodal analysis]\n\n"
            "## Synthesis\n"
            "[Brief synthesis combining text and visual insights]"
        ),
        agent=comprehensive_analyst_agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[comprehensive_analyst_agent],
        tasks=[comprehensive_analysis_task],
        verbose=True
    )

    try:
        result = crew.kickoff()
        raw_output = result.raw if result else "No result returned"
        print(f"Comprehensive Analysis Result: {raw_output}")

        # Save output to markdown file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, "test_comprehensive_analyst_agent_output.md")
        with open(output_file_path, "w") as f:
            f.write("## Test: Comprehensive Analyst Agent (Multimodal + VisionTool)\n\n")
            f.write("### Image Path:\n")
            f.write(f"```{image_path}```\n\n")
            f.write("### Raw Output:\n")
            f.write(f"```\n{raw_output}\n```\n")
        print(f"Output saved to {output_file_path}")

        return result
    except Exception as e:
        print(f"❌ Error running comprehensive analyst agent test: {str(e)}")
        return None

if __name__ == "__main__":
    test_comprehensive_image_analysis() 