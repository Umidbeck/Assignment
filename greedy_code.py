import fitz
import json
import re

#Glogal o'zgaruvchi
list_page = None
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
def extract_page_numbers_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    list_page = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")
        lines = text.splitlines()

        for n, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            first_word = line.split()[0]
            if '.' in first_word:  # Agar birinchi so'zda '.' bo'lsa, bu bo'lim nomi bo'lishi mumkin.
                if line.split()[-1].isdigit():
                    end_page = int(line.split()[-1])  # Oxirgi element sahifa raqami bo'lsa, end_page sifatida olinadi.
                else:
                    if n + 1 < len(lines):
                        next_line = lines[n + 1].strip()
                        try:
                            if len(next_line.split()) == 1 and next_line.split()[0].isdigit():
                                end_page = int(next_line.split()[0])  # Keyingi satrda faqat raqam bo'lsa
                            elif next_line.split()[-1].isdigit():
                                end_page = int(next_line.split()[-1])  # Keyingi satrning oxirgi elementi raqam bo'lsa
                            elif next_line.split()[-1].isalpha():
                                if n + 2 < len(lines):
                                    new_line = lines[n + 2].strip()
                                    if new_line.split()[-1].isdigit():
                                        end_page = int(new_line.split()[-1])
                                    else:
                                        end_page = None  
                                else:
                                    end_page = None  
                            else:
                                end_page = None  
                        except IndexError:
                            end_page = None
                    else:
                        end_page = None  

                if end_page is not None:
                    list_page.append(end_page)
            else:
                continue
    return list_page

    pdf_document.close()
    return list_page

def clean_title(title):
    """Sarlavhalarni tozalash uchun, raqam va ... ni olib tashlaydi."""
    cleaned_title = re.sub(r'\s*\.\.\.\s*|\s*\d+\s*$', '', title).strip()
    return cleaned_title

def extract_text_for_section(pdf_path, title, section_num, flag = False):
    """Berilgan sahifalar orasidagi section uchun matn va uzunlikni olish."""
    global list_page
    
    start_page = 14  
    end_page = None  
    found_title = False

    if list_page is None:
        list_page = extract_page_numbers_from_pdf(pdf_path)
        end_page = list_page[0]
        list_page[-1] = 358
        list_page[-2] = int('357')
        # Birinchi chaqiruvda end_page ni birinchi sahifa raqami bilan belgilaymiz
    else:
        if start_page != 14:
            end_page = list_page[0]
        else:
            start_page = list_page.pop(0)
            if list_page:
                end_page = list_page[0]
                list_page.append(357)
            else:
                end_page = start_page

    pdf_document = fitz.open(pdf_path)
    text = ""
    if flag:
        text, length = "", 0
        return text, length
    # Sahifalar orasidagi matnni olish
    found_title = False
    flag_true = True
    text = ""  
    title_all = f"{section_num} {title}".rstrip('.')  # Sarlavhani izlash uchun to'liq nom
    title_index = 0
    end_index_1 = -1

    for page_num in range(start_page - 1, end_page + 1):
        page = pdf_document.load_page(page_num)
        page_text = page.get_text("text") + "\n"  
        section_num = str(section_num)
        if not found_title:
            # Agar sarlavha topilmagan bo'lsa, uni qidiramiz
            if title_all in page_text:
                found_title = True
                title_index = page_text.index(title_all) + len(title_all)
                
            elif section_num in page_text:
                found_title = True
                title_index = page_text.index(section_num)
                
            text += page_text[title_index:].strip() + "\n"           
        else:
            # Agar sarlavha allaqachon topilgan bo'lsa, sahifadagi qolgan matnni qo'shamiz
            text += page_text[title_index:].strip() + "\n"
    if flag_true:
                
                section_num_cleaned = str(section_num.rstrip('.'))
                page = pdf_document.load_page(end_page - 1)
                page_text = page.get_text("text") + "\n"  
                lines = page_text.splitlines() 
                for end_page_index in lines:
                    match = re.match(r'^(\d+(\.\d+)*)', end_page_index)

                    if match:
                        section_first_digit = int(section_num_cleaned.split('.')[0])  # 2.1.1 dan 2 ni olish
                        first_number = match.group(1)
                        first_first_digit = int(first_number.split('.')[0])
                        
                        if first_first_digit - section_first_digit in [1, 0]:  
                            end_index = page_text.index(first_number)
                            if title_index < end_index:
                                end_index_1 = end_index
                                break
                    else:
                        pass   
        
    text += page_text[title_index:end_index_1].strip() + "\n"
  
    


    pdf_document.close()

    if not text:  # Matn bo'sh bo'lsa
        return "", 0
    else:
        return text.strip(), len(text)

