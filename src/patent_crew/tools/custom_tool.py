import json
import os
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

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
        print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool attempting to load: {full_path}") # DEBUG PRINT
        
        if not os.path.exists(full_path):
            return f"Error: File not found at {full_path}. Please ensure the json_file_path is correct and relative to the '{self.knowledge_base_root}' directory."
        
        try:
            with open(full_path, 'r') as f:
                patent_data = json.load(f)
            print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool successfully loaded {full_path}. Data snippet: {str(patent_data)[:200]}...") # DEBUG PRINT
            return patent_data
        except json.JSONDecodeError:
            error_msg = f"Error: Could not decode JSON from file {full_path}. The file might be corrupted or not in valid JSON format."
            print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool error: {error_msg}") # DEBUG PRINT
            return error_msg
        except Exception as e:
            error_msg = f"Error: An unexpected error occurred while reading {full_path}: {str(e)}"
            print(f"[DEBUG custom_tool.py] PatentJsonLoaderTool error: {error_msg}") # DEBUG PRINT
            return error_msg


# Obsolete: pass paths directly to the agent as string inputs

# class PatentImageLoaderInput(BaseModel):
#     """Input schema for PatentImageLoaderTool."""
#     image_paths: List[str] = Field(..., description="A list of absolute file paths for the patent's images.")

# class PatentImageLoaderTool(BaseTool):
#     name: str = "Patent Image Path Provider"
#     description: str = (
#         "Accepts a list of pre-resolved absolute image file paths and makes them available to the agent. "
#         "This tool does not perform any I/O or path resolution itself; it expects paths to be fully resolved by the caller."
#     )
#     args_schema: Type[BaseModel] = PatentImageLoaderInput
#     # knowledge_base_root: str = "knowledge" # No longer strictly needed as paths are pre-resolved

#     def _run(self, image_paths: List[str]) -> List[str] | str:
#         """Returns the provided list of absolute image paths."""
#         print(f"[DEBUG custom_tool.py] PatentImageLoaderTool received image_paths: {image_paths}") # DEBUG PRINT
#         if not image_paths:
#             print("[DEBUG custom_tool.py] PatentImageLoaderTool received empty image_paths list.") # DEBUG PRINT
#             return "Input 'image_paths' list is empty."
        
#         return image_paths
