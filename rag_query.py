import os
import sys
import json
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai

# Helper to load environmental variables without external dependency issues
def load_env():
    # Try using python-dotenv first
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Fallback to manual parsing if GEMINI_API_KEY is not set yet
    if not os.environ.get("GEMINI_API_KEY") and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

# Initialize ChromaDB and Embedding model globally to cache them across Streamlit runs
load_env()
db_path = os.path.join("data", "chroma_db")
client = None
collection = None

if os.path.exists(db_path):
    try:
        client = chromadb.PersistentClient(path=db_path)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-mpnet-base-v2"
        )
        collection = client.get_or_create_collection(
            name="heritage",
            embedding_function=embedding_fn
        )
    except Exception as e:
        print(f"Error initializing vector database globally: {e}")

def get_rag_response(question, target_language="English", expertise_level="beginner"):
    global collection
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment or .env file. Please check setup.", []
        
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    if collection is None:
        return "Error: Vector database not found. Please run ingest.py and embed_store.py first.", []

    
    # Retrieve top 5 relevant chunks
    results = collection.query(
        query_texts=[question],
        n_results=5
    )
    
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]
    
    if not documents:
        return "No relevant heritage documents found to answer your question.", []
        
    # Construct context string for Gemini
    context_str = ""
    source_mapping = {}
    
    for idx, (doc, meta) in enumerate(zip(documents, metadatas)):
        source_idx = idx + 1
        source_name = meta.get("source", "Unknown Source")
        site_name = meta.get("site", "Unknown Site")
        
        # Store for post-processing/citations mapping
        source_mapping[source_idx] = {
            "site": site_name,
            "filename": source_name,
            "snippet": doc[:150] + "..." if len(doc) > 150 else doc,
            "full_text": doc
        }
        
        context_str += f"--- Source [{source_idx}]: {site_name} (File: {source_name}) ---\n{doc}\n\n"
        
    # Adjust instructions depending on expertise level
    if expertise_level.lower() == "beginner":
        tone_instruction = "Use simple, easy-to-understand, engaging storytelling. Avoid complex terminology or explain it simply. Make it appealing to a tourist or student."
    else:
        tone_instruction = "Provide a deep, detailed, historically rich, and academic explanation. Include nuances, key historical dates, and architectual details if available in the context."

    # Build prompt
    prompt = f"""You are a knowledgeable and engaging heritage storytelling assistant.
Your task is to answer the user's question about heritage sites using ONLY the provided Context chunks.

CRITICAL INSTRUCTIONS:
1. Answer the question ONLY using the facts present in the Context. If the context does not contain enough information to answer, state clearly that you do not have enough information in the current curated database.
2. Do not use external knowledge or make up facts.
3. You MUST write the entire response in the requested Target Language: {target_language}.
4. Use the requested Tone and Depth: {tone_instruction}
5. You MUST include inline citation markers like [1], [2], etc., corresponding to the Source index at the exact end of sentences or clauses where you use their information. 

Context:
{context_str}

User Question: {question}

Response:"""

    try:
        # Use gemini-3.1-flash-lite model
        model = genai.GenerativeModel("gemini-3.1-flash-lite")
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        return f"Error generating response from Gemini API: {e}", []
        
    # Post-process citations to extract which sources were actually cited by Gemini
    cited_sources = []
    for source_idx, info in source_mapping.items():
        citation_marker = f"[{source_idx}]"
        if citation_marker in answer:
            cited_sources.append({
                "index": source_idx,
                "site": info["site"],
                "filename": info["filename"],
                "snippet": info["snippet"]
            })
            
    # If no citation markers were explicitly used but we want to show sources anyway as backup
    if not cited_sources and len(source_mapping) > 0:
        # We can add the top retrieved sources as potential sources
        for source_idx, info in list(source_mapping.items())[:2]:
            cited_sources.append({
                "index": source_idx,
                "site": info["site"],
                "filename": info["filename"],
                "snippet": info["snippet"]
            })
            
    return answer, cited_sources

if __name__ == "__main__":
    # Force standard output to UTF-8 to handle Unicode characters on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Allow running from command line for verification
    if len(sys.argv) < 2:
        print("Usage: python rag_query.py \"[Question]\" \"[Language]\" \"[beginner/expert]\"")
        print("Example: python rag_query.py \"Tell me about Amber Fort\" \"Hindi\" \"beginner\"")
        sys.exit(1)
        
    question = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "English"
    level = sys.argv[3] if len(sys.argv) > 3 else "beginner"
    
    print(f"\n--- Querying: '{question}' in {language} ({level} level) ---")
    answer, sources = get_rag_response(question, language, level)
    
    print("\n--- Answer ---")
    print(answer)
    
    print("\n--- Sources & Citations ---")
    for src in sources:
        print(f"[{src['index']}] {src['site']} (File: {src['filename']})")
        print(f"    Snippet: {src['snippet']}\n")