def process_extracted_text(text, output_file, pdf_path):
    lines = text.splitlines()
    result = {}
    current_section = 0  
    t = True
    flag_1 = True
    title_nums = 0
    dic_2_num = {'2.1', '2.1.', '2.2.', '2.3.', '2.4.', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '7.1', '9.1', '9.1', '9.3', '9.7', '9.8', '10.1', '11.2', '11.3', '12.1', '13.4', '13.5', '13.6'}

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
                        title = clean_title(next_line)  # Title ni tozalang
                        title_num = line  # Title raqamini saqlang
                        result[current_section] = {
                            "title": title,
                            "text": "",  # Matn
                            "length": 0,  # Uzunlik
                            "sections": {}
                        }

                        # Sahifalarni aniqlash
                        start_page = int(line)  # Title raqami
                        end_page = 0  # Keyingi title raqami uchun

                        # Keyingi bo'limning sahifasini qidiring
                        for j in range(i + 1, len(lines)):  
                            next_line = lines[j].strip()  
                            
                            if re.match(r'^\d+.*\.\.\.\s*\d+$', next_line):  
                                # Satr oxiridagi raqamni olish
                                last_number_match = re.search(r'\d+$', next_line)
                                
                                if last_number_match:  
                                    end_page = int(last_number_match.group())  
                                    break  # Tsiklni to'xtatamiz
                                                
                        if end_page == 0:  # Agar keyingi sahifa topilmasa, oxirigacha olish
                            end_page = start_page  
                        # Matn va uzunlikni olish
                        if current_section != 1:
                            result[current_section]
                            result[current_section]
                        else:
                            title_nums += 1
                            text, length = extract_text_for_section(pdf_path, title, title_nums)
                            result[current_section]["text"] = text
                            result[current_section]["length"] = length
                continue
            
            if current_section:
                first_word = line.split()[0]
                end_page = line.split()[-1]
                # Oxirgi element raqamligini tekshiramiz
                if '.' in first_word:  
                    # Oxirgi element raqamligini tekshiramiz
                    if line.split()[-1].isdigit():
                        end_page = int(line.split()[-1])  
                    else:
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()  # Keyingi satrni olamiz
                            try:

                                if len(next_line.split()) == 1 and next_line.split()[0].isdigit():  # Agar keyingi satrda faqat bitta element bo'lsa va u raqam bo'lsa
                                    end_page = int(next_line.split()[0])  # O'sha bitta raqamni olamiz
                                elif next_line.split()[-1].isdigit():  # Yoki keyingi satrning oxirgi elementi raqammi?
                                    end_page = int(next_line.split()[-1])  # Agar raqam bo'lsa, end_page sifatida qabul qilinadi
                                elif next_line.split()[-1].isalpha():
                                    new_line = lines[i+2]
                                    end_page = int(new_line.split()[-1])
                                else:
                                    end_page = None  # Ehtiyot chorasi sifatida
                            except IndexError:
                                end_page = int('214')
                        else:
                            end_page = None  # Ehtiyot chorasi sifatida

                    section_num = first_word
                    title = clean_title(' '.join(line.split()[1:]).strip())  
                    if not title and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line[0].isalpha():  
                            title = clean_title(next_line)  

                    if section_num.count('.') == 1 or first_word.startswith('2'):  
                        if first_word:
                            section_num = first_word
                        result[current_section]["sections"][section_num] = {
                            "title": title,
                            "text": "",  # Matn
                            "length": 0,  # Uzunlik
                            "sections": {}
                        }
                        # Nested section uchun matn va uzunlik olish
                        if section_num in dic_2_num:
                            text, length = extract_text_for_section(pdf_path, title, section_num)
                            result[current_section]["sections"][section_num]["text"] = text
                            result[current_section]["sections"][section_num]["length"] = length
                        else:
                            text, length = extract_text_for_section(pdf_path, title, section_num, flag = True)
                            result[current_section]["sections"][section_num]
                            result[current_section]["sections"][section_num]
                    elif section_num.count('.') == 2:
                        parent_section = section_num.rsplit('.', 1)[0]
                        if parent_section in result[current_section]["sections"]:
                            result[current_section]["sections"][parent_section]["sections"][section_num] = {
                                "title": title,
                                "text": "",  # Matn
                                "length": 0,  # Uzunlik
                                "sections": {}
                            }
                            # Nested section uchun matn va uzunlik olish
                            text, length = extract_text_for_section(pdf_path, title, section_num)
                            result[current_section]["sections"][parent_section]["sections"][section_num]["text"] = text
                            result[current_section]["sections"][parent_section]["sections"][section_num]["length"] = length

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
    output_file = "result_1.json"  # Natijani saqlash fayli
    result_dict = process_extracted_text(extracted_text, output_file, pdf_path)
else:
    print("Matin bo'sh :(")

