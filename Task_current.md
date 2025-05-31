# Objective

Build multi-agent workflow with CrewAI library to generate product ideas from patent data

# Process
**Input**: a folder contains description of a patent: a patent pdf file, a json file with text extracted from the pdf (patent description), and multiple images extracted from the patent pdf

  **Output**: a json file
- Product title: A concise name for your product  (up to 100 characters).
- Product description: A brief explanation of the product outlining its essential features and functions, the target users, their needs, and the benefits provided by the product (up to 300 characters).
- Implementation: An explanation describing how you will implement the patent's technology into your product (up to 300 characters).
- Differentiation: An explanation highlighting what makes your product unique and the reason why it stands out from existing solutions (up to 300 characters).

Example output:
```json
{
  "publication_number": "US-202117564168-A",
  "title": "NameGuard: AI-Powered Access Control for Enterprise Systems",
  "product_description": "NameGuard helps IT admins and compliance teams block unauthorized access by checking user names against global deny lists and using AI to catch name variations. It's ideal for finance, defense, and critical infrastructure sectors needing strong security and compliance.",
  "implementation": "Use the patented method to integrate a name screening API into login or user registration flows. Names are matched against an updated denylist, decomposed, and analyzed via a neural network to detect obfuscated identities. Access decisions are then returned to the enterprise system.",
  "differentiation": "Unlike traditional DPL checks, NameGuard detects partial or altered name matches using name decomposition and machine learning. It adapts to evolving threats, aggregates multi-source deny lists, and flags suspect names not yet on known lists, reducing false negatives and increasing compliance accuracy."
}
```

# Task: implement simple multi-agent workflow, with 2 agents

1. Read and understand the current simple example in `./src/patent_crew`
2. Read the input from `knowledge/nlp/pdf_and_image/US-2020073983-A1`, the publication_number is `US-2020073983-A1`

3. Agent workflow design:
3.1 patent analyst:
   - Task: Analyze the patent data from the provided JSON file.
   - Input: Reads the JSON file located at `knowledge/nlp/pdf_and_image/US-2020073983-A1/US-2020073983-A1.json` (assuming the JSON file is named after the publication_number within its directory).
   - Action: Ingests the JSON content using `JSONKnowledgeSource` to understand the patent's details, including its abstract, claims, and description.
   - Responsibilities:
     - Extract the core invention and problem solved.
     - Identify key technical components and methodologies described.
     - Note any explicitly mentioned advantages or novel aspects.
   - Expected Output: A structured summary of the patent's core technology, problem-solution, and key distinguishing features, which will be passed as context to the product manager.

3.2 product manager:
   - Task: Create a product concept based on the analyzed patent information.
   - Input: Receives the structured summary from the patent analyst.
   - Responsibilities:
     - Develop a "Product title" (concise, up to 100 characters).
     - Formulate a "Product description" (essential features, functions, target users, needs, benefits; up to 300 characters).
     - Outline the "Implementation" strategy (how to apply the patent's technology; up to 300 characters).
     - Articulate the "Differentiation" (unique selling points compared to existing solutions; up to 300 characters).
   - Expected Output: A JSON object including `publication_number` (e.g., "US-2020073983-A1"), `title`, `product_description`, `implementation`, and `differentiation`, matching the format specified in the #Objective section.

4.1 The output should be exact json format, as described above in #Objective
4.1 The output is stored in output/nlp/{publication_number}_output.json

