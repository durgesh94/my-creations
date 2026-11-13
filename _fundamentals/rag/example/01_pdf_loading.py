
import pymupdf

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"

# Step 1: Open PDF
doc = pymupdf.open(PDF_PATH)

# Step 2: Basic document information
print("Total Pages:", len(doc))

# Step 3: Read PDF file metadata
metadata = doc.metadata

print("\n--- PDF Metadata ---")

for key, value in metadata.items():
    print(f"{key}: {value}")

# Step 4: Read page information
print("\n--- Page Information ---")

for page_number, page in enumerate(doc):

    print(f"\n--- Page {page_number + 1} ---")

    blocks = page.get_text("blocks")

    for block in blocks:
        block_text = block[4]
        block_type = block[6]

        if block_type == 0:
            print("Text Block:")
            print(block_text)

# Step 5: Close PDF
doc.close()
