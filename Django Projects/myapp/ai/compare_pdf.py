import pypdf
from ai.chunker import split_text
from ai.embeddings import create_embedding
from ai.vector_store import search_embedding

def compare_uploaded_document(file_path):
    """
    Parses the newly uploaded document, compares it chunk-by-chunk 
    against our metadata database, and returns the highest overall score 
    along with an organized list of matching sources.
    """
    reader = pypdf.PdfReader(file_path)
    all_matches = []
    highest_score = 0
    
    # 1. Read through the uploaded file page-by-page
    for page in reader.pages:
        text = page.extract_text()
        if not text or not text.strip():
            continue
            
        chunks = split_text(text)
        for chunk in chunks:
            if len(chunk.strip()) < 15:
                continue
            
            # 2. Get vector match and query database
            query_emb = create_embedding(chunk)
            db_matches = search_embedding(query_emb, k=3)
            
            for match in db_matches:
                # Only log matches that cross a meaningful threshold (e.g., > 40%)
                if match["similarity"] > 40:
                    all_matches.append(match)
                    if match["similarity"] > highest_score:
                        highest_score = match["similarity"]

    # 3. Sort matches to show the highest similarity segments first
    all_matches = sorted(all_matches, key=lambda x: x["similarity"], reverse=True)
    
    # 4. Filter out duplicate sentences so the UI stays perfectly clean
    seen_texts = set()
    unique_matches = []
    for m in all_matches:
        if m["text"] not in seen_texts:
            seen_texts.add(m["text"])
            unique_matches.append(m)

    # Return the maximum document score, and the top 10 most relevant matches
    return highest_score, unique_matches[:10]