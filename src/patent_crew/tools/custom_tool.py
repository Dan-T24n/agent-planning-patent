import json
import os
import pathlib
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from google import genai
from google.genai import types

class PatentJsonLoaderInput(BaseModel):
    """Input schema for PatentJsonLoaderTool."""
    json_file_path: str = Field(..., description="The relative path from the 'knowledge' directory to the patent's JSON data file. E.g., 'nlp/pdf_and_image/US-XYZ/US-XYZ.json'.")

class PatentJsonLoaderTool(BaseTool):
    name: str = "Patent JSON Loader"
    description: str = (
        "Loads and returns the content of a specific patent's JSON data file. "
        "The path provided should be relative to the 'knowledge' directory."
    )
    args_schema: Type[BaseModel] = PatentJsonLoaderInput
    # Define a root directory for knowledge base to ensure correct path resolution
    knowledge_base_root: str = "knowledge"

    def _run(self, json_file_path: str) -> Dict[str, Any] | str:
        """Loads JSON data from the specified patent file."""
        full_path = os.path.join(self.knowledge_base_root, json_file_path)
        
        if not os.path.exists(full_path):
            return f"Error: File not found at {full_path}. Please ensure the json_file_path is correct and relative to the '{self.knowledge_base_root}' directory."
        
        try:
            with open(full_path, 'r') as f:
                patent_data = json.load(f)
            return patent_data
        except json.JSONDecodeError:
            error_msg = f"Error: Could not decode JSON from file {full_path}. The file might be corrupted or not in valid JSON format."
            print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool error: {error_msg}") # DEBUG PRINT
            return error_msg
        except Exception as e:
            error_msg = f"Error: An unexpected error occurred while reading {full_path}: {str(e)}"
            print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool error: {error_msg}") # DEBUG PRINT
            return error_msg



class PatentGeminiPdfLoaderInput(BaseModel):
    """Input schema for PatentGeminiPdfLoaderTool."""
    pdf_file_path: str = Field(..., description="The relative path from the 'knowledge' directory to the patent's PDF file. E.g., 'nlp/pdf_and_image/US-XYZ/US-XYZ.pdf'.")
    # Optional: Model name if you want to allow selection, defaults to a capable one
    model_name: str = Field(default="gemini-2.5-flash-preview-05-20", description="The Gemini model to use for processing the PDF.") # Or "gemini-1.5-pro-latest"

class PatentGeminiPdfLoaderTool(BaseTool):
    name: str = "Patent PDF Loader (via Gemini)"
    description: str = (
        "Loads a patent PDF file and uses a Google Gemini model to extract its comprehensive content. "
        "The model will process both text and visual elements from the PDF. "
        "The path provided should be relative to the 'knowledge' directory. "
        "Returns the model's textual interpretation of the PDF content."
    )
    args_schema: Type[BaseModel] = PatentGeminiPdfLoaderInput
    knowledge_base_root: str = "knowledge"

    def _run(self, pdf_file_path: str, model_name: str = "gemini-2.5-flash-preview-05-20") -> str | Dict[str, Any]:
        if not genai:
            return "Error: Google GenAI library is not available or configured."

        full_path = os.path.join(self.knowledge_base_root, pdf_file_path)
        print(f"[DEBUG custom_tool.py] PatentGeminiPdfLoaderTool attempting to load and process via Gemini: {full_path}")

        if not os.path.exists(full_path):
            return f"Error: File not found at {full_path}. Please ensure the pdf_file_path is correct and relative to the '{self.knowledge_base_root}' directory."

        try:
            pdf_file = pathlib.Path(full_path)
            pdf_bytes = pdf_file.read_bytes()

            # It's crucial that the prompt here asks Gemini to extract/describe,
            # not to summarize or analyze, as that's the job of the subsequent agent.
            # The tool's job is to "load" the information.
            extraction_prompt = (
                "You are an expert patent analyst. First, extract the patent title and abstract to establish context. "
                "Then extract visual content of figures/diagrams. For each figure, provide detailed analysis maintaining "
                "overall patent context: 1) Overall design and layout of the figure, 2) Specific entities, components, "
                "and labeled elements present, 3) Relationships and connections between entities, 4) Key features and "
                "interactions among entities. Cross-reference figure descriptions in text with visual elements. "
                "Structure output: PATENT CONTEXT (title, abstract), VISUAL CONTENT for each figure: "
                "FIGURE [X] ANALYSIS with subsections for Design, Entities, Relationships, Features."
            )
            
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
            
            response = client.models.generate_content(
                model = "gemini-2.5-flash-preview-05-20",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes, mime_type='application/pdf',
                    ),
                    extraction_prompt])
            

            
            # Safety check, Gemini API might have safety ratings
            if not response.candidates or not response.candidates[0].content.parts:
                # Handle cases where the response might be blocked or empty due to safety settings or other issues
                safety_ratings_info = ""
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    safety_ratings_info = f"Blocked due to: {response.prompt_feedback.block_reason_message}"
                elif response.candidates and response.candidates[0].finish_reason != 'STOP':
                    safety_ratings_info = f"Finished with reason: {response.candidates[0].finish_reason.name}"

                error_msg = f"Error: Gemini model did not return expected content for {full_path}. {safety_ratings_info}".strip()
                print(f"[DEBUG custom_tool.py] PatentGeminiPdfLoaderTool error: {error_msg}")
                return error_msg

            extracted_content = response.text # .text conveniently concatenates parts

            print(f"[DEBUG custom_tool.py] Content snippet: {extracted_content[:200]}...")
            return extracted_content

        except Exception as e:
            error_msg = f"Error: An unexpected error occurred while processing PDF {full_path} with Gemini: {str(e)}"
            print(f"[DEBUG custom_tool.py] PatentGeminiPdfLoaderTool error: {error_msg}")
            return error_msg

