#!/usr/bin/env python3
"""
Test case for CrewAI multimodal agent capabilities.
This script uses a single agent with multimodal=True to analyze a local image.
"""

import os
from crewai import Agent, Task, Crew, LLM
from crewai_tools import VisionTool # Import VisionTool

def test_multimodal_agent_with_local_image():
    """
    Tests comprehensive analysis of a local image using a multimodal agent, 
    now explicitly directing it to use VisionTool.
    """
    print("\n=== Test: Multimodal Agent with VisionTool for Local Image Analysis ===")

    image_target_path = "knowledge/nlp/pdf_and_image/US-10657124-B2/1.png"
    image_path = os.path.abspath(image_target_path)

    if not os.path.exists(image_path):
        print(f"⚠️ Error: Image not found at the specified absolute path: {image_path}")
        print(f"Please ensure the image file exists at: {image_target_path} (relative to project root)")
        return

    # Initialize the VisionTool
    vision_tool = VisionTool()

    # Create a multimodal agent and explicitly give it VisionTool
    image_analyst_agent = Agent(
        role="Comprehensive Image Analyst",
        goal=(
            "Use the VisionTool to analyze a provided local image and then provide a detailed textual report. "
            "The report should include identified text, visual elements, objects, and overall composition."
        ),
        backstory=(
            "You are an expert visual analyst. You always use the VisionTool for image analysis "
            "and return your full analysis as a single, well-structured string."
        ),
        tools=[vision_tool], # Explicitly add VisionTool
        multimodal=True,  # Keep multimodal True to see interaction
        verbose=True,
        llm=LLM(model="gpt-4o") 
    )

    # Create a task for comprehensive image analysis of the local image
    analyze_image_task = Task(
        description=f"""
        Using the VisionTool, analyze the local image located at: {image_path}
        
        Your analysis should be comprehensive and include:
        1. Any identifiable text content, transcribed accurately.
        2. A description of the main visual elements and their arrangement.
        3. Identification of any prominent objects or figures.
        4. An overview of the image's overall composition and style.
        5. If it's a diagram or chart, explain what it represents.
        
        Compile all your findings into a single, well-structured textual report.
        """,
        expected_output=(
            "A single string containing a detailed textual report based on VisionTool analysis, "
            "covering text, visual elements, objects, and composition of the image."
        ),
        agent=image_analyst_agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[image_analyst_agent],
        tasks=[analyze_image_task],
        verbose=True
    )

    try:
        result = crew.kickoff()
        raw_output = result.raw if result else "No result returned"
        print(f"Multimodal (with VisionTool) Image Analysis Result: {raw_output}")

        # Save output to markdown file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, "test_multimodal_true_agent_output.md")
        with open(output_file_path, "w") as f:
            f.write("## Test: Multimodal Agent with VisionTool for Local Image Analysis\n\n")
            f.write("### Image Path:\n")
            f.write(f"```{image_path}```\n\n")
            f.write("### Raw Output:\n")
            f.write(f"```\n{raw_output}\n```\n")
        print(f"Output saved to {output_file_path}")

        return result
    except Exception as e:
        print(f"❌ Error running multimodal agent (with VisionTool) test: {str(e)}")
        return None

if __name__ == "__main__":
    test_multimodal_agent_with_local_image() 