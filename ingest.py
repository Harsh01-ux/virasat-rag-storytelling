import os
import json

def ingest_documents():
    # Define paths for the raw data folder and the output chunks file
    raw_dir = os.path.join("data", "raw")
    output_file = os.path.join("data", "chunks.json")
    
    # Check if the data/raw directory exists
    if not os.path.exists(raw_dir):
        print(f"Error: Raw directory '{raw_dir}' not found. Please create it and add your .txt files.")
        return
        
    all_chunks = []
    
    # Map raw filenames to readable heritage site names for better metadata
    site_name_mapping = {
        "amberfort": "Amber Fort",
        "hawamahal": "Hawa Mahal",
        "jaigarh": "Jaigarh",
        "ajanta": "Ajanta Caves",
        "khajurao": "Khajuraho",
        "redfort": "Red Fort",
        "tajmahal": "Taj Mahal"
    }
    
    # 1. Reads all txt files from data/raw
    # Iterate through all files in the data/raw folder
    for filename in os.listdir(raw_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(raw_dir, filename)
            print(f"Reading file: {filename}")
            
            # Determine the site key from the filename (e.g., 'AMBERFORT' from 'AMBERFORT.txt')
            site_key = os.path.splitext(filename)[0].lower()
            # Get a clean site name, or fall back to capitalizing the filename
            site_name = site_name_mapping.get(site_key, site_key.title())
            
            try:
                # Open and read the text file with UTF-8 encoding to support special characters
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue
                
            # 2. Breaks each file into small chunks (small paragraphs)
            # We split by double newlines (\n\n) which naturally separates paragraphs
            paragraphs = content.split("\n\n")
            
            chunk_count = 0
            for paragraph in paragraphs:
                paragraph_text = paragraph.strip()
                
                # Skip empty lines, very short snippets, or citation lists (less than 40 characters)
                if not paragraph_text or len(paragraph_text) < 40:
                    continue
                
                # Create a structured chunk containing the text and metadata (source file and site name)
                chunk = {
                    "id": f"{site_key}_{chunk_count}",
                    "text": paragraph_text,
                    "metadata": {
                        "source": filename,
                        "site": site_name
                    }
                }
                all_chunks.append(chunk)
                chunk_count += 1
                
            print(f"Successfully split {filename} into {chunk_count} chunks.")
            
    # 3. Saves them so they can be used later for search
    # Ensure the parent folder (data/) exists before writing the file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the chunks as a formatted JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=4, ensure_ascii=False)
        
    print(f"\nIngestion complete! Saved {len(all_chunks)} total chunks to '{output_file}'")

if __name__ == "__main__":
    ingest_documents()
