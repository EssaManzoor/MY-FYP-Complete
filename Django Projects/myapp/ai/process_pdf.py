import os
import pypdf
from ai.chunker import split_text
from ai.embeddings import create_embedding
from ai.vector_store import add_embedding

def process_document(file_path):
    
    source_file = os.path.basename(file_path)
    
    print(f"Extracting text from {source_file}...")
    
    reader = pypdf.PdfReader(file_path)
    
   
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text()
        
        if not text or not text.strip():
            continue
            
        
        chunks = split_text(text) 
        
        for chunk in chunks:
            if len(chunk.strip()) > 15:  
                embedding = create_embedding(chunk)
                
                add_embedding(embedding, chunk, source_file, page_num)
                
    print(f"Successfully indexed {source_file}!")