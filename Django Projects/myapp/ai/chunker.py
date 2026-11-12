def split_text(text, chunk_size=200, overlap=30):
    """
    Splits text by word count (instead of characters) 
    and adds an overlap to preserve semantic context.
    """
    # Split the raw text into a list of individual words
    words = text.split()
    
    chunks = []
    i = 0
    
    while i < len(words):
        # Grab a slice of actual words
        chunk_words = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_words))
        
        # Move forward by the chunk_size minus the overlap
        i += (chunk_size - overlap)
        
    return chunks