"""
Multi-Image Analysis Crew
Creates separate tasks for each image with proper context flow between tasks.
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from typing import List, Dict, Any
import os

def create_multi_image_analysis_crew(image_paths: List[str]) -> Crew:
    """
    Creates a crew that analyzes multiple images one at a time and summarizes results.
    
    Args:
        image_paths: List of paths to images to be analyzed
        
    Returns:
        Configured Crew instance
    """
    
    # Agent 1: Image Analyzer
    image_analyzer = Agent(
        role="Image Analyzer",
        goal="Analyze individual images and extract detailed information about their content",
        backstory="""You are an expert image analyst with deep knowledge in computer vision 
        and visual content analysis. You excel at identifying objects, scenes, text, people, 
        emotions, and other visual elements in images. You provide detailed, accurate 
        descriptions of what you observe.""",
        verbose=True,
        multimodal=True,  # This automatically includes AddImageTool for image processing
        allow_delegation=False
    )
    
    # Agent 2: Results Summarizer
    results_summarizer = Agent(
        role="Results Summarizer", 
        goal="Collect and synthesize analysis results from multiple images into a comprehensive summary",
        backstory="""You are a skilled data analyst who specializes in synthesizing 
        information from multiple sources. You excel at identifying patterns, themes, 
        and insights across different data points and creating clear, organized summaries 
        that highlight key findings and relationships.""",
        verbose=True,
        allow_delegation=False
    )
    
    # Create individual analysis tasks for each image
    image_analysis_tasks = []
    
    for i, image_path in enumerate(image_paths):
        task = Task(
            description=f"""
            Analyze the image located at: {image_path}
            
            Please provide a detailed analysis including:
            1. Overall description of the image
            2. Key objects and elements present
            3. Colors, composition, and visual style
            4. Any text or writing visible
            5. People or faces (if present) and their expressions/actions
            6. Setting or environment
            7. Any notable details or interesting aspects
            
            Be thorough and specific in your analysis. This analysis will be used 
            by another agent to create a comprehensive summary of multiple images.
            """,
            agent=image_analyzer,
            expected_output=f"Detailed analysis report for image {i+1} covering all visual elements and content"
        )
        image_analysis_tasks.append(task)
    
    # Create summarization task that uses context from all previous tasks
    summary_task = Task(
        description="""
        Create a comprehensive summary report based on all the individual image analyses 
        you have received. Your summary should include:
        
        1. **Overview**: Brief description of the total number of images analyzed
        2. **Common Themes**: Identify any recurring elements, themes, or patterns across images
        3. **Individual Highlights**: Key unique aspects from each image
        4. **Content Categories**: Organize findings by categories (objects, people, settings, etc.)
        5. **Visual Styles**: Compare and contrast visual styles, colors, compositions
        6. **Text Content**: Summarize any text or written content found across images
        7. **Key Insights**: Notable observations or insights from the collective analysis
        8. **Detailed Breakdown**: Individual summary for each image with its key points
        
        Structure your report in a clear, organized manner that would be useful for 
        someone who hasn't seen the images but needs to understand their content.
        """,
        agent=results_summarizer,
        context=image_analysis_tasks,  # This ensures access to all previous task outputs
        expected_output="Comprehensive summary report of all analyzed images with insights and patterns"
    )
    
    # Combine all tasks
    all_tasks = image_analysis_tasks + [summary_task]
    
    # Create and return the crew
    crew = Crew(
        agents=[image_analyzer, results_summarizer],
        tasks=all_tasks,
        process=Process.sequential,  # Sequential ensures proper order of execution
        verbose=True
    )
    
    return crew

def run_multi_image_analysis(image_paths: List[str]) -> str:
    """
    Convenience function to run the multi-image analysis crew.
    
    Args:
        image_paths: List of paths to images to analyze
        
    Returns:
        Final summary report as string
    """
    if not image_paths:
        raise ValueError("At least one image path must be provided")
    
    # Validate image paths exist
    for path in image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image not found: {path}")
    
    # Create and run the crew
    crew = create_multi_image_analysis_crew(image_paths)
    result = crew.kickoff()
    
    return result.raw

def create_image_batch(id_num: str, img_list: List[str], use_patent_format: bool = False) -> Dict[str, Any]:
    """
    Helper function to create a properly formatted image batch dictionary.
    
    Args:
        id_num: Unique identifier for the batch
        img_list: List of image paths to analyze
        use_patent_format: If True, uses 'img_paths_str' key instead of 'img_list'
        
    Returns:
        Dictionary with 'id' and either 'img_list' or 'img_paths_str' keys
    """
    img_key = "img_paths_str" if use_patent_format else "img_list"
    return {
        "id": id_num,
        img_key: img_list
    }

def create_patent_batch(id_num: str, img_paths_str: List[str]) -> Dict[str, Any]:
    """
    Helper function specifically for patent data structure.
    
    Args:
        id_num: Unique identifier for the patent
        img_paths_str: List of image paths for this patent
        
    Returns:
        Dictionary with 'id' and 'img_paths_str' keys (patent format)
    """
    return {
        "id": id_num,
        "img_paths_str": img_paths_str
    }

def create_batches_from_directory(base_dir: str, batch_size: int = 5, use_patent_format: bool = False) -> List[Dict[str, Any]]:
    """
    Helper function to automatically create batches from images in a directory.
    
    Args:
        base_dir: Directory containing images
        batch_size: Maximum number of images per batch
        use_patent_format: If True, uses 'img_paths_str' key instead of 'img_list'
        
    Returns:
        List of batch dictionaries ready for processing
    """
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Directory not found: {base_dir}")
    
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    # Find all image files
    image_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(root, file))
    
    if not image_files:
        print(f"No images found in {base_dir}")
        return []
    
    # Create batches
    batches = []
    for i in range(0, len(image_files), batch_size):
        batch_images = image_files[i:i + batch_size]
        batch_id = f"auto_batch_{i//batch_size + 1:03d}"
        batches.append(create_image_batch(batch_id, batch_images, use_patent_format))
    
    print(f"Created {len(batches)} batches from {len(image_files)} images in {base_dir}")
    return batches

def run_multiple_image_batches(image_batches: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Run multi-image analysis for multiple batches of images in a loop.
    
    Args:
        image_batches: List of dictionaries, each containing:
                      - 'id': Unique identifier for the batch
                      - 'img_list' OR 'img_paths_str': List of image paths to analyze
    
    Returns:
        Dictionary mapping batch IDs to their analysis results
    """
    results = {}
    
    for batch_data in image_batches:
        batch_id = batch_data.get('id')
        
        # Support both formats: 'img_list' (original) and 'img_paths_str' (patent format)
        img_list = batch_data.get('img_list') or batch_data.get('img_paths_str', [])
        
        if not batch_id:
            print("Warning: Batch missing 'id' field, skipping...")
            continue
            
        if not img_list:
            print(f"Warning: Batch {batch_id} has empty image list, skipping...")
            continue
        
        print(f"\n{'='*50}")
        print(f"Processing Patent/Batch ID: {batch_id}")
        print(f"Images to analyze: {len(img_list)}")
        print(f"Image paths: {img_list}")
        print(f"{'='*50}")
        
        try:
            # Run analysis for this batch
            result = run_multi_image_analysis(img_list)
            results[batch_id] = result
            
            print(f"✅ Successfully completed analysis for {batch_id}")
            print(f"Result length: {len(result)} characters")
            
        except Exception as e:
            error_msg = f"❌ Error processing {batch_id}: {str(e)}"
            print(error_msg)
            results[batch_id] = error_msg
    
    return results

