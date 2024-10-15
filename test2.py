import fitz 
import json
import re

def extract_pages_after_keyword(pdf_path, keyword, num_pages):
    pdf_document = fitz.open(pdf_path)
    extracted_text = ""

    keyword_found = False

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        if keyword.lower() in text.lower():
            keyword_found = True
            
            for i in range(page_num, min(page_num + num_pages, pdf_document.page_count)):
                extracted_text += pdf_document.load_page(i).get_text("text") + "\n"
            break

    pdf_document.close()

    if keyword_found:
        return extracted_text.strip()
    else:
        print(f"Kalit so'z '{keyword}' yo'q :(")
        return None

def clean_title(title):
    """Sarlavhalarni tozalash uchun """
    cleaned_title = re.sub(r'\s*\.\.\.\s*|\s*\d+\s*$', '', title).strip()
    return cleaned_title

def process_extracted_text(text, output_file):
    lines = text.splitlines()
    result = {}
    current_section = 0  
    t = True

    for i, line in enumerate(lines):
        line = line.strip()
        
        if line:
            if t:
                if line == '283':
                    t = False
                    continue
            if re.match(r'^\d+$', line):  
                if line in {'214'}:  
                    continue
                
                current_section += 1
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:  
                        title = clean_title(next_line)  
                        result[current_section] = {
                            "title": title,
                            "sections": {}
                        }
                continue
            
            if current_section:
                first_word = line.split()[0]
                if '.' in first_word:  
                    section_num = first_word
                    title = clean_title(' '.join(line.split()[1:]).strip())  
                    if not title and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line[0].isalpha():  
                            title = clean_title(next_line)  

                    if section_num.count('.') == 1:  
                        result[current_section]["sections"][section_num] = {
                            "title": title,
                            "sections": {}
                        }
                    elif section_num.count('.') == 2:  
                        parent_section = section_num.rsplit('.', 1)[0]
                        if parent_section in result[current_section]["sections"]:
                            result[current_section]["sections"][parent_section]["sections"][section_num] = {
                                "title": title,
                                "sections": {}
                            }

    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    print(f"Natija '{output_file}' fayliga saqlandi.")
    return result

pdf_path = "Руководство_Бухгалтерия_для_Узбекистана_ред_3_0.pdf"  
keyword = "Оглавление"  
num_pages = 7  

# PDF dan matin olish uchun ---
extracted_text = extract_pages_after_keyword(pdf_path, keyword, num_pages)

# Natijani qayta ishlash va saqlash
if extracted_text:
    output_file = "result.json"  # Natijani saqlash fayli
    result_dict = process_extracted_text(extracted_text, output_file)
else:
    print("Matin bo'sh :(")

# Bu code faqat shu pdf uchun
# Code virual muhitda qilindi pipenv shell ishtish