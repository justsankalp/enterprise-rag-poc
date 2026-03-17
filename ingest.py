import os
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize ChromaDB (creates a local folder named 'soil_db')
print("Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./soil_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = chroma_client.get_or_create_collection(
    name="save_soil_policies", 
    embedding_function=sentence_transformer_ef
)

# 2. Extract and Chunk the PDF
pdf_path = "CPL2024_SaveSoilPolicyBigBook-World-Web.pdf"
print(f"Reading and chunking {pdf_path}...")

reader = PdfReader(pdf_path)
documents = []
metadatas = []
ids = []

# Simple chunking strategy: split by page, then into smaller blocks if needed
# For this PoC, we will treat each page as a single chunk/document
# Assuming a 6-page offset for front-matter (Cover, TOC, etc.)
PAGE_OFFSET = 6 

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text and text.strip():
        clean_text = " ".join(text.split())
        
        pdf_index = i + 1
        printed_page = pdf_index - PAGE_OFFSET
        
        # If it's a negative number, it's the Table of Contents or Cover
        page_label = str(printed_page) if printed_page > 0 else f"Frontmatter (PDF Page {pdf_index})"

        documents.append(clean_text)
        metadatas.append({
            "source": "Save Soil Policy Big Book 2024", 
            "page": page_label, # Now it will store "133" instead of "139"
            "type": "Policy Document"
        })
        ids.append(f"doc_page_{pdf_index}")

# 3. Upsert into Vector Database
print(f"Upserting {len(documents)} chunks into ChromaDB. This might take a minute...")
collection.upsert(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("Ingestion Complete! The database is ready.")