import os
import json
import chromadb
from chromadb.utils import embedding_functions

def store_embeddings():
    chunks_file = os.path.join("data", "chunks.json")
    db_path = os.path.join("data", "chroma_db")
    
    # 1. Verify that chunks.json exists
    if not os.path.exists(chunks_file):
        print(f"Error: Chunks file '{chunks_file}' not found. Please run ingest.py first.")
        return
        
    # Load the parsed paragraph chunks
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"Loaded {len(chunks)} chunks from '{chunks_file}'.")
    
    # 2. Setup the local persistent ChromaDB client
    # This will save the database files inside data/chroma_db/
    client = chromadb.PersistentClient(path=db_path)
    
    # 3. Setup the multilingual sentence-transformers embedding function
    # ChromaDB will use this model to automatically generate vector embeddings for our chunks
    print("Loading multilingual model: paraphrase-multilingual-mpnet-base-v2...")
    print("Note: This might take a moment if the model is being downloaded for the first time.")
    
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-mpnet-base-v2"
    )
    
    # 4. Get or create the 'heritage' collection
    # We pass the embedding function so ChromaDB knows how to embed the text
    collection = client.get_or_create_collection(
        name="heritage",
        embedding_function=embedding_fn
    )
    
    # Prepare the lists for ChromaDB ingestion
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        
    # 5. Store chunks in the database using .upsert()
    # Using upsert ensures that if a chunk with the same ID already exists,
    # it gets updated instead of creating a duplicate entry.
    print(f"Upserting {len(ids)} documents into ChromaDB...")
    
    # We batch the upload to prevent any large payload limits in ChromaDB
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_docs = documents[i:i + batch_size]
        batch_metadata = metadatas[i:i + batch_size]
        
        collection.upsert(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metadata
        )
        
    # 6. Verify total documents stored in the collection
    total_docs = collection.count()
    print(f"\nSuccess! Total documents in 'heritage' collection: {total_docs}")

if __name__ == "__main__":
    store_embeddings()
