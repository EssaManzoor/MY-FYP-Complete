import os
import json
import faiss
import numpy as np
import pypdf
from ai.chunker import split_text
from ai.embeddings import create_embedding

INDEX_FILE = os.path.join(os.path.dirname(__file__), "storage", "index.faiss")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "storage", "metadata.json")

# Global in-memory cache + file timestamp tracking
_CACHED_INDEX = None
_CACHED_METADATA = None
_LAST_LOADED_TIMESTAMP = 0.0  # Tracks when we last read from disk


def _ensure_store_is_loaded():
    """
    Ensures the vector store is loaded in RAM and automatically forces a re-sync
    if another Django process modified the storage drive index files.
    """
    global _CACHED_INDEX, _CACHED_METADATA, _LAST_LOADED_TIMESTAMP

    # Check the actual modification time on the disk if the files exist
    disk_timestamp = 0.0
    if os.path.exists(INDEX_FILE):
        disk_timestamp = os.path.getmtime(INDEX_FILE)

    # Skip disk read ONLY if cache exists AND matches the latest disk file state
    if _CACHED_INDEX is not None and _CACHED_METADATA is not None:
        if _CACHED_INDEX.ntotal > 0 and disk_timestamp == _LAST_LOADED_TIMESTAMP:
            return  

    # Load or Reload from disk if out of sync
    if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
        _CACHED_INDEX = faiss.read_index(INDEX_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            _CACHED_METADATA = json.load(f)
        _LAST_LOADED_TIMESTAMP = disk_timestamp
    else:
        # Fallback initialization for completely empty project deployments
        if _CACHED_INDEX is None:
            _CACHED_INDEX = faiss.IndexFlatIP(384)
        if _CACHED_METADATA is None:
            _CACHED_METADATA = []


# --- 1. THE INDEXER (RUNS ON TEACHER ACCEPT) ---
def add_document_to_index(pdf_path, source_filename):
    """
    Parses an approved PDF, extracts vectors, normalizes them for Cosine Similarity,
    appends them to the index, and commits changes immediately to storage.
    """
    global _CACHED_INDEX, _CACHED_METADATA, _LAST_LOADED_TIMESTAMP
    
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    _ensure_store_is_loaded()

    reader = pypdf.PdfReader(pdf_path)
    new_vectors = []
    new_metadata = []

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text()
        if not text or not text.strip(): 
            continue
            
        chunks = split_text(text)
        for chunk in chunks:
            if len(chunk.strip()) < 15: 
                continue
            
            vector = create_embedding(chunk)
            new_vectors.append(vector)
            
            new_metadata.append({
                "source_file": source_filename,
                "page": page_num,
                "text": chunk
            })

    if not new_vectors:
        return

    # Convert to standard 32-bit floating point matrix array
    new_vectors_matrix = np.array(new_vectors).astype("float32")

    # 🛡️ Cosine Requirement: Normalize matrix to unit length
    faiss.normalize_L2(new_vectors_matrix)

    if _CACHED_INDEX.ntotal == 0 and isinstance(_CACHED_INDEX, faiss.IndexFlatIP):
        dimension = new_vectors_matrix.shape[1]
        _CACHED_INDEX = faiss.IndexFlatIP(dimension)

    # Append to RAM Cache
    _CACHED_INDEX.add(new_vectors_matrix)
    _CACHED_METADATA.extend(new_metadata)

    # Commit changes permanently down to drive storage
    faiss.write_index(_CACHED_INDEX, INDEX_FILE)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(_CACHED_METADATA, f, indent=4)
        
    # Update current process timestamp tracker immediately to prevent self-reloading
    _LAST_LOADED_TIMESTAMP = os.path.getmtime(INDEX_FILE)


# --- 2. THE SEARCHER (RUNS ON STUDENT UPLOAD) ---
def search_embedding(query_vector, k=2):
    """
    Queries the RAM-cached FAISS index instantly and scales similarity calculations cleanly.
    """
    _ensure_store_is_loaded()

    if _CACHED_INDEX is None or _CACHED_INDEX.ntotal == 0:
        return []  

    query_matrix = np.array([query_vector]).astype("float32")
    
    # 🛡️ Cosine Requirement: Normalize the input query vector matrix
    faiss.normalize_L2(query_matrix)
    
    similarities, indices = _CACHED_INDEX.search(query_matrix, k)

    results = []
    for score, idx in zip(similarities[0], indices[0]):
        if idx < 0 or idx >= len(_CACHED_METADATA): 
            continue  
            
        match_info = _CACHED_METADATA[idx].copy()
        
        # --- CLEAN METRIC CORRECTION SCALE ---
        raw_score = float(score)
        if raw_score <= 1.0:
            match_info["similarity"] = round(raw_score * 100, 1)
        else:
            match_info["similarity"] = round(raw_score, 1)
            
        results.append(match_info)

    return results