def save_batch_results(results: Dict[str, str], output_file: str = "batch_analysis_results.txt"):
    """
    Save the results from multiple batches to a file.
    
    Args:
        results: Dictionary mapping batch IDs to their analysis results
        output_file: Path to the output file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Multi-Image Analysis Results\n")
            f.write("=" * 50 + "\n\n")
            
            for batch_id, result in results.items():
                f.write(f"BATCH ID: {batch_id}\n")
                f.write("-" * 30 + "\n")
                f.write(result)
                f.write("\n\n" + "=" * 50 + "\n\n")
        
        print(f"📄 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def run_patent_analysis(patents_dict: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """
    Convenience function specifically for processing patent dictionaries.
    
    Args:
        patents_dict: Dictionary where each value contains:
                     - 'id': Patent identifier
                     - 'img_paths_str': List of image paths for this patent
    
    Returns:
        Dictionary mapping patent IDs to their analysis results
    """
    # Convert patent dictionary to batch list format
    patent_batches = []
    for patent_data in patents_dict.values():
        if 'id' in patent_data and 'img_paths_str' in patent_data:
            patent_batches.append(patent_data)
        else:
            print(f"Warning: Invalid patent data structure: {patent_data}")
    
    if not patent_batches:
        raise ValueError("No valid patent entries found in the dictionary")
    
    print(f"Processing {len(patent_batches)} patents...")
    return run_multiple_image_batches(patent_batches)

# Example usage
if __name__ == "__main__":
    # Example 1: Single batch (original functionality)
    print("Example 1: Single Batch Analysis")
    print("-" * 40)
    
    sample_images = [
        "/path/to/image1.jpg",
        "/path/to/image2.jpg", 
        "/path/to/image3.jpg"
    ]
    
    try:
        crew = create_multi_image_analysis_crew(sample_images)
        print("Crew created successfully!")
        print(f"Number of tasks: {len(crew.tasks)}")
        print(f"Number of agents: {len(crew.agents)}")
        
        # Uncomment to run (make sure image paths exist first)
        # result = run_multi_image_analysis(sample_images)
        # print("\nFinal Summary:")
        # print(result)
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("Example 2: Multiple Batch Analysis Loop")
    print("="*60)
    
    # Method 1: Manual batch creation (original format)
    image_batches = [
        create_image_batch("batch_001_products", [
            "/path/to/product1.jpg",
            "/path/to/product2.jpg",
            "/path/to/product3.jpg"
        ]),
        create_image_batch("batch_002_people", [
            "/path/to/person1.jpg",
            "/path/to/person2.jpg"
        ]),
        create_image_batch("batch_003_landscapes", [
            "/path/to/landscape1.jpg",
            "/path/to/landscape2.jpg",
            "/path/to/landscape3.jpg",
            "/path/to/landscape4.jpg"
        ])
    ]
    
    print(f"Method 1 - Manual batches: {len(image_batches)} batches configured:")
    for i, batch in enumerate(image_batches, 1):
        img_key = 'img_list' if 'img_list' in batch else 'img_paths_str'
        print(f"  {i}. ID: {batch['id']}, Images: {len(batch[img_key])}")
    
    # Method 2: Loop-based batch creation (original format)
    print(f"\nMethod 2 - Loop-based batch creation:")
    loop_batches = []
    
    # Example: Different categories of images
    image_categories = {
        "social_media_001": ["/path/to/social1.jpg", "/path/to/social2.jpg"],
        "documentation_002": ["/path/to/doc1.jpg", "/path/to/doc2.jpg", "/path/to/doc3.jpg"],
        "marketing_003": ["/path/to/ad1.jpg", "/path/to/ad2.jpg"]
    }
    
    for id_num, img_list in image_categories.items():
        batch = create_image_batch(id_num, img_list)
        loop_batches.append(batch)
        print(f"  Created batch: {id_num} with {len(img_list)} images")
    
    # Method 3: Patent-specific format
    print(f"\nMethod 3 - Patent-specific format (YOUR USE CASE):")
    patents_dict = {
        "patent_1": {
            "id": "US12345678",
            "img_paths_str": [
                "/path/to/patent_US12345678_fig1.jpg",
                "/path/to/patent_US12345678_fig2.jpg",
                "/path/to/patent_US12345678_fig3.jpg"
            ]
        },
        "patent_2": {
            "id": "US87654321", 
            "img_paths_str": [
                "/path/to/patent_US87654321_fig1.jpg",
                "/path/to/patent_US87654321_fig2.jpg"
            ]
        },
        "patent_3": {
            "id": "US11223344",
            "img_paths_str": [
                "/path/to/patent_US11223344_fig1.jpg",
                "/path/to/patent_US11223344_fig2.jpg",
                "/path/to/patent_US11223344_fig3.jpg",
                "/path/to/patent_US11223344_fig4.jpg"
            ]
        }
    }
    
    print(f"  Patent dictionary with {len(patents_dict)} patents:")
    for key, patent in patents_dict.items():
        print(f"    {key}: ID={patent['id']}, Images={len(patent['img_paths_str'])}")
    
    # Method 4: Auto-create from directory (example)
    print(f"\nMethod 4 - Auto-create from directory:")
    print("  # Example: auto_batches = create_batches_from_directory('/path/to/images', batch_size=3)")
    print("  # This would scan a directory and create batches automatically")
    
    print(f"\nTo run any of these analyses, uncomment the appropriate lines:")
    print("# For regular batches:")
    print("# results = run_multiple_image_batches(image_batches)  # or loop_batches")
    print("# For patent dictionary:")
    print("# results = run_patent_analysis(patents_dict)")
    print("# save_batch_results(results)")
    
    # Uncomment these lines to actually run the analysis:
    # Choose which format to run:
    
    # Option A: Regular batch format
    # results = run_multiple_image_batches(image_batches)  # Manual batches
    # results = run_multiple_image_batches(loop_batches)   # Loop-created batches
    
    # Option B: Patent-specific format (YOUR USE CASE)
    # results = run_patent_analysis(patents_dict)
    
    # Option C: Auto-created from directory
    # results = run_multiple_image_batches(create_batches_from_directory('/path/to/images'))
    # 
    # save_batch_results(results, f"patent_analysis_results_{len(results)}_items.txt")
    # print(f"\nAll {len(results)} items completed!")
    # 
    # # Print summary
    # print(f"\nSummary:")
    # successful = sum(1 for result in results.values() if not result.startswith("❌"))
    # failed = len(results) - successful
    # print(f"  ✅ Successful: {successful}")
    # print(f"  ❌ Failed: {failed}")
    # for item_id, result in results.items():
    #     status = "✅ Success" if not result.startswith("❌") else "❌ Failed"
    #     print(f"    {item_id}: {status}")
