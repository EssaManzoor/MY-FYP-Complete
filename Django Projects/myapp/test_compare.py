from ai.bulk_process import process_folder
from ai.compare_pdf import compare_document

folder = r"C:\Users\moosa\Documents\Djangos\Pdf Media\fyp"

process_folder(folder)

pdf = r"C:\Users\moosa\Documents\Djangos\Pdf Media\fyp\fyp_proposal_16.pdf"

results = compare_document(pdf)

print("\nSIMILAR DOCUMENTS FOUND:\n")

for result in results:

    print("----------------")
    print(result[:300])