print("Program started...")

from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer('all-MiniLM-L6-v2')

print("Model loaded successfully!")

text = "Computer system crash during online examination"

embedding = model.encode(text)

print("Embedding generated!")
print("Vector length:", len(embedding))