import fitz  # PyMuPDF

def edit_pdf_fields(input_path, output_path, number, time, region):
    doc = fitz.open(input_path)

    text_to_replace = {
        "НОМЕР": number,
        "ВРЕМЯ": time,
        "РЕГИОН": region,
    }

    for page in doc:
        text_instances = []
        for key, value in text_to_replace.items():
            areas = page.search_for(key)
            for area in areas:
                page.add_redact_annot(area, fill=(1, 1, 1))
                text_instances.append((area, value))

        page.apply_redactions()
        for area, new_text in text_instances:
            page.insert_text(area.tl, new_text, fontsize=12, color=(0, 0, 0))

    doc.save(output_path)
