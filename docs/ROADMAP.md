# Objective

We build a multi-agents workflow based on CrewAI pdf and images handling capabilities.

**Input**: a folder contains description of a patent: a patent pdf file, a json file with text extracted from the pdf (patent description), and multiple images extracted from the patent pdf

**Process**: worfklow of 3 agents
- Patent specialist: ingest pdf, text, image -> patent overview: high-level overview of the patent, summarize technical details, example use-cases directly mentioned from the patent
- Business Development expert: given patent overview -> create 3 potential commercial product ideas, assess commercial viability and differentiation of each product
- R&D Director and Chief Technology Officer: given product ideas and patent overview -> review technical details, analyze feasibility of implementation for each product
- Experienced Investor: given 3 outputs from above -> make an articulated plan to evaluate each product, make recommendations to refine ideas, possibly combine strength from different products
- Venture Capital Managing Partner: given input from investor -> choose a final product, output: product Title, product description, Implementation, Differentiation
- 
  **Output**: a json file
- Product title: A concise name for your product  (up to 100 characters).
- Product description: A brief explanation of the product outlining its essential features and functions, the target users, their needs, and the benefits provided by the product (up to 300 characters).
- Implementation: An explanation describing how you will implement the patent’s technology into your product (up to 300 characters).
- Differentiation: An explanation highlighting what makes your product unique and the reason why it stands out from existing solutions (up to 300 characters).

Example output:
```json
{
  "publication_number": "US-202117564168-A",
  "title": "NameGuard: AI-Powered Access Control for Enterprise Systems",
  "product_description": "NameGuard helps IT admins and compliance teams block unauthorized access by checking user names against global deny lists and using AI to catch name variations. It’s ideal for finance, defense, and critical infrastructure sectors needing strong security and compliance.",
  "implementation": "Use the patented method to integrate a name screening API into login or user registration flows. Names are matched against an updated denylist, decomposed, and analyzed via a neural network to detect obfuscated identities. Access decisions are then returned to the enterprise system.",
  "differentiation": "Unlike traditional DPL checks, NameGuard detects partial or altered name matches using name decomposition and machine learning. It adapts to evolving threats, aggregates multi-source deny lists, and flags suspect names not yet on known lists, reducing false negatives and increasing compliance accuracy."
}
```