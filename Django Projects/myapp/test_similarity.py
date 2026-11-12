from ai.embeddings import create_embedding
from ai.vector_store import add_embedding, search_embedding

doc1 = """
Computer system crashed during online examination.
"""

doc2 = """
AI-based crop disease detection using CNN.
"""

doc3 = """
Online exam platform failure caused student disconnection.
"""

embedding1 = create_embedding(doc1)
embedding2 = create_embedding(doc2)
embedding3 = create_embedding(doc3)

add_embedding(embedding1, doc1)
add_embedding(embedding2, doc2)
add_embedding(embedding3, doc3)

query = """
System failure during digital examination.
"""

query_embedding = create_embedding(query)

results = search_embedding(query_embedding)

print("\nMost Similar Documents:\n")

for r in results:
    print(r)
    print("------------------")