import os
import sys

# Ensures Python can locate your 'ai' package folders properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Notice we are importing the updated function here!
from ai.vector_store import add_document_to_index

def rebuild_faiss_database(pdf_folder_path):
    if not os.path.exists(pdf_folder_path):
        print(f"❌ Error: The folder '{pdf_folder_path}' does not exist.")
        return

    print(f"🚀 Starting bulk database ingestion from: {pdf_folder_path}")
    print("=" * 60)
    
    indexed_count = 0
    
    # Loop through all files in your repository folder
    for file_name in os.listdir(pdf_folder_path):
        if file_name.lower().endswith('.pdf'):
            file_path = os.path.join(pdf_folder_path, file_name)
            print(f"📄 Processing: {file_name}...", end="", flush=True)
            
            try:
                # This feeds the PDF directly into your optimized storage logic
                add_document_to_index(file_path, file_name)
                print(" ✅ Success!")
                indexed_count += 1
            except Exception as e:
                print(f" ❌ Failed! Error: {e}")

    print("=" * 60)
    print(f"🎉 All done! Rebuilt your FAISS store with {indexed_count} reference files.")

if __name__ == "__main__":
    # Pointing to your local directory path
    REPO_PATH = r"C:\Users\moosa\Documents\Djangos\Pdf Media\fyp"
    
    rebuild_faiss_database(REPO_PATH)