#!/usr/bin/env python3
"""
Test case for CrewAI VisionTool with a single agent.
This script uses VisionTool to extract text from a local image.
"""

import os
from crewai import Agent, Task, Crew, LLM
from crewai_tools import VisionTool

def test_vision_tool_agent_with_local_image():
    """
    Tests text extraction from a local image using an agent with VisionTool.
    """
    print("\n=== Test: Agent with VisionTool for Local Image Text Extraction ===")

    image_target_path = "knowledge/nlp/pdf_and_image/US-10657124-B2/1.png"
    image_path = os.path.abspath(image_target_path)

    if not os.path.exists(image_path):
        print(f"⚠️ Error: Image not found at the specified absolute path: {image_path}")
        print(f"Please ensure the image file exists at: {image_target_path} (relative to project root)")
        return

    # Initialize the VisionTool
    vision_tool = VisionTool()

    # Create an agent with the VisionTool
    text_extractor_agent = Agent(
        role="Image Text Extractor",
        goal="Extract and summarize text content from a provided local image",
        backstory="You are an expert at reading and extracting text from various image formats.",
        tools=[vision_tool],
        verbose=True,
        llm=LLM(model="gpt-4o") # or any other suitable model
    )

    # Create a task for text extraction from the local image
    extract_text_task = Task(
        description=f"""
        Your primary task is to use the 'VisionTool' to analyze the image at the path: {image_path}.
        You MUST invoke VisionTool with this image path.
        After VisionTool provides its analysis, extract and summarize all identifiable text content from the tool's output.
        Present this summary as your final answer.
        """,
        expected_output="A summary of the text content extracted by VisionTool from the image.",
        agent=text_extractor_agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[text_extractor_agent],
        tasks=[extract_text_task],
        verbose=True
    )

    try:
        result = crew.kickoff()
        raw_output = result.raw if result else "No result returned"
        print(f"Text Extraction Result: {raw_output}")
        
        # Save output to markdown file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, "test_vision_tool_agent_output.md")
        with open(output_file_path, "w") as f:
            f.write("## Test: Agent with VisionTool for Local Image Text Extraction\n\n")
            f.write("### Image Path:\n")
            f.write(f"```{image_path}```\n\n")
            f.write("### Raw Output:\n")
            f.write(f"```\n{raw_output}\n```\n")
        print(f"Output saved to {output_file_path}")
        
        return result
    except Exception as e:
        print(f"❌ Error running VisionTool agent test: {str(e)}")
        return None

if __name__ == "__main__":
    test_vision_tool_agent_with_local_image() 