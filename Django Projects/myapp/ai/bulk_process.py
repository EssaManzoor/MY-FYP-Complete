import os
from ai.process_pdf import process_document

def process_folder(folder_path):
    # Safety check to make sure the folder actually exists
    if not os.path.exists(folder_path):
        print(f"Error: The directory '{folder_path}' was not found.")
        return

    pdf_files = [
        file for file in os.listdir(folder_path)
        if file.endswith(".pdf")
    ]

    print(f"Found PDFs: {len(pdf_files)}")

    for pdf in pdf_files:
        full_path = os.path.join(folder_path, pdf)
        print("\nProcessing:", pdf)
        process_document(full_path)

    print("\nALL PDFs INDEXED SUCCESSFULLY")


# This block executes immediately when you run this specific file
if __name__ == "__main__":
    # Your exact PDF Media directory path hardcoded
    my_media_folder = r"C:\Users\moosa\Documents\Djangos\Pdf Media\fyp"
    
    process_folder(my_media_folder)