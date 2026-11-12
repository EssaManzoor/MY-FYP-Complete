import os
import json
import faiss
import numpy as np
import pypdf
from django.conf import settings
from sentence_transformers import SentenceTransformer

# Initialize the shared sentence transformer model
# This will download the model on the first run if it isn't already cached locally.
model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_chunks_from_pdf(pdf_path, chunk_size=300, overlap=50):
    """
    Extracts text text from a PDF file page-by-page and segments it 
    into a sliding window list of text chunks with tracking metadata.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Target PDF file not found at: {pdf_path}")
        
    reader = pypdf.PdfReader(pdf_path)
    chunks_with_meta = []
    
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        # Tokenize roughly by splitting whitespace strings
        words = text.split()
        if not words:
            continue
            
        # Slide across the extracted tokens using chunk_size and overlap parameters
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words).strip()
            
            # Avoid logging meaningless or empty visual artifacts
            if len(chunk_text) > 25:
                chunks_with_meta.append({
                    'text': chunk_text,
                    'page_num': page_idx + 1
                })
                
            # Break out early if the end of the page vector space is reached
            if i + chunk_size >= len(words):
                break
                
    return chunks_with_meta


def generate_and_save_boilerplate_index(template_pdf_path, index_output_path='boilerplate.index'):
    """
    Parses a clean, unpopulated master university project template document, 
    converts its boilerplate blocks to normalized embeddings, and writes a 
    reusable reference index to disk.
    """
    print(f"[!] Processing Golden Template PDF: {template_pdf_path}")
    template_chunks = extract_chunks_from_pdf(template_pdf_path, chunk_size=250, overlap=40)
    
    if not template_chunks:
        raise ValueError("Extraction Error: No structural text could be extracted from the template.")
        
    texts = [chunk['text'] for chunk in template_chunks]
    print(f"[!] Vectorizing {len(texts)} boilerplate target fragments...")
    
    # Generate model embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # Normalize vectors to ensure Inner Product calculates absolute Cosine Similarity
    faiss.normalize_L2(embeddings)
    
    # Instantiating flat vector space index mapping standard 384 dimensions
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    # Create the destination directory if it doesn't exist
    output_dir = os.path.dirname(index_output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    # Write structural FAISS bin and backing text JSON trace to disk
    faiss.write_index(index, index_output_path)
    with open(index_output_path + '.json', 'w', encoding='utf-8') as f:
        json.dump(texts, f, indent=4)
        
    print(f"[✓] Success: Reference blueprint index written to: {index_output_path}")


def filter_boilerplate_chunks(student_chunks, boilerplate_index_path='boilerplate.index', similarity_threshold=0.75):
    """
    Performs vector scanning on candidate student text chunks against the reference index.
    Drops blocks matching institutional boilerplate structures above the similarity threshold.
    """
    if not os.path.exists(boilerplate_index_path):
        print(f"[!] Warning: Reference index '{boilerplate_index_path}' not found. Skipping filtration step.")
        return student_chunks

    student_texts = [chunk['text'] for chunk in student_chunks]
    if not student_texts:
        return []
        
    # Vectorize student submission segments
    student_embeddings = model.encode(student_texts, show_progress_bar=False)
    student_embeddings = np.array(student_embeddings).astype('float32')
    faiss.normalize_L2(student_embeddings)
    
    # Load compiled boilerplate matrix
    bp_index = faiss.read_index(boilerplate_index_path)
    
    # Search the boilerplate index for the single closest match (k=1)
    similarities, indices = bp_index.search(student_embeddings, k=1)
    
    clean_chunks = []
    skipped_count = 0
    
    for idx, chunk in enumerate(student_chunks):
        best_match_score = similarities[idx][0]
        
        # If the segment matches the template layout above the threshold, mask it out
        if best_match_score >= similarity_threshold:
            skipped_count += 1
            continue
            
        clean_chunks.append(chunk)
        
    print(f"[✓] Filter Matrix: Masked {skipped_count} boilerplate chunks. Retained {len(clean_chunks)} clean student chunks.")
    return clean_chunks